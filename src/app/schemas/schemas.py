from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name : Optional[str]
    email : EmailStr
    role :  Optional[str]
    password : Optional[str]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: EmailStr = None
    role: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = False
    is_admin: Optional[bool] = False
class UserResponse(BaseModel):
    id: int
    name : str
    email : str
    role :  str
    is_active : bool
    is_admin : bool

    class Config:
        from_attributes=True


class RegisterResponse(BaseModel):
    user: UserResponse
    confirm: dict
    details: Optional[str]=None

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
    stock_quantity: int
    category: Optional[str] = None
    image_url: Optional[str] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    image_url: Optional[str] = None


class Product(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float
    stock_quantity: int
    is_active: bool
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    updated_by: str
    category: Optional[str]
    image_url: Optional[str]

    class Config:
        # orm_mode = True
        from_attributes = True




class ProductListResponse(BaseModel):
    page: int
    per_page: int
    total: int
    items: List[Product]



class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str
