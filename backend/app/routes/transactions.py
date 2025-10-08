from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import json

from app.models.transaction import FinanceTransaction, TransactionPattern
from app.models.user import User
from app.routes.auth import get_current_user
from app.ai_modules.categorizer import TransactionCategorizer
from app.utils.data_simulator import TransactionDataSimulator
from app.database import get_db

router = APIRouter()

# Initialize AI components
categorizer = TransactionCategorizer()
simulator = TransactionDataSimulator()

# Pydantic models
class TransactionCreate(BaseModel):
    amount: float
    transaction_type: str  # 'debit' or 'credit'
    description: str
    merchant_name: str
    merchant_category: Optional[str] = None
    upi_id: Optional[str] = None
    location_lat: Optional[float] = None
    location_lng: Optional[float] = None
    location_name: Optional[str] = None
    transaction_date: Optional[datetime] = None

class TransactionResponse(BaseModel):
    id: int
    transaction_id: str
    amount: float
    transaction_type: str
    description: str
    merchant_name: str
    merchant_category: Optional[str]
    ai_category: Optional[str]
    ai_subcategory: Optional[str]
    confidence_score: Optional[float]
    transaction_date: datetime
    upi_id: Optional[str]
    location_name: Optional[str]
    is_anomaly: bool
    
    class Config:
        from_attributes = True

class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    page: int
    page_size: int
    has_more: bool

class TransactionSummary(BaseModel):
    total_transactions: int
    total_spending: float
    total_income: float
    average_transaction: float
    categories: dict
    time_period: str

@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction"""
    
    # Generate transaction ID
    import uuid
    transaction_id = f"TXN{uuid.uuid4().hex[:10].upper()}"
    
    # Use AI categorization
    transaction_dict = transaction_data.dict()
    transaction_dict["transaction_id"] = transaction_id
    
    category, confidence = categorizer.predict_category(transaction_dict)
    
    # Create transaction
    new_transaction = FinanceTransaction(
        user_id=current_user.id,
        transaction_id=transaction_id,
        amount=transaction_data.amount,
        transaction_type=transaction_data.transaction_type,
        description=transaction_data.description,
        merchant_name=transaction_data.merchant_name,
        merchant_category=transaction_data.merchant_category,
        ai_category=category,
        confidence_score=confidence,
        transaction_date=transaction_data.transaction_date or datetime.utcnow(),
        upi_id=transaction_data.upi_id,
        location_lat=transaction_data.location_lat,
        location_lng=transaction_data.location_lng,
        location_name=transaction_data.location_name,
        is_anomaly=False  # Will be determined by anomaly detection
    )
    
    db.add(new_transaction)
    db.commit()
    db.refresh(new_transaction)
    
    return TransactionResponse.from_orm(new_transaction)

@router.get("/", response_model=TransactionListResponse)
async def get_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None),
    transaction_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    min_amount: Optional[float] = Query(None),
    max_amount: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user transactions with filtering and pagination"""
    
    query = db.query(FinanceTransaction).filter(FinanceTransaction.user_id == current_user.id)
    
    # Apply filters
    if category:
        query = query.filter(FinanceTransaction.ai_category == category)
    
    if transaction_type:
        query = query.filter(FinanceTransaction.transaction_type == transaction_type)
    
    if start_date:
        query = query.filter(FinanceTransaction.transaction_date >= start_date)
    
    if end_date:
        query = query.filter(FinanceTransaction.transaction_date <= end_date)
    
    if min_amount is not None:
        query = query.filter(FinanceTransaction.amount >= min_amount)
    
    if max_amount is not None:
        query = query.filter(FinanceTransaction.amount <= max_amount)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            FinanceTransaction.description.ilike(search_filter) |
            FinanceTransaction.merchant_name.ilike(search_filter)
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    offset = (page - 1) * page_size
    transactions = query.order_by(FinanceTransaction.transaction_date.desc()).offset(offset).limit(page_size).all()
    
    return TransactionListResponse(
        transactions=[TransactionResponse.from_orm(t) for t in transactions],
        total=total,
        page=page,
        page_size=page_size,
        has_more=offset + page_size < total
    )

