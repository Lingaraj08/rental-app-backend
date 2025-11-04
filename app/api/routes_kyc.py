# app/api/routes_kyc.py

from fastapi import APIRouter, Header
from app.services.kyc_service import submit_kyc, review_kyc
from app.services.auth_service import verify_access_token

router = APIRouter()

@router.post("/kyc/submit", tags=["KYC"])
def submit_user_kyc(govt_id_url: str, selfie_url: str, authorization: str = Header(None)):
    """User submits their KYC with ID and selfie"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return submit_kyc(user_id, govt_id_url, selfie_url)


@router.post("/kyc/review", tags=["Admin"])
def admin_review_kyc(user_id: str, approve: bool, reason: str = None, authorization: str = Header(None)):
    """Admin manually approves/rejects pending KYC"""
    if not authorization:
        return {"error": "Missing admin token"}
    token = authorization.replace("Bearer ", "")
    admin_id = verify_access_token(token)
    if not admin_id:
        return {"error": "Invalid admin token"}
    return review_kyc(user_id, admin_id, approve, reason)
