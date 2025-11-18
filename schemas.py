"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- Order -> "order" collection
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List

class Product(BaseModel):
    """
    Products collection schema
    Collection name: "product"
    """
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    image: Optional[str] = Field(None, description="Image URL")
    in_stock: bool = Field(True, description="Whether product is in stock")
    rating: Optional[float] = Field(4.8, ge=0, le=5, description="Average rating")

class OrderItem(BaseModel):
    product_id: str = Field(..., description="Reference to product _id as string")
    title: str = Field(..., description="Product title at time of purchase")
    price: float = Field(..., ge=0, description="Unit price at time of purchase")
    quantity: int = Field(..., ge=1, description="Quantity ordered")
    image: Optional[str] = None

class Customer(BaseModel):
    name: str
    email: EmailStr
    address: Optional[str] = None

class Order(BaseModel):
    """
    Orders collection schema
    Collection name: "order"
    """
    items: List[OrderItem]
    customer: Customer
    subtotal: float = Field(..., ge=0)
    tax: float = Field(0, ge=0)
    total: float = Field(..., ge=0)
    status: str = Field("pending", description="Order status")
