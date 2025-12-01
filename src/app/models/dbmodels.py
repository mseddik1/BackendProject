from sqlalchemy import Column, Integer, String, Boolean
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


Base.metadata.create_all(engine)