from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    role :  Optional[str] = None
    password : Optional[str] = None
    is_active : bool

class UserResponse(BaseModel):
    id: int
    name : str
    email : str
    role :  str
    is_active : bool

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

