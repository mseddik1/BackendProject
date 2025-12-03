import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, func
from src.app.db.base import Base, engine


#Database model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(100),nullable=True, unique=True)
    role = Column(String(100), nullable=False)
    hashed_pwd = Column(String, nullable=False)
    is_active = Column(Boolean, default=True )
    is_admin = Column(Boolean, default=False, nullable=True )



class Products(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(100), nullable=False)
    price = Column(Float(100), nullable=False)
    in_stock = Column(Integer, default=True )
    is_active = Column(Boolean, default=True )
    # created_at = Column(DateTime, server_default=func.now())  # set on insert
    # updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # auto-update
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    updated_by = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    image_url = Column(String(100), nullable=True)




Base.metadata.create_all(engine)