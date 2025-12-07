from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime, timedelta
from database.connection import get_db, SessionLocal
from database.models import User, Idea
from api.services.scanner import run_scan_for_idea

router = APIRouter()

from typing import Optional

class IdeaSubmission(BaseModel):
    email: str
    description: str
    monitor_months: int = 0 # Options: 0 (off), 1, 3
    image_base64: Optional[str] = None # New: Optional visual input

def background_scan_wrapper(idea_id: int, image_base64: str = None):
    """
    Wrapper to ensure the background task has its own DB session.
    """
    db = SessionLocal()
    try:
        run_scan_for_idea(idea_id, db, image_base64=image_base64)
    finally:
        db.close()

@router.post("/submit")
def submit_idea(submission: IdeaSubmission, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == submission.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found. Please signup first.")

    # Rate Limiting: 3 requests per 20 minutes
    twenty_minutes_ago = datetime.utcnow() - timedelta(minutes=20)
    recent_ideas = db.query(Idea).filter(
        Idea.user_id == user.id,
        Idea.created_at >= twenty_minutes_ago
    ).count()

    if recent_ideas >= 3:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. You can submit 3 ideas per 20 minutes. Please try again later."
        )

    # Calculate monitoring period
    monitoring_enabled = False
    monitoring_ends_at = None

    if submission.monitor_months > 0:
        # Simple validation logic (could be expanded to check Premium status later)
        monitoring_enabled = True
        monitoring_ends_at = datetime.utcnow() + timedelta(days=30 * submission.monitor_months)

    new_idea = Idea(
        user_id=user.id,
        user_description=submission.description,
        monitoring_enabled=monitoring_enabled,
        monitoring_ends_at=monitoring_ends_at
    )
    db.add(new_idea)
    db.commit()
    db.refresh(new_idea)

    # Trigger background scan - Pass image if provided
    background_tasks.add_task(background_scan_wrapper, new_idea.id, submission.image_base64)

    return {
        "message": "Idea received. Scanning started.", 
        "idea_id": new_idea.id,
        "monitoring": "Active" if monitoring_enabled else "Inactive"
    }

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
