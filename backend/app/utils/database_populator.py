from datetime import datetime, timedelta
from typing import List, Dict, Optional
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models.transaction import FinanceTransaction
from app.models.budget import Budget
from app.utils.data_simulator import TransactionDataSimulator

class DatabasePopulator:
    """
    Populates the database with simulated data for development and demo purposes.
    """
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.simulator = TransactionDataSimulator()
    
    def populate_demo_data(self, user_id: int, clear_existing: bool = True) -> Dict:
        """
        Populate database with comprehensive demo data for a user.
        
        Args:
            user_id: User ID to populate data for
            clear_existing: Whether to clear existing data first
            
        Returns:
            Summary of created data
        """
        if clear_existing:
            self._clear_user_data(user_id)
        
        # Generate transactions
        transactions_data = self.simulator.generate_transactions(
            user_id=user_id,
            num_transactions=200,
            days_back=120
        )
        
        transactions = self._create_transactions(transactions_data)
        
        # Generate budgets based on transaction patterns
        budgets_data = self.simulator.generate_budget_data(user_id, transactions_data)
        budgets = self._create_budgets(budgets_data)
        
        # Create transaction patterns
        patterns = self._create_transaction_patterns(user_id, transactions_data)
        
        summary = {
            "user_id": user_id,
            "transactions_created": len(transactions),
            "budgets_created": len(budgets),
            "patterns_created": len(patterns),
            "date_range": {
                "start": min(t.transaction_date for t in transactions).isoformat(),
                "end": max(t.transaction_date for t in transactions).isoformat()
            },
            "total_spending": sum(t.amount for t in transactions if t.transaction_type == "debit"),
            "total_income": sum(t.amount for t in transactions if t.transaction_type == "credit"),
            "categories": list(set(t.ai_category for t in transactions))
        }
        
        return summary
    
    def _clear_user_data(self, user_id: int):
        """Clear existing data for user"""
        self.db.query(FinanceTransaction).filter(FinanceTransaction.user_id == user_id).delete()
        self.db.query(Budget).filter(Budget.user_id == user_id).delete()
        self.db.commit()
    
    def _create_transactions(self, transactions_data: List[Dict]) -> List[FinanceTransaction]:
        """Create transaction records in database"""
        transactions = []
        
        for txn_data in transactions_data:
            # Create computed features for ML
            features = self._compute_transaction_features(txn_data)
            
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
                tags=txn_data["tags"],
                features_json=features
            )
            
            self.db.add(transaction)
            transactions.append(transaction)
        
        self.db.commit()
        return transactions
    
    def _create_budgets(self, budgets_data: List[Dict]) -> List[Budget]:
        """Create budget records in database"""
        budgets = []
        
        for budget_data in budgets_data:
            budget = Budget(
                user_id=budget_data["user_id"],
                name=budget_data["name"],
                category=budget_data["category"],
                budget_type=budget_data["budget_type"],
                allocated_amount=budget_data["allocated_amount"],
                spent_amount=budget_data["spent_amount"],
                remaining_amount=budget_data["remaining_amount"],
                start_date=budget_data["start_date"],
                end_date=budget_data["end_date"],
                ai_recommended_amount=budget_data["ai_recommended_amount"],
                is_active=budget_data["is_active"],
                alert_threshold=budget_data["alert_threshold"]
            )
            
            self.db.add(budget)
            budgets.append(budget)
        
        self.db.commit()
        return budgets
    
    def _create_transaction_patterns(self, user_id: int, transactions_data: List[Dict]) -> List:
        """Analyze and create transaction patterns"""
        # This would typically involve ML analysis
        # For demo, we'll create simple patterns
        patterns = []
        
        # Group by merchant and analyze patterns
        df = pd.DataFrame(transactions_data)
        merchant_patterns = df.groupby('merchant_name').agg({
            'amount': ['mean', 'min', 'max', 'count'],
            'ai_category': 'first'
        }).round(2)
        
        # Create patterns for frequent merchants (>3 transactions)
        for merchant, data in merchant_patterns.iterrows():
            if data[('amount', 'count')] >= 3:
                pattern_data = {
                    "user_id": user_id,
                    "pattern_name": f"{merchant}_pattern",
                    "merchant_pattern": merchant,
                    "amount_range_min": float(data[('amount', 'min')]),
                    "amount_range_max": float(data[('amount', 'max')]),
                    "average_amount": float(data[('amount', 'mean')]),
                    "occurrence_count": int(data[('amount', 'count')]),
                    "category": data[('ai_category', 'first')],
                    "frequency": "weekly" if data[('amount', 'count')] > 10 else "monthly",
                    "confidence": min(0.9, data[('amount', 'count')] / 20.0),
                    "last_occurrence": datetime.now()
                }
                patterns.append(pattern_data)
        
        return patterns
    
    def _compute_transaction_features(self, txn_data: Dict) -> str:
        """Compute ML features for a transaction"""
        import json
        
        txn_date = txn_data["transaction_date"]
        
        features = {
            "amount_log": np.log1p(txn_data["amount"]),
            "hour": txn_date.hour,
            "day_of_week": txn_date.weekday(),
            "day_of_month": txn_date.day,
            "month": txn_date.month,
            "is_weekend": txn_date.weekday() >= 5,
            "is_evening": 18 <= txn_date.hour <= 23,
            "is_morning": 6 <= txn_date.hour <= 11,
            "merchant_category_encoded": hash(txn_data["merchant_category"]) % 100,
            "amount_category": "low" if txn_data["amount"] < 500 else "medium" if txn_data["amount"] < 2000 else "high",
            "has_location": bool(txn_data.get("location_lat")),
            "description_length": len(txn_data["description"]),
            "merchant_name_length": len(txn_data["merchant_name"])
        }
        
        return json.dumps(features)
    
    def get_data_summary(self, user_id: int) -> Dict:
        """Get summary of existing data for user"""
        transactions = self.db.query(FinanceTransaction).filter(FinanceTransaction.user_id == user_id).all()
        budgets = self.db.query(Budget).filter(Budget.user_id == user_id).all()
        
        if not transactions:
            return {"message": "No data found for user"}
        
        df = pd.DataFrame([{
            "amount": t.amount,
            "category": t.ai_category,
            "date": t.transaction_date,
            "type": t.transaction_type
        } for t in transactions])
        
        summary = {
            "total_transactions": len(transactions),
            "total_budgets": len(budgets),
            "date_range": {
                "start": df["date"].min().isoformat(),
                "end": df["date"].max().isoformat()
            },
            "spending_by_category": df[df["type"] == "debit"].groupby("category")["amount"].sum().to_dict(),
            "total_spending": df[df["type"] == "debit"]["amount"].sum(),
            "total_income": df[df["type"] == "credit"]["amount"].sum(),
            "average_transaction": df["amount"].mean(),
            "anomalies": len([t for t in transactions if t.is_anomaly])
        }
        
        return summary