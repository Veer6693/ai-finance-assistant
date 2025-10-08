from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel

from app.models.budget import Budget, BudgetHistory, SavingsGoal
from app.models.transaction import FinanceTransaction
from app.models.user import User
from app.routes.auth import get_current_user
from app.database import get_db

router = APIRouter()

# Pydantic models for request/response
class BudgetCreate(BaseModel):
    name: str
    category: str
    amount: float
    period: str = "monthly"  # monthly, weekly, yearly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    amount: Optional[float] = None
    period: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class BudgetResponse(BaseModel):
    id: int
    name: str
    category: str
    amount: float
    spent_amount: float
    remaining_amount: float
    period: str
    start_date: datetime
    end_date: datetime
    is_active: bool
    utilization_percentage: float

    class Config:
        from_attributes = True

@router.get("/", response_model=List[BudgetResponse])
async def get_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for the current user"""
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    
    budget_responses = []
    for budget in budgets:
        # Calculate spent amount from transactions
        spent_amount = db.query(FinanceTransaction).filter(
            FinanceTransaction.user_id == current_user.id,
            FinanceTransaction.category == budget.category,
            FinanceTransaction.transaction_date >= budget.start_date,
            FinanceTransaction.transaction_date <= budget.end_date
        ).with_entities(FinanceTransaction.amount).all()
        
        total_spent = sum([abs(amount[0]) for amount in spent_amount]) if spent_amount else 0
        remaining = budget.amount - total_spent
        utilization = (total_spent / budget.amount * 100) if budget.amount > 0 else 0
        
        budget_responses.append(BudgetResponse(
            id=budget.id,
            name=budget.name,
            category=budget.category,
            amount=budget.amount,
            spent_amount=total_spent,
            remaining_amount=remaining,
            period=budget.period,
            start_date=budget.start_date,
            end_date=budget.end_date,
            is_active=budget.is_active,
            utilization_percentage=utilization
        ))
    
    return budget_responses

@router.post("/", response_model=BudgetResponse)
async def create_budget(
    budget_data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget"""
    
    # Set default dates if not provided
    if not budget_data.start_date:
        budget_data.start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    if not budget_data.end_date:
        if budget_data.period == "monthly":
            # End of current month
            next_month = budget_data.start_date.replace(day=28) + timedelta(days=4)
            budget_data.end_date = next_month - timedelta(days=next_month.day)
        elif budget_data.period == "weekly":
            budget_data.end_date = budget_data.start_date + timedelta(days=7)
        else:  # yearly
            budget_data.end_date = budget_data.start_date.replace(year=budget_data.start_date.year + 1)
    
    budget = Budget(
        user_id=current_user.id,
        name=budget_data.name,
        category=budget_data.category,
        amount=budget_data.amount,
        period=budget_data.period,
        start_date=budget_data.start_date,
        end_date=budget_data.end_date,
        is_active=True
    )
    
    db.add(budget)
    db.commit()
    db.refresh(budget)
    
    return BudgetResponse(
        id=budget.id,
        name=budget.name,
        category=budget.category,
        amount=budget.amount,
        spent_amount=0,
        remaining_amount=budget.amount,
        period=budget.period,
        start_date=budget.start_date,
        end_date=budget.end_date,
        is_active=budget.is_active,
        utilization_percentage=0
    )

@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific budget by ID"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Calculate spent amount
    spent_amount = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.category == budget.category,
        FinanceTransaction.transaction_date >= budget.start_date,
        FinanceTransaction.transaction_date <= budget.end_date
    ).with_entities(FinanceTransaction.amount).all()
    
    total_spent = sum([abs(amount[0]) for amount in spent_amount]) if spent_amount else 0
    remaining = budget.amount - total_spent
    utilization = (total_spent / budget.amount * 100) if budget.amount > 0 else 0
    
    return BudgetResponse(
        id=budget.id,
        name=budget.name,
        category=budget.category,
        amount=budget.amount,
        spent_amount=total_spent,
        remaining_amount=remaining,
        period=budget.period,
        start_date=budget.start_date,
        end_date=budget.end_date,
        is_active=budget.is_active,
        utilization_percentage=utilization
    )

@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing budget"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Update fields if provided
    if budget_data.name is not None:
        budget.name = budget_data.name
    if budget_data.category is not None:
        budget.category = budget_data.category
    if budget_data.amount is not None:
        budget.amount = budget_data.amount
    if budget_data.period is not None:
        budget.period = budget_data.period
    if budget_data.start_date is not None:
        budget.start_date = budget_data.start_date
    if budget_data.end_date is not None:
        budget.end_date = budget_data.end_date
    
    budget.updated_at = datetime.now()
    
    db.commit()
    db.refresh(budget)
    
    # Calculate spent amount
    spent_amount = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.category == budget.category,
        FinanceTransaction.transaction_date >= budget.start_date,
        FinanceTransaction.transaction_date <= budget.end_date
    ).with_entities(FinanceTransaction.amount).all()
    
    total_spent = sum([abs(amount[0]) for amount in spent_amount]) if spent_amount else 0
    remaining = budget.amount - total_spent
    utilization = (total_spent / budget.amount * 100) if budget.amount > 0 else 0
    
    return BudgetResponse(
        id=budget.id,
        name=budget.name,
        category=budget.category,
        amount=budget.amount,
        spent_amount=total_spent,
        remaining_amount=remaining,
        period=budget.period,
        start_date=budget.start_date,
        end_date=budget.end_date,
        is_active=budget.is_active,
        utilization_percentage=utilization
    )

@router.delete("/{budget_id}")
async def delete_budget(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a budget"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db.delete(budget)
    db.commit()
    
    return {"message": "Budget deleted successfully"}

@router.get("/{budget_id}/performance")
async def get_budget_performance(
    budget_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed budget performance"""
    budget = db.query(Budget).filter(
        Budget.id == budget_id,
        Budget.user_id == current_user.id
    ).first()
    
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    # Get all transactions for this budget category
    transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.category == budget.category,
        FinanceTransaction.transaction_date >= budget.start_date,
        FinanceTransaction.transaction_date <= budget.end_date
    ).all()
    
    total_spent = sum([abs(t.amount) for t in transactions])
    daily_spending = {}
    
    for transaction in transactions:
        date_key = transaction.transaction_date.strftime('%Y-%m-%d')
        if date_key not in daily_spending:
            daily_spending[date_key] = 0
        daily_spending[date_key] += abs(transaction.amount)
    
    days_passed = (datetime.now().date() - budget.start_date.date()).days + 1
    days_total = (budget.end_date.date() - budget.start_date.date()).days + 1
    
    projected_spending = (total_spent / days_passed * days_total) if days_passed > 0 else 0
    
    return {
        "budget_id": budget.id,
        "budget_name": budget.name,
        "allocated_amount": budget.amount,
        "spent_amount": total_spent,
        "remaining_amount": budget.amount - total_spent,
        "utilization_percentage": (total_spent / budget.amount * 100) if budget.amount > 0 else 0,
        "days_passed": days_passed,
        "days_remaining": max(0, days_total - days_passed),
        "projected_spending": projected_spending,
        "is_over_budget": projected_spending > budget.amount,
        "daily_spending": daily_spending,
        "average_daily_spending": total_spent / days_passed if days_passed > 0 else 0
    }