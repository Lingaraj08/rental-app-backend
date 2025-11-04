# app/api/routes_payments.py
from fastapi import APIRouter, Header
from app.services.auth_service import verify_access_token
from app.services.payments_service import create_payment_order, verify_payment_signature

router = APIRouter()

@router.post("/payments/create_order", tags=["Payments"])
def create_order(amount: float, purpose: str, authorization: str = Header(None)):
    """Create a Razorpay order for adding money to wallet."""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}

    return create_payment_order(user_id, amount, purpose)


@router.post("/payments/verify", tags=["Payments"])
def verify_payment(order_id: str, payment_id: str, signature: str):
    """Verify Razorpay payment signature and credit wallet."""
    return verify_payment_signature(order_id, payment_id, signature)
