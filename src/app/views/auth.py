from fastapi.security import OAuth2PasswordRequestForm

from src.app.db.base import get_db
from src.app.schemas import schemas
from sqlalchemy.orm import Session
from fastapi import Depends
from src.app.services import services
from src.app.core import security
from fastapi import APIRouter



auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


# Auth Endpoints
@auth_router.post("/register", response_model=schemas.UserResponse)
def register_user(user:schemas.UserCreate, db: Session = Depends(get_db)):
    return services.register_user(user)


@auth_router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data:OAuth2PasswordRequestForm =Depends(), db: Session = Depends(get_db)):
   return services.login_for_access_token(form_data, db)






