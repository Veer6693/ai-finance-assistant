from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import pandas as pd

from app.models.budget import Budget, BudgetHistory, SavingsGoal
from app.models.transaction import FinanceTransaction
from app.models.user import User
from app.routes.auth import get_current_user
from app.ai_modules.forecaster import SpendingForecaster
from app.ai_modules.budget_optimizer import ContextualBudgetOptimizer, UserContext
from app.database import get_db

router = APIRouter()

# Initialize AI components
forecaster = SpendingForecaster()
budget_optimizer = ContextualBudgetOptimizer()

# Pydantic models
class SpendingAnalysisResponse(BaseModel):
    total_spending: float
    total_income: float
    category_breakdown: Dict[str, float]
    time_period: str
    daily_average: float
    trend_analysis: Dict[str, Any]
    comparison_with_previous: Optional[Dict[str, Any]]

class BudgetPerformanceResponse(BaseModel):
    budget_name: str
    allocated_amount: float
    spent_amount: float
    remaining_amount: float
    utilization_percentage: float
    is_over_budget: bool
    days_remaining: int
    projected_end_amount: float

class ForecastResponse(BaseModel):
    predictions: List[Dict[str, Any]]
    total_predicted_spending: float
    confidence_intervals: Dict[str, float]
    insights: List[str]

class AnomalyDetectionResponse(BaseModel):
    anomalies: List[Dict[str, Any]]
    total_anomalies: int
    anomaly_rate: float
    severity_breakdown: Dict[str, int]