@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific transaction"""
    
    transaction = db.query(FinanceTransaction).filter(
        FinanceTransaction.transaction_id == transaction_id,
        FinanceTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return TransactionResponse.from_orm(transaction)

@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    transaction_data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a transaction"""
    
    transaction = db.query(FinanceTransaction).filter(
        FinanceTransaction.transaction_id == transaction_id,
        FinanceTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update transaction fields
    for field, value in transaction_data.dict(exclude_unset=True).items():
        if hasattr(transaction, field):
            setattr(transaction, field, value)
    
    # Re-categorize with AI if description or merchant changed
    if hasattr(transaction_data, 'description') or hasattr(transaction_data, 'merchant_name'):
        try:
            ai_result = categorizer.categorize_transaction(
                description=transaction.description,
                merchant=transaction.merchant_name,
                amount=transaction.amount
            )
            
            transaction.ai_category = ai_result.get('category')
            transaction.ai_subcategory = ai_result.get('subcategory')
            transaction.confidence_score = ai_result.get('confidence', 0.0)
        except Exception as e:
            print(f"AI categorization failed: {e}")
    
    db.commit()
    db.refresh(transaction)
    
    return TransactionResponse.from_orm(transaction)

@router.put("/{transaction_id}/category")
async def update_transaction_category(
    transaction_id: str,
    category: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update transaction category (user feedback for ML)"""
    
    transaction = db.query(FinanceTransaction).filter(
        FinanceTransaction.transaction_id == transaction_id,
        FinanceTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Update category
    transaction.user_confirmed_category = category
    transaction.ai_category = category  # Also update AI category for consistency
    transaction.confidence_score = 1.0  # Max confidence for user-confirmed
    
    db.commit()
    
    # Update categorizer with feedback (for future improvement)
    categorizer.update_model_with_feedback(transaction_id, category)
    
    return {"message": "Category updated successfully"}

@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction"""
    
    transaction = db.query(FinanceTransaction).filter(
        FinanceTransaction.transaction_id == transaction_id,
        FinanceTransaction.user_id == current_user.id
    ).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    db.delete(transaction)
    db.commit()
    
    return {"message": "Transaction deleted successfully"}

@router.get("/summary/overview", response_model=TransactionSummary)
async def get_transaction_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction summary for a time period"""
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.now()
    
    # Get transactions in date range
    transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_date >= start_date,
        FinanceTransaction.transaction_date <= end_date
    ).all()
    
    if not transactions:
        return TransactionSummary(
            total_transactions=0,
            total_spending=0.0,
            total_income=0.0,
            average_transaction=0.0,
            categories={},
            time_period=f"{start_date.date()} to {end_date.date()}"
        )
    
    # Calculate metrics
    spending_transactions = [t for t in transactions if t.transaction_type == 'debit']
    income_transactions = [t for t in transactions if t.transaction_type == 'credit']
    
    total_spending = sum(t.amount for t in spending_transactions)
    total_income = sum(t.amount for t in income_transactions)
    
    # Category breakdown
    categories = {}
    for transaction in spending_transactions:
        category = transaction.ai_category or 'other'
        categories[category] = categories.get(category, 0) + transaction.amount
    
    return TransactionSummary(
        total_transactions=len(transactions),
        total_spending=total_spending,
        total_income=total_income,
        average_transaction=sum(t.amount for t in transactions) / len(transactions),
        categories=categories,
        time_period=f"{start_date.date()} to {end_date.date()}"
    )

@router.get("/patterns/analysis")
async def get_spending_patterns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spending patterns and insights"""
    
    # Get last 90 days of transactions
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_date >= start_date,
        FinanceTransaction.transaction_type == 'debit'
    ).all()
    
    if not transactions:
        return {"message": "No transactions found for analysis"}
    
    # Convert to format for analysis
    transaction_data = []
    for t in transactions:
        transaction_data.append({
            "amount": t.amount,
            "ai_category": t.ai_category,
            "transaction_date": t.transaction_date,
            "merchant_name": t.merchant_name,
            "description": t.description
        })
    
    # Analyze patterns
    import pandas as pd
    df = pd.DataFrame(transaction_data)
    
    patterns = {
        "daily_average": df['amount'].mean(),
        "weekly_totals": df.groupby(df['transaction_date'].dt.week)['amount'].sum().to_dict(),
        "category_averages": df.groupby('ai_category')['amount'].mean().to_dict(),
        "most_frequent_merchants": df['merchant_name'].value_counts().head(5).to_dict(),
        "spending_trends": {
            "trend": "increasing" if df['amount'].corr(range(len(df))) > 0 else "decreasing",
            "correlation": df['amount'].corr(range(len(df)))
        }
    }
    
    return patterns

@router.post("/generate-demo-data")
async def generate_demo_transactions(
    num_transactions: int = Query(100, ge=10, le=500),
    days_back: int = Query(90, ge=30, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate demo transaction data for testing (development only)"""
    
    # Generate transactions using simulator
    transactions_data = simulator.generate_transactions(
        user_id=current_user.id,
        num_transactions=num_transactions,
        days_back=days_back
    )
    
    # Save to database
    created_transactions = []
    for txn_data in transactions_data:
        transaction = FinanceTransaction(
            user_id=txn_data["user_id"],
            transaction_id=txn_data["transaction_id"],
            amount=txn_data["amount"],
            transaction_type=txn_data["transaction_type"],
            description=txn_data["description"],
            merchant_name=txn_data["merchant_name"],
            merchant_category=txn_data["merchant_category"],
            ai_category=txn_data["ai_category"],
            confidence_score=txn_data["confidence_score"],
            transaction_date=txn_data["transaction_date"],
            upi_id=txn_data["upi_id"],
            reference_number=txn_data["reference_number"],
            bank_reference=txn_data["bank_reference"],
            location_lat=txn_data.get("location_lat"),
            location_lng=txn_data.get("location_lng"),
            location_name=txn_data.get("location_name"),
            is_anomaly=txn_data["is_anomaly"],
            tags=txn_data["tags"]
        )
        
        db.add(transaction)
        created_transactions.append(transaction)
    
    db.commit()
    
    return {
        "message": f"Generated {len(created_transactions)} demo transactions",
        "transactions_created": len(created_transactions),
        "date_range": {
            "start": min(t.transaction_date for t in created_transactions).isoformat(),
            "end": max(t.transaction_date for t in created_transactions).isoformat()
        }
    }

@router.get("/categories/list")
async def get_available_categories():
    """Get list of available transaction categories"""
    return {
        "categories": categorizer.categories,
        "descriptions": {
            "food": "Restaurant meals, food delivery, dining out",
            "groceries": "Supermarket shopping, household items, vegetables",
            "transport": "Cab rides, fuel, public transport, parking",
            "shopping": "Online shopping, clothes, electronics, retail",
            "entertainment": "Movies, subscriptions, games, concerts",
            "bills": "Utilities, mobile recharge, internet, rent",
            "healthcare": "Medical expenses, pharmacy, hospital visits",
            "investment": "Stocks, mutual funds, SIP, insurance",
            "education": "Courses, books, training, skill development",
            "other": "Miscellaneous expenses not fitting other categories"
        }
    }