from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, validator
import logging

from ..database import get_db
from ..models.user import User
from ..models.transaction import FinanceTransaction
from ..services.upi_service import mock_razorpay_upi, PaymentStatus, UPIProvider
from ..utils.auth_utils import get_current_user
from ..ai_modules.categorizer import TransactionCategorizer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/upi", tags=["UPI Integration"])

# Initialize categorizer
categorizer = TransactionCategorizer()

class UPIPaymentRequest(BaseModel):
    amount: float
    vpa: str
    description: Optional[str] = "UPI Payment"
    merchant_name: Optional[str] = "FinanceAI"
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        if v > 200000:  # UPI limit
            raise ValueError('Amount exceeds UPI transaction limit')
        return v
    
    @validator('vpa')
    def validate_vpa(cls, v):
        if not v or '@' not in v:
            raise ValueError('Invalid VPA format')
        return v.lower()

class PaymentLinkRequest(BaseModel):
    amount: float
    description: Optional[str] = "Payment for services"
    customer_vpa: Optional[str] = None
    callback_url: Optional[str] = None
    
    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class RefundRequest(BaseModel):
    payment_id: str
    amount: Optional[float] = None
    reason: Optional[str] = "Customer request"

@router.get("/payment-methods")
async def get_payment_methods(
    amount: float,
    current_user: User = Depends(get_current_user)
):
    """
    Get available UPI payment methods and limits
    """
    try:
        methods = await mock_razorpay_upi.get_payment_methods(amount)
        return {
            "success": True,
            "data": methods
        }
    except Exception as e:
        logger.error(f"Error fetching payment methods: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment methods"
        )

