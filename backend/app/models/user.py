from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

# Import shared Base from database module
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    full_name = Column(String)
    phone_number = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # User preferences
    monthly_income = Column(Float, default=0.0)
    savings_goal = Column(Float, default=0.0)
    risk_tolerance = Column(String, default="moderate")  # conservative, moderate, aggressive
    
    # Relationships
    transactions = relationship("FinanceTransaction", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    user_preferences = relationship("UserPreference", back_populates="user", uselist=False)

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # ML Model preferences
    enable_auto_categorization = Column(Boolean, default=True)
    enable_spending_alerts = Column(Boolean, default=True)
    enable_investment_suggestions = Column(Boolean, default=False)
    
    # Notification preferences
    email_notifications = Column(Boolean, default=True)
    sms_notifications = Column(Boolean, default=False)
    budget_alert_threshold = Column(Float, default=0.8)  # 80% of budget
    
    # AI preferences
    learning_rate = Column(Float, default=0.01)
    model_update_frequency = Column(String, default="weekly")
    
    user = relationship("User", back_populates="user_preferences")