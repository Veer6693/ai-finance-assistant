import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import json
from sqlalchemy.orm import Session

def prepare_transaction_data(transactions: List[Any]) -> pd.DataFrame:
    """Convert transaction objects to pandas DataFrame"""
    data = []
    for txn in transactions:
        data.append({
            'id': txn.id,
            'transaction_id': txn.transaction_id,
            'amount': txn.amount,
            'transaction_type': txn.transaction_type,
            'description': txn.description,
            'merchant_name': txn.merchant_name,
            'ai_category': txn.ai_category,
            'transaction_date': txn.transaction_date,
            'is_anomaly': txn.is_anomaly,
            'confidence_score': txn.confidence_score
        })
    return pd.DataFrame(data)

def calculate_spending_summary(df: pd.DataFrame, group_by: str = 'ai_category') -> Dict[str, float]:
    """Calculate spending summary grouped by specified column"""
    if df.empty:
        return {}
    
    # Filter only debit transactions
    spending_df = df[df['transaction_type'] == 'debit']
    
    if spending_df.empty:
        return {}
    
    return spending_df.groupby(group_by)['amount'].sum().to_dict()

def calculate_monthly_trends(df: pd.DataFrame, months: int = 6) -> Dict[str, Any]:
    """Calculate monthly spending trends"""
    if df.empty:
        return {"trend": "no_data", "monthly_totals": {}}
    
    # Filter last N months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    df_filtered = df[
        (df['transaction_date'] >= start_date) & 
        (df['transaction_type'] == 'debit')
    ]
    
    if df_filtered.empty:
        return {"trend": "no_data", "monthly_totals": {}}
    
    # Group by month
    df_filtered['month'] = df_filtered['transaction_date'].dt.to_period('M')
    monthly_totals = df_filtered.groupby('month')['amount'].sum().to_dict()
    
    # Convert period to string for JSON serialization
    monthly_totals = {str(k): v for k, v in monthly_totals.items()}
    
    # Calculate trend
    if len(monthly_totals) > 1:
        values = list(monthly_totals.values())
        trend = "increasing" if values[-1] > values[0] else "decreasing"
    else:
        trend = "stable"
    
    return {
        "trend": trend,
        "monthly_totals": monthly_totals,
        "average_monthly": sum(monthly_totals.values()) / len(monthly_totals) if monthly_totals else 0
    }

def detect_spending_anomalies(df: pd.DataFrame, threshold_std: float = 2.5) -> List[Dict[str, Any]]:
    """Detect spending anomalies using statistical methods"""
    if df.empty:
        return []
    
    spending_df = df[df['transaction_type'] == 'debit']
    
    if len(spending_df) < 10:  # Need minimum data for anomaly detection
        return []
    
    # Calculate statistical thresholds
    mean_amount = spending_df['amount'].mean()
    std_amount = spending_df['amount'].std()
    threshold = mean_amount + threshold_std * std_amount
    
    # Find anomalies
    anomalies = spending_df[spending_df['amount'] > threshold]
    
    anomaly_list = []
    for _, row in anomalies.iterrows():
        anomaly_list.append({
            'transaction_id': row['transaction_id'],
            'date': row['transaction_date'].strftime('%Y-%m-%d'),
            'amount': row['amount'],
            'merchant': row['merchant_name'],
            'category': row['ai_category'],
            'description': row['description'],
            'severity': 'high' if row['amount'] > threshold * 1.5 else 'medium',
            'deviation_factor': (row['amount'] - mean_amount) / std_amount
        })
    
    return anomaly_list

def calculate_budget_performance(budgets: List[Any], actual_spending: Dict[str, float]) -> List[Dict[str, Any]]:
    """Calculate budget performance metrics"""
    performance = []
    
    for budget in budgets:
        actual = actual_spending.get(budget.category, 0.0)
        allocated = budget.allocated_amount
        
        utilization = (actual / allocated * 100) if allocated > 0 else 0
        variance = actual - allocated
        variance_pct = (variance / allocated * 100) if allocated > 0 else 0
        
        performance.append({
            'category': budget.category,
            'allocated': allocated,
            'actual': actual,
            'utilization': utilization,
            'variance': variance,
            'variance_percentage': variance_pct,
            'status': 'over_budget' if actual > allocated else 'under_budget',
            'remaining': max(0, allocated - actual)
        })
    
    return performance

