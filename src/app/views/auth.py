from typing import Optional

from fastapi.security import OAuth2PasswordRequestForm

from src.app.models import dbmodels
from src.app.db.base import get_db
from src.app.schemas import schemas
from sqlalchemy.orm import Session
from fastapi import Depends
from src.app.services import services
from src.app.core import security
from src.app.utils import emailUtil
from fastapi import APIRouter, Request, Query, Response
from fastapi import Cookie




auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# Auth Endpoints
@auth_router.post("/register", response_model=schemas.RegisterResponse)
def register_user(user:schemas.UserCreate, db: Session = Depends(get_db)):
    return services.register_user(user,db)


@auth_router.get("/confirm-email")
def confirm_email(token:str =Query(None),  db: Session = Depends(get_db)):
    return security.confirm_email(token,db)

@auth_router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data:OAuth2PasswordRequestForm =Depends(), db: Session = Depends(get_db)):
   return services.login_for_access_token(form_data, db)


@auth_router.get("/me", response_model=schemas.UserResponse)
def read_me(current_user: dbmodels.User = Depends(services.get_current_active_user)):
    return current_user



@auth_router.post("/refresh")
def refresh_token(
    request: Request,
    db: Session = Depends(get_db)):

    refresh_token = request.cookies.get("refresh_token")

    return security.refresh_token(refresh_token=refresh_token, db=db)



@auth_router.post("/forgot-password")
def forgot_password(payload: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    return security.forgot_password(payload=payload, db=db)



@auth_router.post("/reset-password")
def reset_password(payload: schemas.ResetPasswordRequest, db: Session = Depends(get_db), token:str = Query(None)):
    return security.reset_password(payload=payload, db=db, token=token)



@auth_router.post("/logout")
def logout(response: Response):
    return services.logout(response)



# @auth_router.get("/send-email")
# def send_email( to_email: str, subject: str, html_body: str):
#     return emailUtil.send_email(to_email=to_email, subject=subject, html_body=html_body)