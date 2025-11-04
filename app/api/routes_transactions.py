# app/api/routes_transactions.py
from fastapi import APIRouter, Header
from datetime import date
from app.services.transactions_service import create_transaction, get_user_transactions
from app.services.auth_service import verify_access_token

router = APIRouter()

@router.post("/transactions", tags=["Transactions"])
def create_tx(listing_id: int, start_date: date, end_date: date, authorization: str = Header(None)):
    """Record a rental transaction"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    renter_id = verify_access_token(token)
    if not renter_id:
        return {"error": "Invalid token"}
    return create_transaction(renter_id, listing_id, start_date, end_date)

@router.get("/my_transactions", tags=["Transactions"])
def user_transactions(authorization: str = Header(None)):
    """Fetch user's transactions"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return {"transactions": get_user_transactions(user_id)}
