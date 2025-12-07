from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from database.connection import get_db
from database.models import Competitor, User
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

@router.get("/unsubscribe")
def unsubscribe(email: str, db: Session = Depends(get_db)):
    """
    Unsubscribe user from all emails.
    Simple GET endpoint so it can be clicked from an email.
    """
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return HTMLResponse("""
        <html>
            <head><title>Unsubscribe</title></head>
            <body style="font-family: sans-serif; text-align: center; padding: 50px;">
                <h2>Email not found</h2>
                <p>This email address is not in our system.</p>
            </body>
        </html>
        """)

    user.is_active = 0
    db.commit()

    return HTMLResponse("""
    <html>
        <head><title>Unsubscribed</title></head>
        <body style="font-family: sans-serif; text-align: center; padding: 50px;">
            <h2>✓ Successfully Unsubscribed</h2>
            <p>You will no longer receive emails from Idea Validator.</p>
            <p style="color: #666; font-size: 0.9em; margin-top: 30px;">
                To reactivate your account in the future, simply submit a new idea scan.
            </p>
        </body>
    </html>
    """)
