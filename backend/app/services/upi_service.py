import asyncio
import json
import hashlib
import hmac
import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class PaymentStatus(Enum):
    CREATED = "created"
    PENDING = "pending"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"

class UPIProvider(Enum):
    PAYTM = "paytm"
    PHONEPE = "phonepe"
    GOOGLEPAY = "googlepay"
    AMAZONPAY = "amazonpay"
    BHIM = "bhim"

@dataclass
class UPITransaction:
    transaction_id: str
    razorpay_payment_id: str
    amount: float
    currency: str
    status: PaymentStatus
    method: str
    upi_provider: UPIProvider
    vpa: str  # Virtual Payment Address
    merchant_name: str
    description: str
    created_at: datetime
    captured_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    error_code: Optional[str] = None
    error_description: Optional[str] = None
    fees: float = 0.0
    tax: float = 0.0
    settlement_amount: float = 0.0

@dataclass
class UPIAccount:
    account_id: str
    vpa: str
    provider: UPIProvider
    account_holder_name: str
    phone_number: str
    is_verified: bool = True
    balance: float = 50000.0  # Mock balance
    daily_limit: float = 100000.0
    transaction_limit: float = 5000.0

class MockRazorpayUPI:
    """
    Mock implementation of Razorpay UPI integration for demonstration purposes.
    Simulates real UPI payment flows with realistic delays and responses.
    """
    
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api.razorpay.com/v1"
        self.webhook_secret = "webhook_secret_key"
        
        # Mock data
        self.transactions: Dict[str, UPITransaction] = {}
        self.accounts: Dict[str, UPIAccount] = {}
        self._initialize_mock_accounts()
    
    def _initialize_mock_accounts(self):
        """Initialize mock UPI accounts for simulation"""
        mock_accounts = [
            UPIAccount(
                account_id="acc_001",
                vpa="user@paytm",
                provider=UPIProvider.PAYTM,
                account_holder_name="John Doe",
                phone_number="9876543210",
                balance=25000.0
            ),
            UPIAccount(
                account_id="acc_002", 
                vpa="customer@phonepe",
                provider=UPIProvider.PHONEPE,
                account_holder_name="Jane Smith",
                phone_number="8765432109",
                balance=15000.0
            ),
            UPIAccount(
                account_id="acc_003",
                vpa="buyer@gpay",
                provider=UPIProvider.GOOGLEPAY,
                account_holder_name="Mike Johnson",
                phone_number="7654321098",
                balance=35000.0
            )
        ]
        
        for account in mock_accounts:
            self.accounts[account.vpa] = account
    
    def _generate_payment_id(self) -> str:
        """Generate mock Razorpay payment ID"""
        return f"pay_{int(time.time())}_{random.randint(1000, 9999)}"
    
    def _generate_transaction_id(self) -> str:
        """Generate mock transaction ID"""
        return f"txn_{int(time.time())}_{random.randint(10000, 99999)}"
    
    def _calculate_fees(self, amount: float) -> tuple[float, float]:
        """Calculate mock fees and tax"""
        # Razorpay UPI fees: 2% or ₹2, whichever is higher
        fees = max(amount * 0.02, 2.0)
        tax = fees * 0.18  # 18% GST
        return fees, tax
    
    def _create_signature(self, data: str) -> str:
        """Create webhook signature for verification"""
        return hmac.new(
            self.webhook_secret.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()
    
    async def create_payment_link(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create UPI payment link
        """
        payment_id = self._generate_payment_id()
        transaction_id = self._generate_transaction_id()
        
        # Simulate some processing delay
        await asyncio.sleep(0.5)
        
        payment_link = {
            "id": payment_id,
            "entity": "payment_link",
            "status": "created",
            "amount": order_data["amount"],
            "amount_paid": 0,
            "currency": order_data.get("currency", "INR"),
            "description": order_data.get("description", "UPI Payment"),
            "short_url": f"https://rzp.io/l/{payment_id}",
            "created_at": int(time.time()),
            "upi": {
                "flow": "collect",
                "vpa": order_data.get("customer", {}).get("vpa"),
                "expiry_time": int(time.time()) + 300  # 5 minutes
            },
            "customer": order_data.get("customer", {}),
            "callback_url": order_data.get("callback_url"),
            "callback_method": "get"
        }
        
        return payment_link
    
    async def initiate_upi_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initiate UPI payment collection
        """
        payment_id = self._generate_payment_id()
        transaction_id = self._generate_transaction_id()
        
        amount = payment_data["amount"]
        vpa = payment_data["vpa"]
        
        # Check if VPA exists in our mock accounts
        if vpa not in self.accounts:
            return {
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "Invalid VPA",
                    "field": "vpa"
                }
            }
        
        account = self.accounts[vpa]
        fees, tax = self._calculate_fees(amount)
        
        # Create transaction record
        transaction = UPITransaction(
            transaction_id=transaction_id,
            razorpay_payment_id=payment_id,
            amount=amount,
            currency=payment_data.get("currency", "INR"),
            status=PaymentStatus.CREATED,
            method="upi",
            upi_provider=account.provider,
            vpa=vpa,
            merchant_name=payment_data.get("merchant_name", "FinanceAI"),
            description=payment_data.get("description", "UPI Payment"),
            created_at=datetime.now(),
            fees=fees,
            tax=tax,
            settlement_amount=amount - fees - tax
        )
        
        self.transactions[payment_id] = transaction
        
        # Simulate payment processing
        asyncio.create_task(self._process_payment(payment_id))
        
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": amount,
            "currency": "INR",
            "status": "created",
            "method": "upi",
            "created_at": int(time.time()),
            "vpa": vpa,
            "provider": account.provider.value,
            "description": transaction.description
        }
    
    async def _process_payment(self, payment_id: str):
        """
        Simulate payment processing with realistic delays and outcomes
        """
        transaction = self.transactions[payment_id]
        account = self.accounts[transaction.vpa]
        
        # Simulate processing delay (2-10 seconds)
        processing_delay = random.uniform(2, 10)
        await asyncio.sleep(processing_delay)
        
        # Update status to pending
        transaction.status = PaymentStatus.PENDING
        
        # Simulate payment success/failure based on account balance and limits
        success_probability = 0.85  # 85% success rate
        
        if transaction.amount > account.balance:
            # Insufficient balance
            transaction.status = PaymentStatus.FAILED
            transaction.failed_at = datetime.now()
            transaction.error_code = "INSUFFICIENT_BALANCE"
            transaction.error_description = "Insufficient balance in the account"
        elif transaction.amount > account.transaction_limit:
            # Transaction limit exceeded
            transaction.status = PaymentStatus.FAILED
            transaction.failed_at = datetime.now()
            transaction.error_code = "TRANSACTION_LIMIT_EXCEEDED"
            transaction.error_description = "Transaction amount exceeds daily limit"
        elif random.random() > success_probability:
            # Random failure
            error_codes = [
                ("PAYMENT_DECLINED", "Payment declined by bank"),
                ("UPI_TIMEOUT", "UPI payment timed out"),
                ("INVALID_VPA", "VPA is invalid or not found"),
                ("PAYMENT_CANCELLED", "Payment cancelled by user")
            ]
            error_code, error_desc = random.choice(error_codes)
            transaction.status = PaymentStatus.FAILED
            transaction.failed_at = datetime.now()
            transaction.error_code = error_code
            transaction.error_description = error_desc
        else:
            # Successful payment
            transaction.status = PaymentStatus.CAPTURED
            transaction.captured_at = datetime.now()
            account.balance -= transaction.amount
        
        # Simulate webhook notification
        await self._send_webhook_notification(payment_id)
    
    async def _send_webhook_notification(self, payment_id: str):
        """
        Simulate webhook notification (in real implementation, this would be sent to client)
        """
        transaction = self.transactions[payment_id]
        
        webhook_payload = {
            "entity": "event",
            "account_id": "acc_test123",
            "event": f"payment.{transaction.status.value}",
            "contains": ["payment"],
            "payload": {
                "payment": {
                    "entity": {
                        "id": payment_id,
                        "entity": "payment",
                        "amount": transaction.amount,
                        "currency": transaction.currency,
                        "status": transaction.status.value,
                        "method": "upi",
                        "vpa": transaction.vpa,
                        "created_at": int(transaction.created_at.timestamp()),
                        "captured_at": int(transaction.captured_at.timestamp()) if transaction.captured_at else None,
                        "error_code": transaction.error_code,
                        "error_description": transaction.error_description
                    }
                }
            },
            "created_at": int(time.time())
        }
        
        # In real implementation, send POST request to configured webhook URL
        print(f"Webhook notification: {json.dumps(webhook_payload, indent=2)}")
    
    async def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """
        Get payment status by payment ID
        """
        if payment_id not in self.transactions:
            return {
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "Payment not found"
                }
            }
        
        transaction = self.transactions[payment_id]
        
        return {
            "id": payment_id,
            "entity": "payment",
            "amount": transaction.amount,
            "currency": transaction.currency,
            "status": transaction.status.value,
            "method": "upi",
            "vpa": transaction.vpa,
            "provider": transaction.upi_provider.value,
            "description": transaction.description,
            "created_at": int(transaction.created_at.timestamp()),
            "captured_at": int(transaction.captured_at.timestamp()) if transaction.captured_at else None,
            "failed_at": int(transaction.failed_at.timestamp()) if transaction.failed_at else None,
            "error_code": transaction.error_code,
            "error_description": transaction.error_description,
            "fees": transaction.fees,
            "tax": transaction.tax,
            "settlement_amount": transaction.settlement_amount
        }
    
    async def get_payment_methods(self, amount: float) -> Dict[str, Any]:
        """
        Get available payment methods for UPI
        """
        return {
            "methods": {
                "upi": True,
                "card": False,
                "netbanking": False,
                "wallet": False
            },
            "upi": {
                "providers": [provider.value for provider in UPIProvider],
                "min_amount": 100,  # ₹1
                "max_amount": 200000  # ₹2,00,000
            },
            "amount": amount,
            "currency": "INR"
        }
    
    async def get_transaction_history(self, limit: int = 10, skip: int = 0) -> List[Dict[str, Any]]:
        """
        Get transaction history for the merchant
        """
        transactions = list(self.transactions.values())
        transactions.sort(key=lambda x: x.created_at, reverse=True)
        
        paginated_transactions = transactions[skip:skip + limit]
        
        return [
            {
                "id": txn.razorpay_payment_id,
                "amount": txn.amount,
                "currency": txn.currency,
                "status": txn.status.value,
                "method": "upi",
                "vpa": txn.vpa,
                "provider": txn.upi_provider.value,
                "description": txn.description,
                "created_at": int(txn.created_at.timestamp()),
                "captured_at": int(txn.captured_at.timestamp()) if txn.captured_at else None
            }
            for txn in paginated_transactions
        ]
    
    async def refund_payment(self, payment_id: str, amount: Optional[float] = None) -> Dict[str, Any]:
        """
        Simulate payment refund
        """
        if payment_id not in self.transactions:
            return {
                "error": {
                    "code": "BAD_REQUEST_ERROR", 
                    "description": "Payment not found"
                }
            }
        
        transaction = self.transactions[payment_id]
        
        if transaction.status != PaymentStatus.CAPTURED:
            return {
                "error": {
                    "code": "BAD_REQUEST_ERROR",
                    "description": "Payment not captured, cannot refund"
                }
            }
        
        refund_amount = amount or transaction.amount
        refund_id = f"rfnd_{int(time.time())}_{random.randint(1000, 9999)}"
        
        # Simulate refund processing delay
        await asyncio.sleep(1)
        
        # Add refund amount back to account
        account = self.accounts[transaction.vpa]
        account.balance += refund_amount
        
        return {
            "id": refund_id,
            "entity": "refund",
            "amount": refund_amount,
            "currency": transaction.currency,
            "payment_id": payment_id,
            "status": "processed",
            "speed_processed": "normal",
            "created_at": int(time.time())
        }
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verify webhook signature for security
        """
        expected_signature = self._create_signature(payload)
        return hmac.compare_digest(expected_signature, signature)

# Global instance for use across the application
mock_razorpay_upi = MockRazorpayUPI(
    api_key="rzp_test_mock_key",
    api_secret="mock_secret_key"
)