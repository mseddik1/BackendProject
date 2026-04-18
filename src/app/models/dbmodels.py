import datetime

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, func, JSON, ForeignKey
from src.app.db.base import Base, engine


#Database model
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    email = Column(String(100),nullable=True, unique=True)
    role = Column(String(100), nullable=False)
    hashed_pwd = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, nullable=True )
    is_admin = Column(Boolean, default=False, nullable=True )
    failed_attempts = Column(Integer, default=0, nullable=False )
    confirmation_key = Column(Integer, default=False, nullable=True)
    confirmation_expires_at = Column(DateTime, nullable=True)
    failed_otp_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)


class Products(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(100), nullable=False)
    price = Column(Float(100), nullable=False)
    stock_quantity = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, default=False )
    # created_at = Column(DateTime, server_default=func.now())  # set on insert
    # updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())  # auto-update
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now())
    updated_by = Column(String(100), nullable=False)
    category = Column(String(100), nullable=True)
    image_url = Column(String(100), nullable=True)



class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)  # positive or negative
    movement_type = Column(String(50), nullable=False)  # sale, restock, return
    created_at = Column(DateTime, default=datetime.datetime.now())
    created_by = Column(String(100), nullable=False)
    note = Column(String(255), nullable=True)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(50), nullable=False)  # e.g. "send_email"
    payload = Column(JSON, nullable=False)     # any data needed for the job
    status = Column(String(20), default="pending")  # "pending", "processing", "done", "failed"
    created_at = Column(DateTime, default=datetime.datetime.now())
    updated_at = Column(DateTime, default=datetime.datetime.now())
    attempts = Column(Integer, default=0, nullable=False )
    max_attempts = Column(Integer, default=3, nullable=False )


class Tracking(Base):
    __tablename__ = "tracking"
    id = Column(Integer, primary_key=True, index=True)
    ip = Column(String(100), nullable=False)
    user_agent = Column(String(100), nullable=False)
    path = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)


Base.metadata.create_all(engine)