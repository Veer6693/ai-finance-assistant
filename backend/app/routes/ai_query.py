from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel

from app.models.user import User
from app.routes.auth import get_current_user
from app.ai_modules.nlp_processor import NLPQueryProcessor, QueryIntent
from app.ai_modules.categorizer import TransactionCategorizer
from app.ai_modules.forecaster import SpendingForecaster
from app.ai_modules.budget_optimizer import ContextualBudgetOptimizer
from app.database import get_db

router = APIRouter()

# Initialize AI components
nlp_processor = NLPQueryProcessor()
categorizer = TransactionCategorizer()
forecaster = SpendingForecaster()
budget_optimizer = ContextualBudgetOptimizer()

# Pydantic models
class QueryRequest(BaseModel):
    query: str
    context: Dict[str, Any] = {}

class QueryResponse(BaseModel):
    query: str
    intent: str
    entities: Dict[str, Any]
    answer: str
    data: Dict[str, Any]
    confidence: float
    processing_time: float

@router.post("/query", response_model=QueryResponse)
async def process_natural_language_query(
    query_request: QueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> QueryResponse:
    """Process natural language query about finances"""
    
    from datetime import datetime
    start_time = datetime.now()
    
    # Add user context
    user_context = {
        "user_id": current_user.id,
        "income": current_user.monthly_income,
        "preferences": query_request.context
    }
    
    # Process query with NLP
    query_intent = nlp_processor.process_query(query_request.query, user_context)
    
    # Execute query based on intent
    try:
        if query_intent.intent_type == "spending_analysis":
            result = await _handle_spending_query(query_intent, current_user, db)
        elif query_intent.intent_type == "budget_query":
            result = await _handle_budget_query(query_intent, current_user, db)
        elif query_intent.intent_type == "transaction_search":
            result = await _handle_transaction_search(query_intent, current_user, db)
        elif query_intent.intent_type == "savings_analysis":
            result = await _handle_savings_query(query_intent, current_user, db)
        elif query_intent.intent_type == "prediction":
            result = await _handle_prediction_query(query_intent, current_user, db)
        else:
            result = {
                "answer": "I understand your query but I'm not sure how to help with that specific request. Please try asking about your spending, budget, or transactions.",
                "data": {}
            }
    
    except Exception as e:
        result = {
            "answer": f"I encountered an error processing your query: {str(e)}. Please try rephrasing your question.",
            "data": {}
        }
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return QueryResponse(
        query=query_request.query,
        intent=query_intent.intent_type,
        entities=query_intent.entities,
        answer=result["answer"],
        data=result["data"],
        confidence=query_intent.confidence,
        processing_time=processing_time
    )

async def _handle_spending_query(query_intent: QueryIntent, user: User, db: Session) -> Dict[str, Any]:
    """Handle spending analysis queries"""
    from app.models.transaction import FinanceTransaction
    from datetime import datetime, timedelta
    
    entities = query_intent.entities
    
    # Build query
    query = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == user.id,
        FinanceTransaction.transaction_type == 'debit'
    )
    
    # Apply filters from entities
    if "start_date" in entities and "end_date" in entities:
        query = query.filter(
            FinanceTransaction.transaction_date >= entities["start_date"],
            FinanceTransaction.transaction_date <= entities["end_date"]
        )
        time_period = entities.get("time_period", "the specified period")
    else:
        # Default to current month
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        query = query.filter(FinanceTransaction.transaction_date >= start_date)
        time_period = "this month"
    
    if "category" in entities:
        query = query.filter(FinanceTransaction.ai_category == entities["category"])
    
    if "merchant" in entities:
        query = query.filter(FinanceTransaction.merchant_name.ilike(f"%{entities['merchant']}%"))
    
    if "amount" in entities:
        amount = entities["amount"]
        comparison = entities.get("amount_comparison", "equal_to")
        
        if comparison == "greater_than":
            query = query.filter(FinanceTransaction.amount > amount)
        elif comparison == "less_than":
            query = query.filter(FinanceTransaction.amount < amount)
        else:
            query = query.filter(FinanceTransaction.amount == amount)
    
    # Execute query
    transactions = query.all()
    
    if not transactions:
        return {
            "answer": f"I didn't find any transactions matching your criteria for {time_period}.",
            "data": {"total_spending": 0, "transaction_count": 0}
        }
    
    total_spending = sum(t.amount for t in transactions)
    transaction_count = len(transactions)
    
    # Generate answer
    if "category" in entities:
        category = entities["category"]
        answer = f"You spent ₹{total_spending:,.2f} on {category} during {time_period} across {transaction_count} transactions."
    else:
        answer = f"Your total spending during {time_period} was ₹{total_spending:,.2f} across {transaction_count} transactions."
    
    # Add category breakdown if no specific category was requested
    category_breakdown = {}
    if "category" not in entities:
        for t in transactions:
            cat = t.ai_category or 'other'
            category_breakdown[cat] = category_breakdown.get(cat, 0) + t.amount
        
        if len(category_breakdown) > 1:
            top_category = max(category_breakdown.items(), key=lambda x: x[1])
            answer += f" Your highest spending category was {top_category[0]} at ₹{top_category[1]:,.2f}."
    
    return {
        "answer": answer,
        "data": {
            "total_spending": total_spending,
            "transaction_count": transaction_count,
            "category_breakdown": category_breakdown,
            "time_period": time_period,
            "average_transaction": total_spending / transaction_count if transaction_count > 0 else 0
        }
    }

