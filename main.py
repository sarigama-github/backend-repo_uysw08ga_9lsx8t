import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Product, Order

app = FastAPI(title="Veltrax API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"name": "Veltrax API", "message": "Welcome to Veltrax backend"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# Seed products if empty for demo
@app.post("/seed")
def seed_products():
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    count = db["product"].count_documents({})
    if count > 0:
        return {"seeded": False, "message": "Products already exist"}
    sample_products = [
        {
            "title": "Veltrax Pro Headphones",
            "description": "Audiophile-grade wireless headphones with adaptive ANC.",
            "price": 299.0,
            "category": "Audio",
            "image": "https://images.unsplash.com/photo-1518445317430-1369bde26f59?q=80&w=800&auto=format&fit=crop",
            "in_stock": True,
            "rating": 4.9,
        },
        {
            "title": "Veltrax Nova Keyboard",
            "description": "Low-profile mechanical keyboard with per-key RGB.",
            "price": 189.0,
            "category": "Peripherals",
            "image": "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=800&auto=format&fit=crop",
            "in_stock": True,
            "rating": 4.7,
        },
        {
            "title": "Veltrax Quantum Mouse",
            "description": "Precision wireless mouse with 8K polling.",
            "price": 129.0,
            "category": "Peripherals",
            "image": "https://images.unsplash.com/photo-1545235617-9465d2a55698?q=80&w=800&auto=format&fit=crop",
            "in_stock": True,
            "rating": 4.8,
        },
        {
            "title": "Veltrax Vision Monitor 32\"",
            "description": "32-inch 4K mini-LED display with 120Hz and HDR1000.",
            "price": 1299.0,
            "category": "Displays",
            "image": "https://images.unsplash.com/photo-1517331156700-3c241d2b4d83?q=80&w=1200&auto=format&fit=crop",
            "in_stock": True,
            "rating": 4.6,
        },
    ]
    for p in sample_products:
        create_document("product", p)
    return {"seeded": True, "count": len(sample_products)}

@app.get("/products", response_model=List[Product])
def list_products(category: Optional[str] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filter_query = {"category": category} if category else {}
    products = get_documents("product", filter_query)
    # Normalize _id to string
    for p in products:
        p["id"] = str(p.get("_id"))
        p.pop("_id", None)
    return products

class CartItem(BaseModel):
    product_id: str
    quantity: int

class CheckoutRequest(BaseModel):
    items: List[CartItem]
    name: str
    email: str
    address: Optional[str] = None

@app.post("/checkout")
def checkout(payload: CheckoutRequest):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    # Fetch products, compute totals
    items_detail = []
    subtotal = 0.0
    for item in payload.items:
        try:
            prod = db["product"].find_one({"_id": ObjectId(item.product_id)})
        except Exception:
            prod = None
        if not prod:
            raise HTTPException(status_code=400, detail=f"Invalid product: {item.product_id}")
        line_total = float(prod.get("price", 0)) * item.quantity
        subtotal += line_total
        items_detail.append({
            "product_id": str(prod["_id"]),
            "title": prod.get("title"),
            "price": float(prod.get("price", 0)),
            "quantity": item.quantity,
            "image": prod.get("image")
        })
    tax = round(subtotal * 0.08, 2)
    total = round(subtotal + tax, 2)
    order_doc = Order(
        items=items_detail,  # type: ignore
        customer={"name": payload.name, "email": payload.email, "address": payload.address},  # type: ignore
        subtotal=round(subtotal, 2),
        tax=tax,
        total=total,
    )
    order_id = create_document("order", order_doc)
    return {"order_id": order_id, "subtotal": order_doc.subtotal, "tax": tax, "total": total}
