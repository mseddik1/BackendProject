from datetime import datetime
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, EmailStr, constr


class UserCreate(BaseModel):
    name : constr(min_length=1, max_length=100) #I added this to test if i create a user with more than 100 chars. It gave an error :D
    email : EmailStr
    role :  Optional[str]
    password : Optional[str]


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
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
    is_active: Optional[bool] = False
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


class TrackPayload(BaseModel):
    event: str

    token_present: Optional[bool] = None
    correlation_id: Optional[str] = None
    client_id: Optional[str] = None

    user_agent: Optional[str] = None
    user_agent_hints: Optional[Dict[str, Any]] = None
    languages: Optional[List[str]] = None
    language: Optional[str] = None
    platform: Optional[str] = None

    max_touch_points: Optional[int] = None
    hardware_concurrency: Optional[int] = None
    device_memory_gb: Optional[float] = None

    time: Optional[Dict[str, Any]] = None
    page: Optional[Dict[str, Any]] = None
    display: Optional[Dict[str, Any]] = None
    preferences: Optional[Dict[str, Any]] = None
    permissions: Optional[Dict[str, Any]] = None
    storage: Optional[Dict[str, Any]] = None
    capabilities: Optional[Dict[str, Any]] = None
    network: Optional[Dict[str, Any]] = None
    battery: Optional[Dict[str, Any]] = None
    media: Optional[Dict[str, Any]] = None
    webgl: Optional[Dict[str, Any]] = None
    derived: Optional[Dict[str, Any]] = None
