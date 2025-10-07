from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import json

# Import shared Base from database module
from app.database import Base

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Budget details
    name = Column(String, nullable=False)  # e.g., "Monthly Budget", "Vacation Fund"
    category = Column(String, nullable=False)  # food, transport, entertainment, etc.
    budget_type = Column(String, default="monthly")  # monthly, weekly, yearly, custom
    
    # Budget amounts
    allocated_amount = Column(Float, nullable=False)
    spent_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float)
    
    # Time period
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    
    # AI optimization
    ai_recommended_amount = Column(Float)  # AI-suggested budget amount
    optimization_score = Column(Float)  # How well user follows the budget
    adjustment_frequency = Column(Integer, default=0)  # How many times adjusted
    
    # Status and metadata
    is_active = Column(Boolean, default=True)
    auto_adjust = Column(Boolean, default=False)  # Allow AI to auto-adjust
    alert_threshold = Column(Float, default=0.8)  # Alert when 80% spent
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    budget_history = relationship("BudgetHistory", back_populates="budget")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'budget_type': self.budget_type,
            'allocated_amount': self.allocated_amount,
            'spent_amount': self.spent_amount,
            'remaining_amount': self.remaining_amount,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'ai_recommended_amount': self.ai_recommended_amount,
            'is_active': self.is_active,
            'alert_threshold': self.alert_threshold
        }
    
    def update_spent_amount(self, new_transaction_amount):
        """Update spent amount when new transaction is added"""
        self.spent_amount += new_transaction_amount
        self.remaining_amount = self.allocated_amount - self.spent_amount
        
    def get_utilization_percentage(self):
        """Get budget utilization as percentage"""
        if self.allocated_amount == 0:
            return 0
        return (self.spent_amount / self.allocated_amount) * 100
    
    def is_over_budget(self):
        """Check if budget is exceeded"""
        return self.spent_amount > self.allocated_amount
    
    def should_alert(self):
        """Check if alert should be sent based on threshold"""
        return self.get_utilization_percentage() >= (self.alert_threshold * 100)

class BudgetHistory(Base):
    __tablename__ = "budget_history"
    
    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    
    # Historical data
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    allocated_amount = Column(Float, nullable=False)
    actual_spent = Column(Float, nullable=False)
    variance = Column(Float)  # actual - allocated
    variance_percentage = Column(Float)
    
    # Performance metrics
    goal_achieved = Column(Boolean)  # Did user stay within budget?
    days_over_budget = Column(Integer, default=0)
    average_daily_spend = Column(Float)
    
    # AI insights
    ai_insights = Column(Text)  # JSON string with AI-generated insights
    predicted_spend = Column(Float)  # What AI predicted vs actual
    prediction_accuracy = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    budget = relationship("Budget", back_populates="budget_history")

class SavingsGoal(Base):
    __tablename__ = "savings_goals"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Goal details
    name = Column(String, nullable=False)  # e.g., "Emergency Fund", "Vacation"
    description = Column(Text)
    target_amount = Column(Float, nullable=False)
    current_amount = Column(Float, default=0.0)
    
    # Timeline
    target_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # AI recommendations
    recommended_monthly_savings = Column(Float)
    ai_achievability_score = Column(Float)  # 0-1 score of how achievable the goal is
    suggested_actions = Column(Text)  # JSON array of AI suggestions
    
    # Status
    is_active = Column(Boolean, default=True)
    is_achieved = Column(Boolean, default=False)
    achieved_date = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'target_amount': self.target_amount,
            'current_amount': self.current_amount,
            'target_date': self.target_date.isoformat() if self.target_date else None,
            'recommended_monthly_savings': self.recommended_monthly_savings,
            'ai_achievability_score': self.ai_achievability_score,
            'is_active': self.is_active,
            'is_achieved': self.is_achieved,
            'progress_percentage': (self.current_amount / self.target_amount * 100) if self.target_amount > 0 else 0
        }