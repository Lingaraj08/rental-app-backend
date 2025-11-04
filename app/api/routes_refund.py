# app/api/routes_refunds.py
from fastapi import APIRouter, Header
from app.services.auth_service import verify_access_token
from app.services.refund_service import process_refund

router = APIRouter()

@router.post("/refunds", tags=["Refunds"])
def refund_payment(provider_payment_id: str, amount: float, reason: str, authorization: str = Header(None)):
    """Initiate refund through Razorpay for a completed payment."""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}

    return process_refund(provider_payment_id, user_id, amount, reason)