def generate_spending_insights(df: pd.DataFrame, user_income: float = 0) -> Dict[str, Any]:
    """Generate insights from spending data"""
    insights = {
        'patterns': [],
        'recommendations': [],
        'achievements': [],
        'alerts': []
    }
    
    if df.empty:
        return insights
    
    spending_df = df[df['transaction_type'] == 'debit']
    
    if spending_df.empty:
        return insights
    
    total_spending = spending_df['amount'].sum()
    avg_transaction = spending_df['amount'].mean()
    
    # Pattern insights
    category_spending = spending_df.groupby('ai_category')['amount'].sum()
    top_category = category_spending.idxmax() if not category_spending.empty else None
    
    if top_category:
        top_amount = category_spending[top_category]
        insights['patterns'].append(
            f"Your highest spending category is {top_category} at ₹{top_amount:,.2f}"
        )
    
    # Weekend vs weekday analysis
    spending_df['is_weekend'] = spending_df['transaction_date'].dt.dayofweek >= 5
    weekend_spending = spending_df[spending_df['is_weekend']]['amount'].sum()
    weekday_spending = spending_df[~spending_df['is_weekend']]['amount'].sum()
    
    if weekend_spending > weekday_spending * 0.5:  # Weekend spending > 50% of weekday
        insights['patterns'].append(
            "You tend to spend more on weekends. Consider setting weekend budgets."
        )
    
    # Income-based recommendations
    if user_income > 0:
        spending_ratio = total_spending / user_income
        
        if spending_ratio > 0.9:
            insights['alerts'].append(
                "Your spending is very high relative to income. Consider reviewing your budget."
            )
        elif spending_ratio < 0.5:
            insights['achievements'].append(
                "Great job! You're maintaining a healthy spending-to-income ratio."
            )
        
        # Category-specific recommendations
        for category, amount in category_spending.items():
            category_ratio = amount / user_income
            
            if category == 'food' and category_ratio > 0.25:
                insights['recommendations'].append(
                    "Food spending is high. Consider cooking more meals at home."
                )
            elif category == 'entertainment' and category_ratio > 0.15:
                insights['recommendations'].append(
                    "Entertainment spending could be optimized. Look for free or low-cost alternatives."
                )
    
    # Transaction frequency insights
    transaction_count = len(spending_df)
    if transaction_count > 100:  # High transaction volume
        insights['patterns'].append(
            "You make frequent transactions. Consider consolidating purchases to save time and fees."
        )
    
    # Large transaction alerts
    large_transactions = spending_df[spending_df['amount'] > avg_transaction * 3]
    if len(large_transactions) > 0:
        insights['alerts'].append(
            f"You have {len(large_transactions)} unusually large transactions this period."
        )
    
    return insights

def format_date_range(start_date: datetime, end_date: datetime) -> str:
    """Format date range for display"""
    if start_date.date() == end_date.date():
        return start_date.strftime('%Y-%m-%d')
    elif start_date.year == end_date.year and start_date.month == end_date.month:
        return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%d')}"
    else:
        return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

def calculate_savings_rate(income_transactions: List, expense_transactions: List) -> float:
    """Calculate savings rate from income and expense transactions"""
    total_income = sum(t.amount for t in income_transactions)
    total_expenses = sum(t.amount for t in expense_transactions)
    
    if total_income == 0:
        return 0.0
    
    return ((total_income - total_expenses) / total_income) * 100

def get_category_insights(category: str, amount: float, user_income: float) -> List[str]:
    """Get category-specific insights and recommendations"""
    insights = []
    
    if user_income <= 0:
        return insights
    
    category_ratio = amount / user_income
    
    category_benchmarks = {
        'food': {'max': 0.25, 'ideal': 0.15},
        'transport': {'max': 0.20, 'ideal': 0.10},
        'entertainment': {'max': 0.15, 'ideal': 0.08},
        'shopping': {'max': 0.20, 'ideal': 0.10},
        'bills': {'max': 0.30, 'ideal': 0.25},
        'healthcare': {'max': 0.10, 'ideal': 0.05},
        'investment': {'min': 0.10, 'ideal': 0.20},
        'savings': {'min': 0.10, 'ideal': 0.20}
    }
    
    if category in category_benchmarks:
        benchmark = category_benchmarks[category]
        
        if 'max' in benchmark and category_ratio > benchmark['max']:
            insights.append(f"{category.title()} spending is above recommended maximum of {benchmark['max']*100:.0f}% of income")
        elif 'min' in benchmark and category_ratio < benchmark['min']:
            insights.append(f"Consider increasing {category} allocation to at least {benchmark['min']*100:.0f}% of income")
        elif category_ratio <= benchmark.get('ideal', 0.15):
            insights.append(f"Great! Your {category} spending is within ideal range")
    
    return insights

def export_data_to_csv(data: List[Dict[str, Any]], filename: str) -> str:
    """Export data to CSV format"""
    df = pd.DataFrame(data)
    
    # Create exports directory if it doesn't exist
    import os
    os.makedirs('exports', exist_ok=True)
    
    filepath = f"exports/{filename}"
    df.to_csv(filepath, index=False)
    
    return filepath

def validate_date_range(start_date: datetime, end_date: datetime) -> bool:
    """Validate date range"""
    if start_date > end_date:
        return False
    
    # Don't allow future dates
    if end_date > datetime.now():
        return False
    
    # Don't allow ranges too far in the past (more than 5 years)
    if start_date < datetime.now() - timedelta(days=5*365):
        return False
    
    return True

def clean_transaction_data(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Clean and validate transaction data"""
    cleaned = []
    
    for txn in transactions:
        # Skip transactions with invalid amounts
        if txn.get('amount', 0) <= 0:
            continue
        
        # Ensure required fields exist
        if not all(key in txn for key in ['transaction_id', 'amount', 'transaction_type']):
            continue
        
        # Clean merchant name and description
        txn['merchant_name'] = txn.get('merchant_name', 'Unknown').strip()
        txn['description'] = txn.get('description', '').strip()
        
        # Ensure category is set
        if not txn.get('ai_category'):
            txn['ai_category'] = 'other'
        
        cleaned.append(txn)
    
    return cleaned