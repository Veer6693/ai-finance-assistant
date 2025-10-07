import random
import json
from datetime import datetime, timedelta
from typing import List, Dict
import uuid

class TransactionDataSimulator:
    """
    Simulates realistic transaction data for AI training and demo purposes.
    Generates transactions that mimic real UPI/banking patterns in India.
    """
    
    def __init__(self):
        # Indian merchant categories and typical spending patterns
        self.merchant_categories = {
            "food": {
                "merchants": [
                    "Swiggy", "Zomato", "McDonald's", "KFC", "Domino's Pizza", 
                    "Subway", "Pizza Hut", "Cafe Coffee Day", "Starbucks",
                    "Local Restaurant", "Street Food Vendor", "Haldiram's"
                ],
                "amount_range": (50, 800),
                "frequency_weight": 25  # Higher weight = more frequent
            },
            "groceries": {
                "merchants": [
                    "Big Bazaar", "Reliance Fresh", "Spencer's", "D-Mart",
                    "Local Grocery Store", "Blinkit", "BigBasket", "Grofers",
                    "More Supermarket", "24/7 Store"
                ],
                "amount_range": (200, 3000),
                "frequency_weight": 15
            },
            "transport": {
                "merchants": [
                    "Uber", "Ola", "Auto Rickshaw", "Metro Card Recharge",
                    "Bus Pass", "Petrol Pump", "Rapido", "Local Taxi",
                    "Train Booking", "Flight Booking"
                ],
                "amount_range": (30, 5000),
                "frequency_weight": 20
            },
            "shopping": {
                "merchants": [
                    "Amazon", "Flipkart", "Myntra", "Ajio", "Nykaa",
                    "Lifestyle", "Pantaloons", "Westside", "Shoppers Stop",
                    "Local Shop", "Meesho", "NYKAA"
                ],
                "amount_range": (100, 5000),
                "frequency_weight": 12
            },
            "entertainment": {
                "merchants": [
                    "BookMyShow", "Netflix", "Amazon Prime", "Spotify",
                    "Disney+ Hotstar", "PVR Cinemas", "INOX", "Game Zone",
                    "Bowling Alley", "Concert Tickets"
                ],
                "amount_range": (99, 2000),
                "frequency_weight": 8
            },
            "bills": {
                "merchants": [
                    "Electricity Bill", "Gas Bill", "Water Bill", "Internet Bill",
                    "Mobile Recharge", "DTH Recharge", "Jio", "Airtel",
                    "BSNL", "Municipal Tax", "Society Maintenance"
                ],
                "amount_range": (100, 8000),
                "frequency_weight": 10
            },
            "healthcare": {
                "merchants": [
                    "Apollo Pharmacy", "1mg", "Local Clinic", "Hospital",
                    "Dentist", "Lab Test", "Netmeds", "PharmEasy",
                    "Medical Store", "Health Checkup"
                ],
                "amount_range": (50, 10000),
                "frequency_weight": 5
            },
            "investment": {
                "merchants": [
                    "Zerodha", "Groww", "SIP Transfer", "Mutual Fund",
                    "Stock Purchase", "Gold Purchase", "EPF", "PPF",
                    "Insurance Premium", "ULIP"
                ],
                "amount_range": (500, 50000),
                "frequency_weight": 3
            },
            "education": {
                "merchants": [
                    "Course Fee", "Book Purchase", "Online Course",
                    "Udemy", "Coursera", "Unacademy", "BYJU'S",
                    "School Fee", "Tuition Fee", "Library Fee"
                ],
                "amount_range": (200, 25000),
                "frequency_weight": 2
            }
        }
        
        # UPI payment modes
        self.payment_modes = [
            "UPI", "Credit Card", "Debit Card", "Net Banking", "Wallet"
        ]
        
        # Common UPI IDs patterns
        self.upi_patterns = [
            "user@paytm", "user@phonepe", "user@googlepay", "user@amazonpay",
            "user@ybl", "user@okaxis", "user@ibl", "user@icici"
        ]
    
    def generate_transactions(self, 
                            user_id: int, 
                            num_transactions: int = 100,
                            days_back: int = 90) -> List[Dict]:
        """
        Generate realistic transaction data for a user.
        
        Args:
            user_id: User ID for the transactions
            num_transactions: Number of transactions to generate
            days_back: Number of days to go back from today
            
        Returns:
            List of transaction dictionaries
        """
        transactions = []
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        for i in range(num_transactions):
            # Randomly select category based on frequency weights
            category = self._select_weighted_category()
            category_data = self.merchant_categories[category]
            
            # Generate transaction details
            transaction = {
                "user_id": user_id,
                "transaction_id": f"TXN{uuid.uuid4().hex[:10].upper()}",
                "amount": round(random.uniform(*category_data["amount_range"]), 2),
                "transaction_type": "debit",  # Most transactions are debits
                "description": self._generate_description(category),
                "merchant_name": random.choice(category_data["merchants"]),
                "merchant_category": category,
                "ai_category": category,  # Pre-assign for demo
                "confidence_score": round(random.uniform(0.7, 0.95), 2),
                "transaction_date": self._generate_random_date(start_date, end_date),
                "upi_id": self._generate_upi_id(),
                "reference_number": f"REF{random.randint(100000000, 999999999)}",
                "bank_reference": f"BNK{random.randint(100000, 999999)}",
                "is_anomaly": False,
                "tags": json.dumps(self._generate_tags(category))
            }
            
            # Occasionally generate income transactions
            if random.random() < 0.05:  # 5% chance
                transaction.update({
                    "transaction_type": "credit",
                    "amount": round(random.uniform(10000, 100000), 2),
                    "merchant_name": random.choice(["Salary", "Freelance Payment", "Investment Return", "Refund"]),
                    "merchant_category": "income",
                    "ai_category": "income"
                })
            
            # Occasionally mark as anomaly (unusual spending)
            if random.random() < 0.02:  # 2% chance
                transaction["is_anomaly"] = True
                transaction["amount"] *= random.uniform(3, 10)  # Unusually high amount
            
            # Add location data for some transactions
            if random.random() < 0.3:  # 30% chance
                transaction.update({
                    "location_lat": round(random.uniform(12.9716, 28.7041), 6),  # India lat range
                    "location_lng": round(random.uniform(77.5946, 88.3639), 6),  # India lng range
                    "location_name": random.choice(["Mumbai", "Delhi", "Bangalore", "Chennai", "Kolkata", "Pune", "Hyderabad"])
                })
            
            transactions.append(transaction)
        
        # Sort by date
        transactions.sort(key=lambda x: x["transaction_date"])
        
        return transactions
    
    def _select_weighted_category(self) -> str:
        """Select category based on frequency weights"""
        categories = list(self.merchant_categories.keys())
        weights = [self.merchant_categories[cat]["frequency_weight"] for cat in categories]
        return random.choices(categories, weights=weights)[0]
    
    def _generate_description(self, category: str) -> str:
        """Generate realistic transaction descriptions"""
        descriptions = {
            "food": ["Food Order", "Restaurant Bill", "Dinner", "Lunch", "Snacks"],
            "groceries": ["Grocery Shopping", "Weekly Groceries", "Household Items"],
            "transport": ["Cab Ride", "Fuel", "Parking", "Auto Ride", "Metro"],
            "shopping": ["Online Shopping", "Clothes", "Electronics", "Books"],
            "entertainment": ["Movie Tickets", "Subscription", "Games", "Concert"],
            "bills": ["Utility Bill", "Mobile Bill", "Internet", "Electricity"],
            "healthcare": ["Medicine", "Doctor Visit", "Health Checkup", "Pharmacy"],
            "investment": ["Investment", "SIP", "Stock Purchase", "Insurance"],
            "education": ["Course Fee", "Books", "Online Learning", "Tuition"]
        }
        return random.choice(descriptions.get(category, ["Payment"]))
    
    def _generate_random_date(self, start_date: datetime, end_date: datetime) -> datetime:
        """Generate random date between start and end"""
        time_between = end_date - start_date
        days_between = time_between.days
        random_days = random.randrange(days_between)
        random_seconds = random.randrange(24 * 60 * 60)  # Random time of day
        return start_date + timedelta(days=random_days, seconds=random_seconds)
    
    def _generate_upi_id(self) -> str:
        """Generate realistic UPI ID"""
        username = f"user{random.randint(1000, 9999)}"
        provider = random.choice(["@paytm", "@phonepe", "@googlepay", "@ybl"])
        return f"{username}{provider}"
    
    def _generate_tags(self, category: str) -> List[str]:
        """Generate relevant tags for transactions"""
        tag_map = {
            "food": ["dining", "delivery", "restaurant"],
            "groceries": ["household", "weekly", "essentials"],
            "transport": ["travel", "commute", "fuel"],
            "shopping": ["online", "retail", "purchase"],
            "entertainment": ["leisure", "subscription", "recreation"],
            "bills": ["recurring", "utility", "monthly"],
            "healthcare": ["medical", "wellness", "pharmacy"],
            "investment": ["finance", "savings", "growth"],
            "education": ["learning", "skill", "development"]
        }
        return random.sample(tag_map.get(category, ["general"]), k=random.randint(1, 2))
    
    def generate_budget_data(self, user_id: int, transactions: List[Dict]) -> List[Dict]:
        """
        Generate budget data based on transaction patterns.
        
        Args:
            user_id: User ID
            transactions: List of transactions to analyze
            
        Returns:
            List of budget dictionaries
        """
        # Analyze spending patterns by category
        category_spending = {}
        for txn in transactions:
            if txn["transaction_type"] == "debit":
                category = txn["ai_category"]
                category_spending[category] = category_spending.get(category, 0) + txn["amount"]
        
        budgets = []
        start_date = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        for category, total_spent in category_spending.items():
            # Calculate average monthly spending
            avg_monthly = total_spent / 3  # Assuming 3 months of data
            
            # Set budget with some buffer (10-30% more than average spending)
            buffer_multiplier = random.uniform(1.1, 1.3)
            allocated_amount = round(avg_monthly * buffer_multiplier, 2)
            
            # Current month's spending (partial)
            current_spent = round(avg_monthly * random.uniform(0.3, 0.9), 2)
            
            budget = {
                "user_id": user_id,
                "name": f"{category.title()} Budget",
                "category": category,
                "budget_type": "monthly",
                "allocated_amount": allocated_amount,
                "spent_amount": current_spent,
                "remaining_amount": allocated_amount - current_spent,
                "start_date": start_date,
                "end_date": end_date,
                "ai_recommended_amount": round(avg_monthly * 1.2, 2),
                "is_active": True,
                "alert_threshold": 0.8
            }
            budgets.append(budget)
        
        return budgets
    
    def generate_user_profile(self, email: str, full_name: str) -> Dict:
        """Generate a realistic user profile"""
        return {
            "email": email,
            "full_name": full_name,
            "phone_number": f"+91{random.randint(7000000000, 9999999999)}",
            "monthly_income": round(random.uniform(30000, 200000), 2),
            "savings_goal": round(random.uniform(5000, 50000), 2),
            "risk_tolerance": random.choice(["conservative", "moderate", "aggressive"])
        }

# Example usage
if __name__ == "__main__":
    simulator = TransactionDataSimulator()
    
    # Generate sample data
    transactions = simulator.generate_transactions(user_id=1, num_transactions=150, days_back=90)
    budgets = simulator.generate_budget_data(user_id=1, transactions=transactions)
    user_profile = simulator.generate_user_profile("demo@example.com", "Demo User")
    
    print(f"Generated {len(transactions)} transactions")
    print(f"Generated {len(budgets)} budgets")
    print("Sample transaction:", transactions[0])
    print("Sample budget:", budgets[0])