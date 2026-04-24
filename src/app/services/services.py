import base64
import binascii
import json
from datetime import timedelta, datetime
from typing import Optional

from fastapi import Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, select
from fastapi import HTTPException, status, Response

from src.app.core.security import send_confirmation_email
from src.app.enums import enums
from src.app.schemas import schemas
from src.app.core import security
from src.app.db.base import get_db
from src.app.models import dbmodels
from src.app.core.config import settings
from fastapi.responses import JSONResponse



# Auth Dependencies
def get_current_user(token: str=Depends(security.oauth2_scheme), db: Session =Depends(get_db)):
    token_data =  security.verify_token(token)
    user = db.query(dbmodels.User).filter(dbmodels.User.email==token_data.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "User does not exist!", headers={"WWW-Authenticate":"Bearer"})
    return user

def get_current_active_user(current_user: dbmodels.User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Inactive user!", headers={"WWW-Authenticate":"Bearer"})

    return current_user





# Auth Endpoints
def register_user(user:schemas.UserCreate, db: Session ):
    db_user =db.query(dbmodels.User).filter(dbmodels.User.email==user.email).first()
    if db_user and db_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User exists!", headers={"WWW-Authenticate":"Bearer"})
    if db_user and not db_user.is_active:
        confirm = security.send_confirmation_email(db_user, db)
        return {
        "user" :db_user,
        "confirm" : confirm,
        "details": "User already registered, please confirm your email!"
        }

    confirm = security.send_confirmation_email(user, db)

    hashed_pwd = security.hash_pwd(user.password)
    db_user = dbmodels.User(
        name = user.name,
        email = user.email,
        role= user.role,
        hashed_pwd = hashed_pwd,
        # is_active = True #I am doing this here because it is logic that registering a user will make him active, unless there is "verify your email" to activate it.
    )


    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {
        "user" :db_user,
        "confirm" : confirm
    }

login_counter = 0

def login_for_access_token(form_data: OAuth2PasswordRequestForm, db: Session):
    user = db.query(dbmodels.User).filter(dbmodels.User.email==form_data.username).first()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Unauthorized!", headers={"WWW-Authenticate":"Bearer"})

    if user.failed_attempts >= 3 :
        user.is_active = False
        db.commit()
        db.refresh(user)
        send_confirmation_email(user, db)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Too many failed attempts. Please verify your email." )

    if not security.verify_pwd(form_data.password, user.hashed_pwd):
        user.failed_attempts += 1
        db.commit()
        db.refresh(user)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Unauthorized!", headers={"WWW-Authenticate":"Bearer"})


    if not user.is_active:
        send_confirmation_email(user, db)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User inactive, please check your email to activate it!", headers={"WWW-Authenticate":"Bearer"})

    access_token_expires = timedelta(minutes=settings.access_token_expires)
    refresh_token_expires = timedelta(days=settings.refresh_token_expires)
    access_token= security.create_access_token(data ={"sub":user.email}, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(data ={"sub":user.email}, expires_delta=refresh_token_expires)

    user.failed_attempts = 0
    db.commit()
    db.refresh(user)

    response = JSONResponse(
        content={
            "access_token": access_token,
            "token_type": "bearer",
        }
    )
    # HTTP-only refresh cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # True in production with HTTPS
        samesite="lax",
        max_age=60 * 60 * 24 * settings.refresh_token_expires
    )
    return response


def logout(response: Response):
    # Remove the refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=False,     # keep same attributes as set_cookie
        samesite="lax"
    )

    return {"detail": "Logged out successfully"}









def root() :
    return {"message":"Using SQL with FastAPI! "}

def get_profile(current_user:dbmodels.User ):
    return current_user

def verify_token_endpoint(current_user:dbmodels.User ):
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role

        }
    }

def get_user(user_id: int, db: Session):
    user = db.query(dbmodels.User).filter(dbmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail = "user not found!")
    return user