@router.get("/spending-summary")
async def get_spending_analysis(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    category: Optional[str] = Query(None, description="Filter by category"),
    compare_with_previous: bool = Query(False, description="Compare with previous period"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive spending analysis"""
    
    # Default to current month if no dates provided
    if not start_date:
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if not end_date:
        end_date = datetime.now()
    
    # Get expense transactions (debit)
    expense_query = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= start_date,
        FinanceTransaction.transaction_date <= end_date
    )
    
    if category:
        expense_query = expense_query.filter(FinanceTransaction.ai_category == category)
    
    expense_transactions = expense_query.all()
    
    # Get income transactions (credit)
    income_query = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_type == 'credit',
        FinanceTransaction.transaction_date >= start_date,
        FinanceTransaction.transaction_date <= end_date
    )
    
    income_transactions = income_query.all()
    
    # Calculate total income
    total_income = sum(t.amount for t in income_transactions)
    
    if not expense_transactions and not income_transactions:
        return SpendingAnalysisResponse(
            total_spending=0.0,
            total_income=0.0,
            category_breakdown={},
            time_period=f"{start_date.date()} to {end_date.date()}",
            daily_average=0.0,
            trend_analysis={"trend": "no_data", "correlation": 0.0},
            comparison_with_previous=None
        )
    
    # Calculate metrics
    total_spending = sum(t.amount for t in expense_transactions)
    days_in_period = (end_date - start_date).days + 1
    daily_average = total_spending / days_in_period
    
    # Category breakdown (expenses only) - prioritize user-selected categories
    category_breakdown = {}
    for transaction in expense_transactions:
        # Use merchant_category (user-selected) first, then fall back to ai_category
        cat = transaction.merchant_category or transaction.ai_category or 'other'
        category_breakdown[cat] = category_breakdown.get(cat, 0) + transaction.amount
    
    # Trend analysis (using expense transactions)
    df = pd.DataFrame([{
        'amount': t.amount,
        'date': t.transaction_date.date(),
        'days_from_start': (t.transaction_date.date() - start_date.date()).days
    } for t in expense_transactions])
    
    trend_correlation = df['amount'].corr(df['days_from_start']) if len(df) > 1 else 0
    trend_direction = "increasing" if trend_correlation > 0.1 else "decreasing" if trend_correlation < -0.1 else "stable"
    
    trend_analysis = {
        "trend": trend_direction,
        "correlation": trend_correlation,
        "daily_variance": df['amount'].std() if len(df) > 1 else 0
    }
    
    # Comparison with previous period
    comparison = None
    if compare_with_previous:
        period_length = end_date - start_date
        prev_start = start_date - period_length
        prev_end = start_date
        
        # Previous expenses
        prev_expense_transactions = db.query(FinanceTransaction).filter(
            FinanceTransaction.user_id == current_user.id,
            FinanceTransaction.transaction_type == 'debit',
            FinanceTransaction.transaction_date >= prev_start,
            FinanceTransaction.transaction_date < prev_end
        ).all()
        
        # Previous income
        prev_income_transactions = db.query(FinanceTransaction).filter(
            FinanceTransaction.user_id == current_user.id,
            FinanceTransaction.transaction_type == 'credit',
            FinanceTransaction.transaction_date >= prev_start,
            FinanceTransaction.transaction_date < prev_end
        ).all()
        
        if prev_expense_transactions or prev_income_transactions:
            prev_total_spending = sum(t.amount for t in prev_expense_transactions)
            prev_total_income = sum(t.amount for t in prev_income_transactions)
            change_amount = total_spending - prev_total_spending
            change_percentage = (change_amount / prev_total_spending * 100) if prev_total_spending > 0 else 0
            income_change = total_income - prev_total_income
            income_change_percentage = (income_change / prev_total_income * 100) if prev_total_income > 0 else 0
            
            comparison = {
                "previous_total_spending": prev_total_spending,
                "previous_total_income": prev_total_income,
                "spending_change_amount": change_amount,
                "spending_change_percentage": change_percentage,
                "income_change_amount": income_change,
                "income_change_percentage": income_change_percentage,
                "period": f"{prev_start.date()} to {prev_end.date()}"
            }
    
    return SpendingAnalysisResponse(
        total_spending=total_spending,
        total_income=total_income,
        category_breakdown=category_breakdown,
        time_period=f"{start_date.date()} to {end_date.date()}",
        daily_average=daily_average,
        trend_analysis=trend_analysis,
        comparison_with_previous=comparison
    )

@router.get("/monthly-trends")
async def get_monthly_trends(
    months: int = Query(6, description="Number of months to analyze"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly spending trends"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # Get transactions for the period
    transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_date >= start_date,
        FinanceTransaction.transaction_date <= end_date
    ).all()
    
    if not transactions:
        return {"trends": [], "total_months": months, "avg_monthly_spending": 0}
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame([{
        'date': t.transaction_date,
        'amount': abs(t.amount),
        'category': t.ai_category or t.merchant_category or 'Other',
        'month': t.transaction_date.strftime('%Y-%m')
    } for t in transactions])
    
    # Group by month
    monthly_data = df.groupby('month').agg({
        'amount': 'sum',
        'category': 'count'
    }).reset_index()
    
    monthly_data.columns = ['month', 'total_spending', 'transaction_count']
    
    # Calculate trends
    trends = []
    for _, row in monthly_data.iterrows():
        trends.append({
            'month': row['month'],
            'total_spending': float(row['total_spending']),
            'transaction_count': int(row['transaction_count']),
            'avg_transaction_amount': float(row['total_spending'] / row['transaction_count'])
        })
    
    return {
        "trends": trends,
        "total_months": len(trends),
        "avg_monthly_spending": float(monthly_data['total_spending'].mean()) if len(monthly_data) > 0 else 0
    }

@router.get("/budget-performance")
async def get_budget_performance(
    budget_id: Optional[int] = Query(None, description="Specific budget ID"),
    monthly: bool = Query(True, description="Show monthly performance"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # Get active budgets for current month
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = (current_month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    budgets = db.query(Budget).filter(
        Budget.user_id == current_user.id,
        Budget.is_active == True,
        Budget.start_date <= current_month_end,
        Budget.end_date >= current_month_start
    ).all()
    
    performance_list = []
    
    for budget in budgets:
        # Calculate actual spending for this budget category
        # Need to check both merchant_category and ai_category, and handle category mapping
        category_variants = []
        
        # Add the budget category as-is
        category_variants.append(budget.category)
        
        # Add mapped variants (in case budget stores display format but transactions store backend format)
        category_mapping = {
            'Food & Dining': ['food', 'groceries'],
            'Transportation': ['transport'],
            'Shopping': ['shopping'],
            'Entertainment': ['entertainment'], 
            'Bills & Utilities': ['bills'],
            'Healthcare': ['healthcare'],
            'Investment': ['investment'],
            'Income': ['income'],
            'Other': ['other']
        }
        
        # Add mapped backend categories if budget uses display format
        if budget.category in category_mapping:
            category_variants.extend(category_mapping[budget.category])
        
        # Also add reverse mapping (if budget uses backend format but transactions use display format)
        reverse_mapping = {
            'food': ['Food & Dining'],
            'groceries': ['Food & Dining'],
            'transport': ['Transportation'],
            'shopping': ['Shopping'],
            'entertainment': ['Entertainment'],
            'bills': ['Bills & Utilities'],
            'healthcare': ['Healthcare'],
            'investment': ['Investment'],
            'income': ['Income'],
            'other': ['Other']
        }
        
        if budget.category in reverse_mapping:
            category_variants.extend(reverse_mapping[budget.category])
        
        # Remove duplicates
        category_variants = list(set(category_variants))
        
        # Query transactions that match any of the category variants in either field
        actual_spent = db.query(FinanceTransaction).filter(
            FinanceTransaction.user_id == current_user.id,
            FinanceTransaction.transaction_type == 'debit',
            or_(
                FinanceTransaction.merchant_category.in_(category_variants),
                FinanceTransaction.ai_category.in_(category_variants)
            ),
            FinanceTransaction.transaction_date >= max(budget.start_date, current_month_start),
            FinanceTransaction.transaction_date <= min(budget.end_date, current_month_end)
        ).with_entities(FinanceTransaction.amount).all()
        
        total_spent = sum(amount[0] for amount in actual_spent) if actual_spent else 0.0
        
        # Update budget spent amount
        budget.spent_amount = total_spent
        budget.remaining_amount = budget.allocated_amount - total_spent
        
        # Calculate metrics
        utilization_percentage = (total_spent / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
        days_remaining = (budget.end_date - datetime.now()).days
        
        # Project end-of-period spending
        days_elapsed = (datetime.now() - budget.start_date).days + 1
        daily_average = total_spent / days_elapsed if days_elapsed > 0 else 0
        total_days = (budget.end_date - budget.start_date).days + 1
        projected_end_amount = daily_average * total_days
        
        performance_list.append(BudgetPerformanceResponse(
            budget_name=budget.name,
            allocated_amount=budget.allocated_amount,
            spent_amount=total_spent,
            remaining_amount=budget.remaining_amount,
            utilization_percentage=utilization_percentage,
            is_over_budget=total_spent > budget.allocated_amount,
            days_remaining=max(0, days_remaining),
            projected_end_amount=projected_end_amount
        ))
    
    db.commit()  # Save updated spent amounts
    
    return performance_list

@router.get("/forecasting")
async def get_spending_forecast(
    days: int = Query(30, description="Number of days to forecast"),
    category: Optional[str] = Query(None, description="Category to forecast"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get spending forecast using LSTM model"""
    
    # Get historical transactions for training/prediction
    historical_transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= datetime.now() - timedelta(days=120)
    ).all()
    
    if len(historical_transactions) < 30:
        raise HTTPException(
            status_code=400, 
            detail="Insufficient historical data for forecasting. Need at least 30 days of transactions."
        )
    
    # Convert to format for forecaster
    transaction_data = []
    for t in historical_transactions:
        if not category or t.ai_category == category:
            transaction_data.append({
                "amount": t.amount,
                "ai_category": t.ai_category,
                "transaction_date": t.transaction_date,
                "merchant_name": t.merchant_name,
                "description": t.description,
                "transaction_type": t.transaction_type
            })
    
    if len(transaction_data) < 30:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient data for {'category ' + category if category else 'forecasting'}. Need at least 30 transactions."
        )
    
    try:
        # Check if model is trained, if not train it
        if not forecaster.load_model():
            # Train model with user data
            X, y, daily_data = forecaster.prepare_data(transaction_data)
            if len(X) >= forecaster.sequence_length:
                forecaster.train(transaction_data)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient data for model training. Need more historical transactions."
                )
        
        # Make predictions
        X, y, daily_data = forecaster.prepare_data(transaction_data)
        predictions_data = forecaster.predict_future_spending(daily_data, days)
        
        # Generate insights
        insights = [
            f"Based on your spending patterns, you're projected to spend ₹{predictions_data['total_predicted_spending']:.2f} over the next {days} days.",
        ]
        
        # Add category-specific insights
        if predictions_data['predictions']:
            avg_daily = predictions_data['total_predicted_spending'] / days
            current_avg = sum(t['amount'] for t in transaction_data[-7:]) / 7  # Last week average
            
            if avg_daily > current_avg * 1.2:
                insights.append("Your predicted spending is 20% higher than recent averages.")
            elif avg_daily < current_avg * 0.8:
                insights.append("Your predicted spending is 20% lower than recent averages.")
            else:
                insights.append("Your predicted spending aligns with recent patterns.")
        
        # Calculate confidence intervals (simplified)
        confidence_intervals = {
            "low": predictions_data['total_predicted_spending'] * 0.8,
            "high": predictions_data['total_predicted_spending'] * 1.2,
            "average_confidence": sum(p.get('confidence', 0.5) for p in predictions_data['predictions']) / len(predictions_data['predictions']) if predictions_data['predictions'] else 0.5
        }
        
        return ForecastResponse(
            predictions=predictions_data['predictions'],
            total_predicted_spending=predictions_data['total_predicted_spending'],
            confidence_intervals=confidence_intervals,
            insights=insights
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")

@router.get("/anomalies")
async def detect_anomalies(
    days_back: int = Query(30, description="Number of days to analyze"),
    sensitivity: float = Query(0.95, description="Anomaly detection sensitivity (0.5-0.99)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    
    # Get historical transactions
    start_date = datetime.now() - timedelta(days=days_back)
    transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= start_date
    ).all()
    
    if len(transactions) < 10:
        return AnomalyDetectionResponse(
            anomalies=[],
            total_anomalies=0,
            anomaly_rate=0.0,
            severity_breakdown={"low": 0, "medium": 0, "high": 0}
        )
    
    # Convert to format for anomaly detection
    transaction_data = []
    for t in transactions:
        transaction_data.append({
            "amount": t.amount,
            "ai_category": t.ai_category,
            "transaction_date": t.transaction_date,
            "merchant_name": t.merchant_name,
            "description": t.description,
            "transaction_type": t.transaction_type,
            "transaction_id": t.transaction_id
        })
    
    try:
        # Prepare daily data for anomaly detection
        X, y, daily_data = forecaster.prepare_data(transaction_data)
        
        # Calculate threshold based on sensitivity
        threshold_std = 3.0 - (sensitivity * 2.0)  # Convert sensitivity to std threshold
        
        # Detect anomalies
        anomaly_results = forecaster.detect_anomalies(daily_data, threshold_std)
        
        # Count by severity
        severity_breakdown = {"low": 0, "medium": 0, "high": 0}
        for anomaly in anomaly_results['anomalies']:
            severity = anomaly.get('severity', 'medium')
            severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1
        
        return AnomalyDetectionResponse(
            anomalies=anomaly_results['anomalies'],
            total_anomalies=anomaly_results['total_anomalies'],
            anomaly_rate=anomaly_results['anomaly_rate'],
            severity_breakdown=severity_breakdown
        )
    
    except Exception as e:
        # Fallback to simple statistical anomaly detection
        amounts = [t.amount for t in transactions]
        mean_amount = sum(amounts) / len(amounts)
        std_amount = (sum((x - mean_amount) ** 2 for x in amounts) / len(amounts)) ** 0.5
        threshold = mean_amount + threshold_std * std_amount
        
        statistical_anomalies = []
        for t in transactions:
            if t.amount > threshold:
                statistical_anomalies.append({
                    "date": t.transaction_date.strftime("%Y-%m-%d"),
                    "amount": t.amount,
                    "transaction_id": t.transaction_id,
                    "merchant": t.merchant_name,
                    "description": t.description,
                    "type": "statistical",
                    "severity": "high" if t.amount > threshold * 1.5 else "medium",
                    "reason": f"Amount ₹{t.amount:.2f} is {((t.amount - mean_amount) / std_amount):.1f} standard deviations above average"
                })
        
        severity_breakdown = {"low": 0, "medium": 0, "high": 0}
        for anomaly in statistical_anomalies:
            severity_breakdown[anomaly['severity']] += 1
        
        return AnomalyDetectionResponse(
            anomalies=statistical_anomalies,
            total_anomalies=len(statistical_anomalies),
            anomaly_rate=len(statistical_anomalies) / len(transactions) * 100,
            severity_breakdown=severity_breakdown
        )

@router.get("/insights")
async def get_monthly_insights(
    month: Optional[int] = Query(None, description="Month (1-12)"),
    year: Optional[int] = Query(None, description="Year"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get monthly spending insights and recommendations"""
    
    # Get current month data
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    current_month_end = datetime.now()
    
    # Get transactions for current month
    current_month_transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= current_month_start,
        FinanceTransaction.transaction_date <= current_month_end
    ).all()
    
    # Get previous month for comparison
    prev_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    prev_month_end = current_month_start - timedelta(days=1)
    
    prev_month_transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= prev_month_start,
        FinanceTransaction.transaction_date <= prev_month_end
    ).all()
    
    # Calculate insights
    current_total = sum(t.amount for t in current_month_transactions)
    prev_total = sum(t.amount for t in prev_month_transactions)
    
    # Category analysis
    current_categories = {}
    for t in current_month_transactions:
        cat = t.ai_category or 'other'
        current_categories[cat] = current_categories.get(cat, 0) + t.amount
    
    # Generate insights
    insights = {
        "spending_summary": {
            "current_month_total": current_total,
            "previous_month_total": prev_total,
            "month_over_month_change": current_total - prev_total,
            "change_percentage": ((current_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
        },
        "category_breakdown": current_categories,
        "top_spending_categories": sorted(current_categories.items(), key=lambda x: x[1], reverse=True)[:5],
        "recommendations": [],
        "achievements": []
    }
    
    # Generate recommendations
    if current_total > prev_total * 1.2:
        insights["recommendations"].append("Your spending has increased significantly this month. Consider reviewing your budget.")
    
    if current_categories.get("entertainment", 0) > current_total * 0.15:
        insights["recommendations"].append("Entertainment spending is high. Consider setting a stricter budget for discretionary expenses.")
    
    if current_categories.get("food", 0) > current_total * 0.3:
        insights["recommendations"].append("Food expenses are above recommended levels. Try cooking more meals at home.")
    
    # Generate achievements
    if current_total < prev_total:
        insights["achievements"].append(f"Great job! You've reduced spending by ₹{prev_total - current_total:.2f} this month.")
    
    if len(current_month_transactions) < len(prev_month_transactions):
        insights["achievements"].append("You made fewer transactions this month, showing more mindful spending.")
    
    return insights