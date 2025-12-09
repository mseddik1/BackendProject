from datetime import timedelta

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from src.app.enums import enums
from src.app.schemas import schemas
from src.app.core import security
from src.app.db.base import get_db
from src.app.models import dbmodels
from src.app.core.config import settings



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
    if db.query(dbmodels.User).filter(dbmodels.User.email==user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User exists!", headers={"WWW-Authenticate":"Bearer"})
    hashed_pwd = security.hash_pwd(user.password)
    db_user = dbmodels.User(
        name = user.name,
        email = user.email,
        role= user.role,
        hashed_pwd = hashed_pwd
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def login_for_access_token(form_data: OAuth2PasswordRequestForm, db: Session):
    user = db.query(dbmodels.User).filter(dbmodels.User.email==form_data.username).first()

    if not user or not security.verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Unauthorized!", headers={"WWW-Authenticate":"Bearer"})

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User inactive!", headers={"WWW-Authenticate":"Bearer"})

    access_token_expires = timedelta(minutes=settings.TOKEN_EXPIRES)
    access_token= security.create_access_token(data ={"sub":user.email}, expires_delta=access_token_expires)
    return {"access_token":access_token, "token_type":"bearer"}







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

def update_user(user_id: int, user: schemas.UserCreate, current_user:dbmodels.User , db: Session ):
    user_db = db.query(dbmodels.User).filter(dbmodels.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail = "user not found!")

    update_data = user.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            if field == "password":
                hashed_pwd = security.hash_pwd(user.password)
                setattr(user_db, "password", hashed_pwd)
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

def get_all_users(db: Session):
    return db.query(dbmodels.User).all()


def require_admin(current_user:dbmodels.User = Depends(get_current_active_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="You are not an admin!")
    return current_user

def get_all_products(db: Session, page: int, per_page: int,_: dbmodels.User):
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
