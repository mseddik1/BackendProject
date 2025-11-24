from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer,  OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import create_engine,  Column, Integer, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session 
from typing import Optional, List
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta

from sqlalchemy.util import deprecated
# separating_main
# Security Config
SECRET_KEY = "backEndProject"
ALGORITHM ="HS256"
TOKEN_EXPIRES = 30
pwd_context = CryptContext(schemes=['argon2'], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")







#Database setup
engine = create_engine("sqlite:///users.db", connect_args={"check_same_thread":False})
SessionLocal = sessionmaker(autocommit=False  ,autoflush=False, bind=engine)
Base = declarative_base()

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


class UserCreate(BaseModel):
    name : Optional[str] = None
    email : Optional[str] = None
    role :  Optional[str] = None
    password : Optional[str] = None
    is_active : bool

class UserResponse(BaseModel):
    id: int
    name : str
    email : str
    role :  str
    is_active : bool

    class Config:
        from_attributes=True


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
     email: Optional[str] = None



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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_token(token:str)-> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Could not verify credentials!", headers={"WWW-Authenticate":"Bearer"})
        return TokenData(email=email )

    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Could not verify credentials!", headers={"WWW-Authenticate":"Bearer"})





def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



# Auth Dependencies

def get_current_user(token: str=Depends(oauth2_scheme), db: Session =Depends(get_db)):
    token_data =  verify_token(token)
    user = db.query(User).filter(User.email==token_data.email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "User does not exist!", headers={"WWW-Authenticate":"Bearer"})
    return user



def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail= "Inactive user!", headers={"WWW-Authenticate":"Bearer"})

    return current_user




app = FastAPI(title="Integration with SQL!")

# Auth Endpoints

@app.post("/register", response_model=UserResponse)
def register_user(user:UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email==user.email).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User exists!", headers={"WWW-Authenticate":"Bearer"})
    hashed_pwd = hash_pwd(user.password)
    db_user = User(
        name = user.name,
        email = user.email,
        role= user.role,
        hashed_pwd = hashed_pwd
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/login", response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm =Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email==form_data.username).first()

    if not user or not verify_pwd(form_data.password, user.hashed_pwd):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail= "Unauthorized!", headers={"WWW-Authenticate":"Bearer"})

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail= "User inactive!", headers={"WWW-Authenticate":"Bearer"})

    access_token_expires = timedelta(minutes=TOKEN_EXPIRES)
    access_token= create_access_token(data ={"sub":user.email}, expires_delta=access_token_expires)
    return {"access_token":access_token, "token_type":"bearer"}









@app.get("/")
def root() :
    return {"message":"Using SQL with FastAPI!  "}


@app.get("/profile", response_model=UserResponse)
def get_profile(current_user:User = Depends(get_current_active_user)):
    return current_user

@app.get("/verify-token")
def verify_token_endpoint(current_user:User = Depends(get_current_active_user)):
    return {
        "valid": True,
        "user": {
            "id": current_user.id,
            "name": current_user.name,
            "email": current_user.email,
            "role": current_user.role
        }
    }



@app.get("/users/{user_id}", response_model= UserResponse)
def get_user(user_id: int, current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db) ):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail = "user not found!")
    return user

@app.post("/users", response_model= UserResponse)
def create_user(user: UserCreate, current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    if db.query(User).filter(User.email==user.email).first():
        raise  HTTPException(status_code=400, detail= "user already exists! ")

    hashed_pwd = hash_pwd(user.password)
    db_user = User(
        name=user.name,
        email=user.email,
        role=user.role,
        hashed_pwd=hashed_pwd
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user




@app.put("/user/{user_id}",response_model=UserResponse)
def update_user(user_id: int, user: UserCreate, current_user:User = Depends(get_current_active_user) , db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code= 404, detail = "user not found!")

    for field, value in user.dict().items():
        if value is not None:
            if field == "password":
                hashed_pwd = hash_pwd(user.password)
                setattr(user_db, "password", hashed_pwd)
            else:
                setattr(user_db, field, value)

    db.commit()
    db.refresh(user_db)
    return user_db



@app.delete("/user/{user_id}" )
def detele_user(user_id:int, current_user:User = Depends(get_current_active_user), db: Session = Depends(get_db)):
    user_db = db.query(User).filter(User.id == user_id).first()
    if not user_db:
        raise HTTPException(status_code= 404, detail = "user not found!")
    if user_db.id == current_user.id:
        raise HTTPException(status_code=404, detail="You can not delete yourself!")

    db.delete(user_db)
    db.commit()
    # db.refresh(user_db)

    return {"message":"User deleted!"}


@app.get("/users", response_model=List[UserResponse])
def get_all_users(current_user:User = Depends(get_current_active_user),db: Session = Depends(get_db)):
    return db.query(User).all()