async def _handle_budget_query(query_intent: QueryIntent, user: User, db: Session) -> Dict[str, Any]:
    """Handle budget-related queries"""
    from app.models.budget import Budget
    from datetime import datetime
    
    entities = query_intent.entities
    
    # Get current budgets
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    query = db.query(Budget).filter(
        Budget.user_id == user.id,
        Budget.is_active == True,
        Budget.start_date <= datetime.now(),
        Budget.end_date >= current_month_start
    )
    
    if "category" in entities:
        query = query.filter(Budget.category == entities["category"])
    
    budgets = query.all()
    
    if not budgets:
        category_text = f" for {entities['category']}" if "category" in entities else ""
        return {
            "answer": f"You don't have any active budgets{category_text} for this month.",
            "data": {}
        }
    
    # Calculate budget status
    budget_info = []
    total_allocated = 0
    total_spent = 0
    
    for budget in budgets:
        utilization = (budget.spent_amount / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
        budget_info.append({
            "category": budget.category,
            "allocated": budget.allocated_amount,
            "spent": budget.spent_amount,
            "remaining": budget.remaining_amount,
            "utilization": utilization,
            "is_over_budget": budget.spent_amount > budget.allocated_amount
        })
        total_allocated += budget.allocated_amount
        total_spent += budget.spent_amount
    
    # Generate answer
    if len(budgets) == 1:
        budget = budgets[0]
        utilization = (budget.spent_amount / budget.allocated_amount * 100) if budget.allocated_amount > 0 else 0
        answer = f"Your {budget.category} budget is ₹{budget.allocated_amount:,.2f}. You've spent ₹{budget.spent_amount:,.2f} ({utilization:.1f}%) with ₹{budget.remaining_amount:,.2f} remaining."
        
        if budget.spent_amount > budget.allocated_amount:
            answer += " You're over budget for this category."
        elif utilization > 80:
            answer += " You're close to your budget limit."
    else:
        overall_utilization = (total_spent / total_allocated * 100) if total_allocated > 0 else 0
        answer = f"Across your {len(budgets)} active budgets, you've allocated ₹{total_allocated:,.2f} and spent ₹{total_spent:,.2f} ({overall_utilization:.1f}%)."
        
        over_budget_count = sum(1 for info in budget_info if info["is_over_budget"])
        if over_budget_count > 0:
            answer += f" {over_budget_count} budget(s) are over the limit."
    
    return {
        "answer": answer,
        "data": {
            "budgets": budget_info,
            "total_allocated": total_allocated,
            "total_spent": total_spent,
            "overall_utilization": (total_spent / total_allocated * 100) if total_allocated > 0 else 0
        }
    }

async def _handle_transaction_search(query_intent: QueryIntent, user: User, db: Session) -> Dict[str, Any]:
    """Handle transaction search queries"""
    from app.models.transaction import FinanceTransaction
    
    entities = query_intent.entities
    
    # Build search query
    query = db.query(FinanceTransaction).filter(FinanceTransaction.user_id == user.id)
    
    # Apply filters
    filters_applied = []
    
    if "start_date" in entities and "end_date" in entities:
        query = query.filter(
            FinanceTransaction.transaction_date >= entities["start_date"],
            FinanceTransaction.transaction_date <= entities["end_date"]
        )
        filters_applied.append(f"during {entities.get('time_period', 'the specified period')}")
    
    if "category" in entities:
        query = query.filter(FinanceTransaction.ai_category == entities["category"])
        filters_applied.append(f"in {entities['category']} category")
    
    if "merchant" in entities:
        query = query.filter(FinanceTransaction.merchant_name.ilike(f"%{entities['merchant']}%"))
        filters_applied.append(f"from {entities['merchant']}")
    
    if "amount" in entities:
        amount = entities["amount"]
        comparison = entities.get("amount_comparison", "equal_to")
        
        if comparison == "greater_than":
            query = query.filter(FinanceTransaction.amount > amount)
            filters_applied.append(f"above ₹{amount:,.2f}")
        elif comparison == "less_than":
            query = query.filter(FinanceTransaction.amount < amount)
            filters_applied.append(f"below ₹{amount:,.2f}")
        else:
            query = query.filter(FinanceTransaction.amount == amount)
            filters_applied.append(f"equal to ₹{amount:,.2f}")
    
    # Execute query (limit to recent results)
    transactions = query.order_by(FinanceTransaction.transaction_date.desc()).limit(20).all()
    
    filter_text = " " + " and ".join(filters_applied) if filters_applied else ""
    
    if not transactions:
        return {
            "answer": f"I didn't find any transactions{filter_text}.",
            "data": {"transactions": [], "count": 0}
        }
    
    # Format transaction data
    transaction_data = []
    total_amount = 0
    
    for t in transactions:
        transaction_data.append({
            "id": t.transaction_id,
            "date": t.transaction_date.strftime("%Y-%m-%d %H:%M"),
            "amount": t.amount,
            "type": t.transaction_type,
            "merchant": t.merchant_name,
            "category": t.ai_category,
            "description": t.description
        })
        total_amount += t.amount if t.transaction_type == 'debit' else -t.amount
    
    answer = f"I found {len(transactions)} transaction(s){filter_text}."
    if len(transactions) == 20:
        answer += " Showing the 20 most recent results."
    
    if total_amount != 0:
        answer += f" Total amount: ₹{abs(total_amount):,.2f}."
    
    return {
        "answer": answer,
        "data": {
            "transactions": transaction_data,
            "count": len(transactions),
            "total_amount": total_amount,
            "showing_recent": len(transactions) == 20
        }
    }

async def _handle_savings_query(query_intent: QueryIntent, user: User, db: Session) -> Dict[str, Any]:
    """Handle savings analysis queries"""
    from app.models.transaction import FinanceTransaction
    from app.models.budget import SavingsGoal
    from datetime import datetime, timedelta
    
    # Get income vs spending
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    income_transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == user.id,
        FinanceTransaction.transaction_type == 'credit',
        FinanceTransaction.transaction_date >= current_month_start
    ).all()
    
    spending_transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= current_month_start
    ).all()
    
    total_income = sum(t.amount for t in income_transactions)
    total_spending = sum(t.amount for t in spending_transactions)
    net_savings = total_income - total_spending
    
    # Get savings goals
    savings_goals = db.query(SavingsGoal).filter(
        SavingsGoal.user_id == user.id,
        SavingsGoal.is_active == True
    ).all()
    
    # Calculate savings rate
    savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0
    
    answer = f"This month, you've saved ₹{net_savings:,.2f} (savings rate: {savings_rate:.1f}%). "
    
    if net_savings > 0:
        answer += "Great job on saving money! "
    elif net_savings < 0:
        answer += "You're spending more than your income this month. "
    
    if savings_goals:
        goal = savings_goals[0]  # Take first active goal
        progress = (goal.current_amount / goal.target_amount * 100) if goal.target_amount > 0 else 0
        answer += f"Your savings goal progress: ₹{goal.current_amount:,.2f} / ₹{goal.target_amount:,.2f} ({progress:.1f}%)."
    
    return {
        "answer": answer,
        "data": {
            "net_savings": net_savings,
            "savings_rate": savings_rate,
            "total_income": total_income,
            "total_spending": total_spending,
            "savings_goals": [{"name": g.name, "current": g.current_amount, "target": g.target_amount} for g in savings_goals]
        }
    }

