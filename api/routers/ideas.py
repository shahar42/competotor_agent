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

@router.get("/results/{email}")
def get_user_results(email: str, db: Session = Depends(get_db)):
    """Get all ideas and competitors for a user by email"""
    from database.models import Competitor

    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ideas = db.query(Idea).filter(Idea.user_id == user.id).all()

    results = []
    for idea in ideas:
        competitors = db.query(Competitor).filter(Competitor.idea_id == idea.id).order_by(Competitor.similarity_score.desc()).all()
        results.append({
            "idea_id": idea.id,
            "description": idea.user_description,
            "competitors": [
                {
                    "name": c.product_name,
                    "url": c.url,
                    "source": c.source,
                    "price": c.price,
                    "similarity_score": c.similarity_score,
                    "reasoning": c.reasoning
                }
                for c in competitors
            ]
        })

    return results
