from fastapi import APIRouter, Header, HTTPException
from app.services.auth_service import verify_access_token
import app.services.admin_service as admin_service
from app.services.supabase_service import supabase

router = APIRouter()

def require_admin(authorization: str):
    """Verify JWT and ensure the user is admin."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = supabase.table("users").select("is_admin").eq("id", user_id).execute().data
    if not user or not user[0]["is_admin"]:
        raise HTTPException(status_code=403, detail="Admin access required")

    return user_id

# ------------------- EXISTING ADMIN ROUTES -------------------

@router.get("/admin/users", tags=["Admin"])
def all_users():
    return {"users": admin_service.get_all_users()}

@router.delete("/admin/users/{user_id}", tags=["Admin"])
def remove_user(user_id: str):
    return admin_service.delete_user(user_id)

@router.get("/admin/listings", tags=["Admin"])
def all_listings():
    return {"listings": admin_service.get_all_listings()}

@router.delete("/admin/listings/{listing_id}", tags=["Admin"])
def remove_listing(listing_id: int):
    return admin_service.delete_listing(listing_id)

@router.get("/admin/reports", tags=["Admin"])
def all_reports():
    return {"reports": admin_service.get_reports()}

@router.patch("/admin/reports/{report_id}", tags=["Admin"])
def change_status(report_id: int, status: str):
    return admin_service.update_report_status(report_id, status)

@router.get("/admin/stats", tags=["Admin"])
def platform_summary():
    return admin_service.get_platform_stats()

@router.post("/kyc/review", tags=["Admin"])
def review_kyc(user_id: str, approve: bool, reason: str = None, authorization: str = Header(None)):
    admin_id = require_admin(authorization)
    return admin_service.review_kyc(user_id, admin_id, approve, reason)

# ------------------- NEW ADMIN ROUTES -------------------

@router.get("/admin/delivery/view-all", tags=["Admin"])
def admin_view_all_tasks(authorization: str = Header(None)):
    require_admin(authorization)
    return admin_service.get_all_delivery_tasks()

@router.post("/admin/delivery/override", tags=["Admin"])
def admin_override_verification(task_id: int, verification_type: str, authorization: str = Header(None)):
    admin_id = require_admin(authorization)
    return admin_service.override_verification(task_id, admin_id, verification_type)

@router.post("/admin/delivery/regenerate-otp", tags=["Admin"])
def admin_regenerate_otp(task_id: int, authorization: str = Header(None)):
    admin_id = require_admin(authorization)
    return admin_service.regenerate_otp(task_id, admin_id)

@router.get("/admin/actions/logs", tags=["Admin"])
def admin_view_logs(authorization: str = Header(None)):
    require_admin(authorization)
    return {"actions": admin_service.get_admin_actions()}

@router.get("/admin/notifications", tags=["Admin"])
def admin_notifications(authorization: str = Header(None)):
    admin_id = require_admin(authorization)
    res = supabase.table("notifications").select("*").eq("user_id", admin_id).order("created_at", desc=True).execute()
    return {"notifications": res.data}
