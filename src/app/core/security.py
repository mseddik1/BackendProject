from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status
from src.app.core.config import settings
from src.app.schemas import schemas
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=['argon2'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


#Security Functions
def verify_pwd(plain_pwd:str, hashed_pwd: str)-> bool:
    return pwd_context.verify(plain_pwd, hashed_pwd)

def hash_pwd(plain_pwd:str)->str:
    return pwd_context.hash(plain_pwd)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire= datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt


def verify_token(token:str)-> schemas.TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Could not verify credentials!", headers={"WWW-Authenticate":"Bearer"})
        return schemas.TokenData(email=email )

    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Could not verify credentials!", headers={"WWW-Authenticate":"Bearer"})


