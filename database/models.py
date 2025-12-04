from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from database.connection import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Integer, default=1)  # 0=inactive, 1=active
    is_premium = Column(Integer, default=0) # 0=free, 1=premium
    created_at = Column(DateTime, default=datetime.utcnow)
    
    ideas = relationship("Idea", back_populates="user")

class Idea(Base):
    __tablename__ = "ideas"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    user_description = Column(Text, nullable=False)
    extracted_concepts = Column(Text)  # JSON string: core_function, search_keywords, etc.
    negative_keywords = Column(Text)   # JSON string: list of excluded terms
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)

    # Monitoring Fields
    monitoring_enabled = Column(Boolean, default=False)
    monitoring_ends_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="ideas")
    competitors = relationship("Competitor", back_populates="idea")
    scan_history = relationship("ScanHistory", back_populates="idea")

class ScanHistory(Base):
    """
    Lightweight table to track what we've seen to prevent re-scanning/re-alerting.
    Stores hashes of URLs/IDs to save space (Render 140MB limit).
    """
    __tablename__ = "scan_history"

    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"))
    url_hash = Column(String(32), index=True) # MD5 hash of the product URL
    is_relevant = Column(Boolean, default=False) # Cache the LLM decision
    last_seen = Column(DateTime, default=datetime.utcnow)

    idea = relationship("Idea", back_populates="scan_history")

class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(Integer, primary_key=True)
    idea_id = Column(Integer, ForeignKey("ideas.id"))
    product_name = Column(String(500))
    source = Column(String(100))  # aliexpress, kickstarter, google
    url = Column(Text)
    price = Column(Float, nullable=True)
    similarity_score = Column(Float)  # 0-100
    reasoning = Column(Text)  # Why LLM thinks it's similar
    
    # User Feedback / Data Collection
    is_relevant = Column(Integer, nullable=True) # 1=Yes, 0=No, Null=Unreviewed
    feedback_at = Column(DateTime, nullable=True)
    
    discovered_at = Column(DateTime, default=datetime.utcnow)

    idea = relationship("Idea", back_populates="competitors")
