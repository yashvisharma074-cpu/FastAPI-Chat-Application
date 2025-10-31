from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from model.auth_model import User
from core.security import hash_password, verify_password, create_access_token
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from fastapi.responses import JSONResponse

router = APIRouter()

@router.post("/register")
def register(user: dict, db: Session = Depends(get_db)):
    username = user["username"]
    password = user["password"]
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    hashed = hash_password(password)
    new_user = User(username=username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    return {"msg": "User registered successfully"}


@router.post("/login")
def login(user: dict, db: Session = Depends(get_db)):
    username = user["username"]
    password = user["password"]

    db_user = db.query(User).filter(User.username == username).first()
    if not db_user or not verify_password(password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    access_token = create_access_token({"sub": db_user.username}, timedelta(minutes=60))

    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,  
        samesite="Lax"
    )
    return response

@router.get("/users")
def get_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username} for u in users]