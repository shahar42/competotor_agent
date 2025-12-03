from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from database.connection import get_db
from database.models import User

router = APIRouter()

class UserSignup(BaseModel):
    email: EmailStr

@router.post("/signup")
def signup(user_data: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        return {"message": "User already exists", "user_id": existing_user.id}
    
    new_user = User(email=user_data.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # TODO: Send welcome email
    
    return {"message": "User created", "user_id": new_user.id}