def create_user(user: schemas.UserCreate, current_user:dbmodels.User, db: Session):
    if db.query(dbmodels.User).filter(dbmodels.User.email==user.email).first():
        raise  HTTPException(status_code=400, detail= "user already exists! ")

    hashed_pwd = security.hash_pwd(user.password)
    db_user = dbmodels.User(
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_pwd=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def update_user(user_id: int, user: schemas.UserUpdate, current_user:dbmodels.User , db: Session ):
    user_db = db.query(dbmodels.User).filter(dbmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail = "user not found!")

    update_data = user.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            if field == "password":
                hashed_pwd = security.hash_pwd(user.password)
                setattr(user_db, "hashed_pwd", hashed_pwd)
            else:
                setattr(user_db, field, value)

    db.commit()
    db.refresh(user_db)
    return user_db

def delete_user(user_id:int, current_user:dbmodels.User , db: Session ):
    user_db = db.query(dbmodels.User).filter(dbmodels.User.id == user_id).first()
    if not user_db:
        raise HTTPException(status_code= 404, detail = "user not found!")
    if user_db.id == current_user.id:
        raise HTTPException(status_code=404, detail="You can not delete yourself!")

    db.delete(user_db)
    db.commit()
    # db.refresh(user_db)

    return {"message":"User deleted!"}


def search_user_email(email:str, db: Session):
    user_db = db.query(dbmodels.User).filter(dbmodels.User.email == email).first()
    if not user_db:
        raise HTTPException(status_code=404, detail = "user not found!")

    return user_db


def get_all_users(page:int, per_page:int, db: Session):
    skip = (page - 1) * per_page
    limit = per_page
    total = db.query(dbmodels.User).count()
    users = db.query(dbmodels.User).offset(skip).limit(limit).all()
    return total, users


def require_admin(current_user:dbmodels.User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You are not an admin!")
    return current_user

def get_all_products(db: Session, page: int, per_page: int):
    skip = (page - 1) * per_page
    limit = per_page
    total = db.query(dbmodels.Products).count()
    items = db.query(dbmodels.Products).offset(skip).limit(limit).all()
    return total, items

def create_product(product: schemas.ProductCreate, db: Session, current_user: dbmodels.User):
    if db.query(dbmodels.Products).filter(dbmodels.Products.name==product.name).first():
        raise HTTPException(status_code=400, detail="Product already exists! ")
    db_product = dbmodels.Products(
        name=product.name,
        description=product.description,
        price=product.price,
        in_stock=product.in_stock,
        updated_by = current_user.email,
        category=product.category,
        image_url=product.image_url
    )

    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

def get_product_by_id(product_id: int, db: Session):
    product = db.query(dbmodels.Products).filter(dbmodels.Products.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail = "product not found!")
    return product

def get_product_by_name(name:str, db: Session):
    product = db.query(dbmodels.Products).filter(dbmodels.Products.name==name).first()
    if not product:
        raise HTTPException(status_code=404, detail = "product not found!")
    return product

def update_product(product_id: int, product: schemas.ProductUpdate, db: Session, current_user: dbmodels.User ):
    product_db = db.query(dbmodels.Products).filter(dbmodels.Products.id == product_id).first()
    if not product_db:
        raise HTTPException(status_code=404, detail = "product not found!")

    update_data = product.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(product_db, field, value)
    product_db.updated_by = current_user.email
    product_db.updated_at = datetime.now()


    db.commit()
    db.refresh(product_db)
    return product_db

def delete_product(product_id: int, db: Session):
    product_db = db.query(dbmodels.Products).filter(dbmodels.Products.id == product_id).first()
    if not product_db:
        raise HTTPException(status_code=404, detail = "product not found!")
    db.delete(product_db)
    db.commit()
    return {"message":"Product deleted!"}


def publish_product(product_id: int, db: Session):
    product_db = db.query(dbmodels.Products).filter(dbmodels.Products.id == product_id).first()
    if not product_db:
        raise HTTPException(status_code=404, detail = "product not found!")

    product_schema = schemas.Product.from_orm(product_db)
    payload = jsonable_encoder(product_schema, exclude_unset=True)

    job = dbmodels.Job(
        type = enums.JobType.PUBLISH_PRODUCT.value,
        payload = payload
    )

    db.add(job)
    db.commit()
    db.refresh(job)
    return {
        "msg" : "Publishing Queued!",
        "payload" : job.payload
        }


def purchase_product(product_id: int, db: Session):
    pass

def get_current_stock(product_id: int, db: Session):
    pass

def restock_product(product_id: int, db: Session):
    pass


def get_products_cursor(
    limit: int,
    cursor: Optional[str],
    db: Session

):

    """
    This SAME function handles:
    - First request (cursor is None)
    - Next request (cursor is provided)
    """

    # -----------------------
    # CASE 1: FIRST REQUEST
    # -----------------------
    total = db.query(dbmodels.Products).count()

    if cursor is None:
        count = db.query(dbmodels.Products).order_by(dbmodels.Products.created_at.desc(),dbmodels.Products.id.desc()).count()


        limit = min(limit, count)
        products = db.execute(select(dbmodels.Products.id, dbmodels.Products.name, dbmodels.Products.description, dbmodels.Products.price, dbmodels.Products.stock_quantity, dbmodels.Products.created_at)
                              .order_by(dbmodels.Products.created_at.desc(),dbmodels.Products.id.desc()).limit(limit)).mappings().all()

        query = """
        SELECT id, name, description, price, in_stock, stock_quantity
        FROM products
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
        """
        params = {"limit": limit}

    else:
        last_created_at, last_id = decode_cursor(cursor)

        count = db.query(dbmodels.Products).filter(
            or_(dbmodels.Products.created_at < last_created_at,
               and_(
                    dbmodels.Products.created_at == last_created_at,
                    dbmodels.Products.id < last_id
                ))).order_by(
            dbmodels.Products.created_at.desc(),
        dbmodels.Products.id.desc()
        ).count()

        limit = min(limit, count)
        products = db.execute(select(dbmodels.Products.id, dbmodels.Products.name, dbmodels.Products.description, dbmodels.Products.price, dbmodels.Products.stock_quantity, dbmodels.Products.created_at)
                              .where(
            or_(dbmodels.Products.created_at < last_created_at,
               and_(
                    dbmodels.Products.created_at == last_created_at,
                    dbmodels.Products.id < last_id
                ))
        ).order_by(
            dbmodels.Products.created_at.desc(),
        dbmodels.Products.id.desc()
        ).limit(limit)).mappings().all()



        query = """
        SELECT id, name, description, price, in_stock, stock_quantity
        FROM products
        WHERE
            (created_at < :created_at)
            OR (created_at = :created_at AND id < :id)
        ORDER BY created_at DESC, id DESC
        LIMIT :limit
        """
        params = {
            "created_at": last_created_at,
            "id": last_id,
            "limit": limit
        }





    if products:
        last_row = products[-1]

        next_cursor = encode_cursor(
            last_row["created_at"],
            last_row["id"]
        )
        return {
            "data": products,
            "next_cursor": next_cursor
        }
    else:
        return {"message": "That's it for now :) you are up to date!"}






def encode_cursor(created_at: datetime, post_id: int) -> str:
    payload = {
        "created_at": created_at.isoformat(),
        "id": post_id
    }
    json_str = json.dumps(payload)
    return base64.urlsafe_b64encode(json_str.encode()).decode()

def decode_cursor(cursor: str) -> tuple[datetime, int]:
    try:
        decoded = base64.urlsafe_b64decode(cursor.encode()).decode()
    except binascii.Error:
        raise HTTPException(status_code=400, detail=f"Bad cursor {cursor}")

    payload = json.loads(decoded)
    return datetime.fromisoformat(payload["created_at"]), payload["id"]

