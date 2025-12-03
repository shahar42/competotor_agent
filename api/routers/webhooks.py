from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Competitor
from datetime import datetime

router = APIRouter()

@router.get("/feedback")
def record_feedback(competitor_id: int, is_relevant: int, db: Session = Depends(get_db)):
    """
    Simple GET endpoint so it can be clicked from an email.
    is_relevant: 1 = Yes, 0 = No
    """
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        return {"error": "Competitor not found"}
    
    competitor.is_relevant = is_relevant
    competitor.feedback_at = datetime.utcnow()
    db.commit()
    
    return {"message": "Feedback recorded. Thank you!", "relevant": is_relevant == 1}
