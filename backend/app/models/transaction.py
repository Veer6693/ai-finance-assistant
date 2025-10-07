from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import json

# Import shared Base from database module
from app.database import Base

class FinanceTransaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Transaction details
    transaction_id = Column(String, unique=True, index=True)  # UPI transaction ID
    amount = Column(Float, nullable=False)
    transaction_type = Column(String, nullable=False)  # debit, credit
    description = Column(String)
    merchant_name = Column(String)
    merchant_category = Column(String)  # Raw category from UPI
    
    # Categorization (AI-generated)
    ai_category = Column(String)  # AI-predicted category
    ai_subcategory = Column(String)
    confidence_score = Column(Float)  # Confidence in AI categorization
    user_confirmed_category = Column(String)  # User-corrected category
    
    # Temporal features
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # UPI-specific fields
    upi_id = Column(String)  # Sender/Receiver UPI ID
    reference_number = Column(String)
    bank_reference = Column(String)
    payment_method = Column(String)  # upi, card, netbanking, etc.
    payment_provider = Column(String)  # paytm, phonepe, gpay, etc.
    vpa = Column(String)  # Virtual Payment Address
    status = Column(String, default="pending")  # pending, completed, failed
    failure_reason = Column(String)  # In case of failed transactions
    parent_transaction_id = Column(Integer, ForeignKey("transactions.id"))  # For refunds
    
    # Location data (if available)
    location_lat = Column(Float)
    location_lng = Column(Float)
    location_name = Column(String)
    
    # AI features (computed)
    features_json = Column(Text)  # Serialized features for ML models
    is_anomaly = Column(Boolean, default=False)  # Anomaly detection flag
    tags = Column(Text)  # JSON array of tags
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'transaction_date'),
        Index('idx_category', 'ai_category'),
        Index('idx_merchant', 'merchant_name'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'description': self.description,
            'merchant_name': self.merchant_name,
            'ai_category': self.ai_category,
            'ai_subcategory': self.ai_subcategory,
            'transaction_date': self.transaction_date.isoformat() if self.transaction_date else None,
            'confidence_score': self.confidence_score,
            'is_anomaly': self.is_anomaly
        }
    
    def get_features(self):
        """Get computed features for ML models"""
        if self.features_json:
            return json.loads(self.features_json)
        return {}
    
    def set_features(self, features_dict):
        """Set computed features for ML models"""
        self.features_json = json.dumps(features_dict)

class TransactionPattern(Base):
    __tablename__ = "transaction_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # Pattern identification
    pattern_name = Column(String)  # e.g., "monthly_grocery", "weekend_entertainment"
    merchant_pattern = Column(String)  # Regex or pattern for merchant names
    amount_range_min = Column(Float)
    amount_range_max = Column(Float)
    frequency = Column(String)  # daily, weekly, monthly, etc.
    category = Column(String)
    
    # Pattern statistics
    occurrence_count = Column(Integer, default=0)
    average_amount = Column(Float)
    last_occurrence = Column(DateTime)
    confidence = Column(Float)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)