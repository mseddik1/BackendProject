from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status, security
from sqlalchemy.orm.session import Session

from src.app.models import dbmodels
from src.app.core.config import settings
from src.app.schemas import schemas
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
# from jose import JWTError, jwt
from fastapi import Cookie


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
    to_encode.update({"type":"access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire= datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)

    to_encode.update({"exp":expire})
    to_encode.update({"type":"refresh"})
    encoded_refresh_token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_refresh_token


def verify_token(token:str)-> schemas.TokenData:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Could not verify credentials!", headers={"WWW-Authenticate":"Bearer"})
        return schemas.TokenData(email=email )

    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Could not verify credentials!", headers={"WWW-Authenticate":"Bearer"})


def refresh_token(
    db: Session,
        #thats python and fastapi magic, the "refresh_token" parameter is exactly what fastapi will be looking for it
        #Meaning, I am telling fastapi now, look for a parameter that is a string stored in cookies.
        #So python will take the parameter name "refresh_token" and look for it in the cookies.
        #I already sent this specific cookie in the response when logging in. Check services.login_for_access_token
    refresh_token: str

):
    if refresh_token is None:
        raise HTTPException(status_code=401, detail="Missing refresh token")

    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")

    user_email = payload.get("sub")
    user = db.query(dbmodels.User).filter(dbmodels.User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=401, detail="User no longer exists")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRES)
    new_access_token = create_refresh_token(data ={"sub":user.email}, expires_delta=access_token_expires)

    return {"access_token": new_access_token, "token_type": "bearer"}