@router.post("/create-payment")
async def create_upi_payment(
    payment_request: UPIPaymentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new UPI payment request
    """
    try:
        payment_data = {
            "amount": payment_request.amount,
            "vpa": payment_request.vpa,
            "description": payment_request.description,
            "merchant_name": payment_request.merchant_name,
            "currency": "INR"
        }
        
        # Initiate payment with mock Razorpay
        payment_response = await mock_razorpay_upi.initiate_upi_payment(payment_data)
        
        if "error" in payment_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=payment_response["error"]["description"]
            )
        
        # Create transaction record in database
        transaction = FinanceTransaction(
            user_id=current_user.id,
            transaction_id=payment_response["id"],
            amount=payment_request.amount,
            transaction_type="debit",
            description=payment_request.description,
            merchant_name=payment_request.merchant_name,
            payment_method="upi",
            payment_provider=payment_response.get("provider", "unknown"),
            vpa=payment_request.vpa,
            status="pending"
        )
        
        # Categorize transaction
        category, confidence = categorizer.categorize_transaction(
            payment_request.description,
            payment_request.merchant_name,
            payment_request.amount
        )
        transaction.ai_category = category
        transaction.confidence_score = confidence
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        return {
            "success": True,
            "data": {
                "payment_id": payment_response["id"],
                "transaction_id": transaction.id,
                "amount": payment_request.amount,
                "vpa": payment_request.vpa,
                "status": payment_response["status"],
                "provider": payment_response.get("provider"),
                "created_at": payment_response["created_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating UPI payment: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment"
        )

@router.post("/create-payment-link")
async def create_payment_link(
    link_request: PaymentLinkRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Create a UPI payment link for sharing
    """
    try:
        order_data = {
            "amount": link_request.amount,
            "currency": "INR",
            "description": link_request.description,
            "customer": {
                "vpa": link_request.customer_vpa
            },
            "callback_url": link_request.callback_url
        }
        
        payment_link = await mock_razorpay_upi.create_payment_link(order_data)
        
        return {
            "success": True,
            "data": payment_link
        }
        
    except Exception as e:
        logger.error(f"Error creating payment link: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create payment link"
        )

@router.get("/payment-status/{payment_id}")
async def get_payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of a specific payment
    """
    try:
        # Get status from mock Razorpay
        payment_response = await mock_razorpay_upi.get_payment_status(payment_id)
        
        if "error" in payment_response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )
        
        # Update local transaction record if needed
        transaction = db.query(FinanceTransaction).filter(
            FinanceTransaction.transaction_id == payment_id,
            FinanceTransaction.user_id == current_user.id
        ).first()
        
        if transaction:
            # Update status based on payment response
            if payment_response["status"] == "captured":
                transaction.status = "completed"
            elif payment_response["status"] == "failed":
                transaction.status = "failed"
                transaction.failure_reason = payment_response.get("error_description")
            
            db.commit()
        
        return {
            "success": True,
            "data": payment_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching payment status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch payment status"
        )

@router.get("/transaction-history")
async def get_upi_transaction_history(
    limit: int = 10,
    skip: int = 0,
    current_user: User = Depends(get_current_user)
):
    """
    Get UPI transaction history
    """
    try:
        transactions = await mock_razorpay_upi.get_transaction_history(limit, skip)
        
        return {
            "success": True,
            "data": {
                "transactions": transactions,
                "total": len(transactions),
                "limit": limit,
                "skip": skip
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching transaction history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction history"
        )

@router.post("/refund")
async def refund_payment(
    refund_request: RefundRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate payment refund
    """
    try:
        # Check if user owns this transaction
        transaction = db.query(FinanceTransaction).filter(
            FinanceTransaction.transaction_id == refund_request.payment_id,
            FinanceTransaction.user_id == current_user.id
        ).first()
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        if transaction.status != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Can only refund completed transactions"
            )
        
        # Process refund
        refund_response = await mock_razorpay_upi.refund_payment(
            refund_request.payment_id,
            refund_request.amount
        )
        
        if "error" in refund_response:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=refund_response["error"]["description"]
            )
        
        # Create refund transaction record
        refund_amount = refund_request.amount or transaction.amount
        refund_transaction = FinanceTransaction(
            user_id=current_user.id,
            transaction_id=refund_response["id"],
            amount=refund_amount,
            transaction_type="credit",
            description=f"Refund for {transaction.description}",
            merchant_name=transaction.merchant_name,
            payment_method="upi_refund",
            payment_provider=transaction.payment_provider,
            ai_category="refund",
            status="completed",
            parent_transaction_id=transaction.id
        )
        
        db.add(refund_transaction)
        db.commit()
        
        return {
            "success": True,
            "data": {
                "refund_id": refund_response["id"],
                "amount": refund_amount,
                "status": refund_response["status"],
                "transaction_id": refund_transaction.id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing refund: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process refund"
        )

@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle UPI webhook notifications from Razorpay
    This endpoint would be registered with Razorpay to receive payment updates
    """
    try:
        payload = await request.body()
        signature = request.headers.get("X-Razorpay-Signature", "")
        
        # Verify webhook signature (in production)
        # is_valid = mock_razorpay_upi.verify_webhook_signature(
        #     payload.decode(), signature
        # )
        # if not is_valid:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="Invalid webhook signature"
        #     )
        
        webhook_data = await request.json()
        
        if webhook_data.get("event", "").startswith("payment."):
            payment_data = webhook_data["payload"]["payment"]["entity"]
            payment_id = payment_data["id"]
            payment_status = payment_data["status"]
            
            # Update transaction status in database
            transaction = db.query(FinanceTransaction).filter(
                FinanceTransaction.transaction_id == payment_id
            ).first()
            
            if transaction:
                if payment_status == "captured":
                    transaction.status = "completed"
                elif payment_status == "failed":
                    transaction.status = "failed"
                    transaction.failure_reason = payment_data.get("error_description")
                
                db.commit()
                
                logger.info(f"Updated transaction {payment_id} status to {payment_status}")
        
        return {"success": True, "message": "Webhook processed"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {"success": False, "error": str(e)}

@router.get("/providers")
async def get_upi_providers():
    """
    Get list of supported UPI providers
    """
    providers = [
        {
            "id": provider.value,
            "name": provider.value.title(),
            "logo": f"/static/logos/{provider.value}.png",
            "supported": True
        }
        for provider in UPIProvider
    ]
    
    return {
        "success": True,
        "data": {
            "providers": providers,
            "total": len(providers)
        }
    }

@router.get("/mock-accounts")
async def get_mock_accounts(
    current_user: User = Depends(get_current_user)
):
    """
    Get mock UPI accounts for testing (development only)
    """
    accounts = [
        {
            "vpa": account.vpa,
            "provider": account.provider.value,
            "account_holder_name": account.account_holder_name,
            "balance": account.balance,
            "is_verified": account.is_verified
        }
        for account in mock_razorpay_upi.accounts.values()
    ]
    
    return {
        "success": True,
        "data": {
            "accounts": accounts,
            "note": "These are mock accounts for testing purposes only"
        }
    }