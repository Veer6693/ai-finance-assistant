# Test configuration and fixtures
import pytest
import os
import sys
from unittest.mock import Mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test database URL
TEST_DATABASE_URL = "sqlite:///./test_finance_assistant.db"

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    from app.models.user import Base
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    # Cleanup
    try:
        os.remove("./test_finance_assistant.db")
    except FileNotFoundError:
        pass

@pytest.fixture(scope="function")
def test_db_session(test_engine):
    """Create a test database session"""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestingSessionLocal()
    yield session
    session.close()

@pytest.fixture
def mock_user():
    """Create a mock user for testing"""
    user = Mock()
    user.id = 1
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.monthly_income = 50000.0
    return user

@pytest.fixture
def mock_transaction():
    """Create a mock transaction for testing"""
    transaction = Mock()
    transaction.id = 1
    transaction.user_id = 1
    transaction.transaction_id = "test_txn_123"
    transaction.amount = 250.0
    transaction.transaction_type = "debit"
    transaction.description = "Test transaction"
    transaction.merchant_name = "Test Merchant"
    transaction.ai_category = "food"
    transaction.confidence_score = 0.85
    return transaction

@pytest.fixture
def sample_transactions():
    """Create sample transaction data for testing"""
    return [
        {
            "id": 1,
            "amount": 250.0,
            "transaction_type": "debit",
            "description": "SWIGGY BANGALORE",
            "merchant_name": "Swiggy",
            "ai_category": "food",
            "confidence_score": 0.9
        },
        {
            "id": 2,
            "amount": 180.0,
            "transaction_type": "debit", 
            "description": "UBER TRIP",
            "merchant_name": "Uber India",
            "ai_category": "transport",
            "confidence_score": 0.85
        },
        {
            "id": 3,
            "amount": 1200.0,
            "transaction_type": "debit",
            "description": "AMAZON ORDER",
            "merchant_name": "Amazon",
            "ai_category": "shopping",
            "confidence_score": 0.8
        }
    ]

@pytest.fixture
def auth_token():
    """Mock authentication token"""
    return "Bearer test_token_123"

@pytest.fixture
def client():
    """Create a test client"""
    from main import app
    return TestClient(app)

# Test utilities
def create_test_user(session, email="test@example.com", password="testpass123"):
    """Helper function to create a test user"""
    from app.models.user import User
    from app.utils.auth_utils import hash_password
    
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name="Test User",
        is_active=True
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

def create_test_transaction(session, user_id, amount=100.0, description="Test"):
    """Helper function to create a test transaction"""
    from app.models.transaction import Transaction
    from datetime import datetime
    
    transaction = Transaction(
        user_id=user_id,
        transaction_id=f"test_{amount}_{description}",
        amount=amount,
        transaction_type="debit",
        description=description,
        merchant_name="Test Merchant",
        ai_category="other",
        confidence_score=0.5,
        transaction_date=datetime.utcnow()
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction

# Mock AI services for testing
@pytest.fixture
def mock_transaction_categorizer():
    """Mock transaction categorizer"""
    categorizer = Mock()
    categorizer.categorize_transaction.return_value = ("food", 0.85)
    categorizer.categories = ["food", "transport", "shopping", "entertainment", "bills", "other"]
    return categorizer

@pytest.fixture
def mock_nlp_processor():
    """Mock NLP query processor"""
    processor = Mock()
    processor.process_query.return_value = {
        "intent": "spending_query",
        "entities": {"category": "food", "amount": 1000},
        "confidence": 0.9,
        "response_type": "data_query"
    }
    return processor

@pytest.fixture
def mock_spending_forecaster():
    """Mock spending forecaster"""
    forecaster = Mock()
    forecaster.predict_spending.return_value = {
        "next_month_prediction": 25000.0,
        "confidence_interval": [20000.0, 30000.0],
        "trend": "increasing"
    }
    return forecaster

@pytest.fixture
def mock_budget_optimizer():
    """Mock budget optimizer"""
    optimizer = Mock()
    optimizer.optimize_budget.return_value = {
        "recommendations": [
            {"category": "food", "suggested_amount": 8000, "reason": "Reduce dining out"},
            {"category": "transport", "suggested_amount": 5000, "reason": "Use public transport"}
        ],
        "total_savings": 3000.0
    }
    return optimizer

# Environment setup for tests
@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables"""
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]