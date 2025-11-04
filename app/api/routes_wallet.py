# app/api/routes_wallet.py
from fastapi import APIRouter, Header
from app.services.wallet_service import get_wallet_balance, get_wallet_transactions
from app.services.auth_service import verify_access_token

router = APIRouter()

@router.get("/wallet", tags=["Wallet"])
def view_balance(authorization: str = Header(None)):
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return get_wallet_balance(user_id)

@router.get("/wallet/transactions", tags=["Wallet"])
def wallet_history(authorization: str = Header(None)):
    """View wallet transaction history"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return {"transactions": get_wallet_transactions(user_id)}
