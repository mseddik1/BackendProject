from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel


class UserCreate(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    role :  Optional[str] = None
    password : Optional[str] = None
    is_active : bool
    is_admin: bool

class UserResponse(BaseModel):
    id: int
    name : str
    email : str
    role :  str
    is_active : bool
    is_admin : bool

    class Config:
        from_attributes=True

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
     email: Optional[str] = None


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    in_stock: Optional[bool] = True
    is_active: Optional[bool] = True
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    in_stock: Optional[bool] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class Product(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    in_stock: bool
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    updated_by: str
    category: Optional[str]
    image_url: Optional[str]

    class Config:
        orm_mode = True



class ProductListResponse(BaseModel):
    page: int
    per_page: int
    total: int
    items: List[Product]
