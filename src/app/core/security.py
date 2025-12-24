from datetime import datetime, timedelta
from typing import Optional
import jwt
from fastapi import HTTPException, status, security
from jwt import PyJWTError
from sqlalchemy.orm.session import Session

from src.app.models import dbmodels
from src.app.core.config import settings
from src.app.schemas import schemas
from src.app.utils import emailUtil
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from fastapi.responses import HTMLResponse

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





def create_password_reset_token(email: str) -> str:

    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {
        "sub": email,
        "type": "password_reset",
        "exp": expire
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    return encoded_jwt


def decode_password_reset_token(token: str) -> dict:

    payload = jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )
    # optional extra check, but we'll check again later in the endpoint
    if payload.get("type") != "password_reset":
        raise PyJWTError("Invalid token type")
    return payload

def create_confirm_email_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode = {
        "sub": email,
        "type": "email_confirmation",
        "exp": expire
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_email_confirmation_token(token: str) -> dict:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    return payload

def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session):
    user = db.query(dbmodels.User).filter(dbmodels.User.email == payload.email).first()

    # Don't reveal whether the email exists -> generic response
    if not user:
        return {"detail": "If this email exists, a reset link has been sent."}

    token = create_password_reset_token(user.email)


    # For now, just build a link (assuming frontend at http://localhost:3000)
    reset_link = f"http://127.0.0.1:8000/auth/reset-password?token={token}"
    html_body = f"""
    <div style="font-family: Arial, sans-serif; font-size: 15px; color: #333;">
        <p>Hi {user.name},</p>

        <p>You recently requested to reset your password.</p>
        <p>Click the button below to set a new password:</p>

        <p>
            <a href="{reset_link}"
               style="
                   background-color: #1a73e8;
                   color: white;
                   padding: 10px 18px;
                   text-decoration: none;
                   border-radius: 4px;
                   font-weight: bold;
               ">
                Reset Password
            </a>
        </p>

        <p>If the button doesn't work, you can also use this link:</p>
        <p><a href="{reset_link}">{reset_link}</a></p>


        <br>
        <p>If you did not request this password reset, you can safely ignore this email.</p>

        <br>
        <p>Best regards,<br>Your App Team</p>
    </div>
    """

    emailUtil.enqueue_email(user.email,"Reset Password", html_body, db)
    # For demo purposes, you can either:
    # - log it
    print(f"[DEV] Password reset link for {user.email}: {reset_link}")

    # - and/or return it in response while you're developing:
    return {
        "detail": "If this email exists, a reset link has been sent.",
        "reset_link": reset_link,  # remove in production
    }


def reset_password(payload: schemas.ResetPasswordRequest, db: Session, token: str):
    # 1) Decode and validate token
    try:
        data = decode_password_reset_token(token)
    except PyJWTError:
        # covers invalid signature, expired, wrong type, etc.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token"
        )

    if data.get("type") != "password_reset":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type",
        )

    email = data.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload",
        )

    # 2) Find user
    user = db.query(dbmodels.User).filter(dbmodels.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    # 3) Update password
    hashed_password = hash_pwd(payload.new_password)
    setattr(user, "hashed_pwd", hashed_password)
    # db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "detail": "Password has been reset successfully",
        "user":user.email
    }


def send_confirmation_email(user: schemas.UserCreate, db: Session):

    token= create_confirm_email_token(user.email)

    confirm_email_link = f"https://seymour-intersocial-vicenta.ngrok-free.dev/auth/confirm-email?token={token}"
    #http://127.0.0.1:8000
    html_body = f"""
    <div style="font-family: Arial, sans-serif; font-size: 15px; color: #333;">
        <p>Hi {user.name} - {user.role},</p>

        <p>Please confirm your email by clicking the button below:</p>

        <p>
            <a href="{confirm_email_link}" 
               style="background-color: #4CAF50; color: white; padding: 10px 18px; 
                      text-decoration: none; border-radius: 4px; font-weight: bold;">
                Confirm Email
            </a>
        </p>

        # <p>If the button doesn’t work, here is the link:</p>
        # <p><a href="{confirm_email_link}">{confirm_email_link}</a></p>

        <br>
        <p>Best regards,<br>Your App Team</p>
    </div>
    """

    emailUtil.enqueue_email(user.email,"Confirm your email", html_body,db)

    return {
        "detail": "A confirmation link has been sent. Check your email to confirm.",
        "confirm_email_link": confirm_email_link
    }

def confirm_email(token: str,db: Session):
    try:
        data = decode_email_confirmation_token(token)
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token")

    if data.get("type") != "email_confirmation":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token type"
        )

    email = data.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid token payload",
        )


    user = db.query(dbmodels.User).filter(dbmodels.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found"
        )

    user.is_active = True
    db.commit()
    db.refresh(user)

    html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Email Confirmed</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background-color: #f4f6f8;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .card {
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 420px;
                }
                h1 {
                    color: #2e7d32;
                }
                p {
                    color: #555;
                    font-size: 16px;
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>✅ Email Confirmed</h1>
                <p>Your email has been successfully verified.</p>
                <p>You can now safely close this page.</p>
            </div>
        </body>
        </html>
        """

    # return {
    #     "detail": "Email confirmed successfully!"
    # }

    return HTMLResponse(content=html_content)