async def _handle_prediction_query(query_intent: QueryIntent, user: User, db: Session) -> Dict[str, Any]:
    """Handle spending prediction queries"""
    from app.models.transaction import FinanceTransaction
    from datetime import datetime, timedelta
    
    # Get historical data
    historical_transactions = db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == user.id,
        FinanceTransaction.transaction_type == 'debit',
        FinanceTransaction.transaction_date >= datetime.now() - timedelta(days=90)
    ).all()
    
    if len(historical_transactions) < 30:
        return {
            "answer": "I need more transaction history to make accurate predictions. Please add more transactions or wait until you have at least 30 days of data.",
            "data": {}
        }
    
    try:
        # Use simple prediction based on recent averages
        recent_transactions = [t for t in historical_transactions if t.transaction_date >= datetime.now() - timedelta(days=30)]
        
        if recent_transactions:
            avg_daily_spending = sum(t.amount for t in recent_transactions) / 30
            
            # Extract time period from entities
            entities = query_intent.entities
            days_ahead = 30  # Default
            
            if "time_period" in entities:
                time_period = entities["time_period"]
                if "week" in time_period:
                    days_ahead = 7
                elif "month" in time_period:
                    days_ahead = 30
                elif "year" in time_period:
                    days_ahead = 365
            
            predicted_spending = avg_daily_spending * days_ahead
            
            period_text = f"next {days_ahead} days"
            if days_ahead == 7:
                period_text = "next week"
            elif days_ahead == 30:
                period_text = "next month"
            elif days_ahead == 365:
                period_text = "next year"
            
            answer = f"Based on your recent spending patterns, I predict you'll spend approximately ₹{predicted_spending:,.2f} over the {period_text}."
            
            # Add category breakdown
            category_spending = {}
            for t in recent_transactions:
                cat = t.ai_category or 'other'
                category_spending[cat] = category_spending.get(cat, 0) + t.amount
            
            if category_spending:
                top_category = max(category_spending.items(), key=lambda x: x[1])
                predicted_top_amount = (top_category[1] / 30) * days_ahead
                answer += f" Your highest spending category will likely be {top_category[0]} at approximately ₹{predicted_top_amount:,.2f}."
            
            return {
                "answer": answer,
                "data": {
                    "predicted_total": predicted_spending,
                    "days_ahead": days_ahead,
                    "daily_average": avg_daily_spending,
                    "category_predictions": {cat: (amount / 30) * days_ahead for cat, amount in category_spending.items()}
                }
            }
        else:
            return {
                "answer": "I don't have enough recent data to make accurate predictions.",
                "data": {}
            }
    
    except Exception as e:
        return {
            "answer": f"I encountered an error while generating predictions: {str(e)}",
            "data": {}
        }

@router.get("/categories")
async def get_ai_categories():
    """Get available AI categories and their descriptions"""
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

@router.get("/model-status")
async def get_ai_model_status(current_user: User = Depends(get_current_user)):
    """Get status of AI models"""
    
    # Check if models are loaded/trained
    categorizer_status = "ready" if categorizer.kmeans_model is not None else "not_trained"
    forecaster_status = "ready" if forecaster.lstm_model is not None else "not_trained"
    
    return {
        "categorizer": {
            "status": categorizer_status,
            "stats": categorizer.get_categorization_stats()
        },
        "forecaster": {
            "status": forecaster_status,
            "metrics": forecaster.model_metrics
        },
        "nlp_processor": {
            "status": "ready" if nlp_processor.nlp is not None else "fallback_mode",
            "model": nlp_processor.model_name
        },
        "budget_optimizer": {
            "status": "ready",
            "exploration_rate": budget_optimizer.exploration_rate
        }
    }