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
    Returns minimal response - no popup/page to bother user
    """
    competitor = db.query(Competitor).filter(Competitor.id == competitor_id).first()
    if not competitor:
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse("✓", status_code=200)

    competitor.is_relevant = is_relevant
    competitor.feedback_at = datetime.utcnow()
    db.commit()

    # Return minimal response - just a checkmark, no JSON popup
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse("✓", status_code=200)
