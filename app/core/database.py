"""
Database models and initialization
"""
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.core.config import settings

Base = declarative_base()

class User(Base):
    """User model"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    scans = relationship("Scan", back_populates="user")

class Scan(Base):
    """Scan/Workflow execution model"""
    __tablename__ = "scans"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    workflow_name = Column(String(100), nullable=False)
    target = Column(String(255), nullable=False)
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    results = Column(Text)  # JSON string
    report_path = Column(String(500))
    
    # Relationships
    user = relationship("User", back_populates="scans")
    tasks = relationship("Task", back_populates="scan")

class Task(Base):
    """Individual task execution model"""
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True)
    scan_id = Column(Integer, ForeignKey("scans.id"))
    task_name = Column(String(100), nullable=False)
    tool = Column(String(50), nullable=False)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    output = Column(Text)  # JSON string
    errors = Column(Text)
    
    # Relationships
    scan = relationship("Scan", back_populates="tasks")

# Create engine and session
engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

def init_database():
    """Initialize database"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        db.close()