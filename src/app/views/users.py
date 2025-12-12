from src.app.db.base import get_db
from src.app.models import dbmodels
from src.app.schemas import schemas
from sqlalchemy.orm import Session
from fastapi import Depends
from src.app.services import services
from fastapi import HTTPException
from typing import List
from fastapi import APIRouter





users_router = APIRouter(prefix="/users", tags=["Users"])





@users_router.get("/profile", response_model=schemas.UserResponse)
def get_profile(current_user:dbmodels.User = Depends(services.get_current_active_user)):
    return services.get_profile(current_user)

@users_router.get("/verify-token")
def verify_token_endpoint(current_user:dbmodels.User = Depends(services.get_current_active_user)):
    return services.verify_token_endpoint(current_user)




@users_router.get("/{user_id}", response_model= schemas.UserResponse)
def get_user(user_id: int, current_user:dbmodels.User = Depends(services.get_current_active_user), db: Session = Depends(get_db) ):
    return services.get_user(user_id, db)

@users_router.post("/create", response_model= schemas.UserResponse)
def create_user(user: schemas.UserCreate, current_user:dbmodels.User = Depends(services.require_admin), db: Session = Depends(get_db)):
   return services.create_user(user, current_user, db)




@users_router.put("/{user_id}",response_model=schemas.UserResponse)
def update_user(user_id: int, user: schemas.UserCreate, current_user:dbmodels.User = Depends(services.require_admin) , db: Session = Depends(get_db)):
   return services.update_user(user_id, user, current_user,db)


@users_router.delete("/{user_id}" )
def detele_user(user_id:int, current_user:dbmodels.User = Depends(services.require_admin), db: Session = Depends(get_db)):
   return services.detele_user(user_id, current_user, db)


@users_router.get("/", response_model=List[schemas.UserResponse])
def get_all_users(current_user:dbmodels.User = Depends(services.get_current_active_user),db: Session = Depends(get_db)):
    return services.get_all_users(db)



