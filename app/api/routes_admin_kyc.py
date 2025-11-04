from fastapi import APIRouter, Header
from app.services.auth_service import verify_access_token
from app.services.supabase_service import supabase

router = APIRouter()

@router.get("/admin/kyc/pending", tags=["Admin"])
def list_pending_kyc(authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    admin_id = verify_access_token(token)
    admin = supabase.table("users").select("is_admin").eq("id", admin_id).execute().data
    if not admin or not admin[0]["is_admin"]:
        return {"error": "Unauthorized"}

    res = supabase.table("users").select("id, name, email, kyc_id_doc, kyc_selfie, kyc_verified").eq("kyc_verified", False).execute()
    return {"pending_kyc": res.data}


@router.post("/admin/kyc/approve/{user_id}", tags=["Admin"])
def approve_kyc(user_id: str, authorization: str = Header(None)):
    token = authorization.replace("Bearer ", "")
    admin_id = verify_access_token(token)
    admin = supabase.table("users").select("is_admin").eq("id", admin_id).execute().data
    if not admin or not admin[0]["is_admin"]:
        return {"error": "Unauthorized"}

    supabase.table("users").update({"kyc_verified": True}).eq("id", user_id).execute()
    return {"success": True, "message": f"KYC approved for user {user_id}"}
