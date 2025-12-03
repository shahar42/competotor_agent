from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database.connection import get_db, SessionLocal
from database.models import User, Idea
from api.services.scanner import run_scan_for_idea

router = APIRouter()

class IdeaSubmission(BaseModel):
    email: str
    description: str

def background_scan_wrapper(idea_id: int):
    """
    Wrapper to ensure the background task has its own DB session.
    """
    db = SessionLocal()
    try:
        run_scan_for_idea(idea_id, db)
    finally:
        db.close()

@router.post("/submit")
def submit_idea(submission: IdeaSubmission, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == submission.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please signup first.")
    
    new_idea = Idea(
        user_id=user.id,
        user_description=submission.description
    )
    db.add(new_idea)
    db.commit()
    db.refresh(new_idea)
    
    # Trigger background scan
    background_tasks.add_task(background_scan_wrapper, new_idea.id)
    
    return {"message": "Idea received. Scanning started.", "idea_id": new_idea.id}
