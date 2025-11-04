# app/api/routes_delivery.py
from fastapi import APIRouter, Header
from app.services.delivery_service import (
    create_self_delivery_task,
    verify_pickup_otp,
    verify_drop_otp,
    get_tasks_for_user,
    get_task_by_booking,
    supabase,
    update_live_location,
    get_active_deliveries_nearby,
)
from app.services.auth_service import verify_access_token
from datetime import datetime

router = APIRouter()

def _require_user_id(authorization: str = None):
    if not authorization:
        return None
    return verify_access_token(authorization.replace("Bearer ", ""))

@router.post("/delivery/self", tags=["Delivery"])
def schedule_self_delivery(booking_id: int, owner_id: str, renter_id: str):
    """Create a self-managed pickup/drop delivery task"""
    return create_self_delivery_task(booking_id, owner_id, renter_id)

@router.post("/delivery/pickup/verify", tags=["Delivery"])
def pickup_verify(booking_id: int, otp: str):
    """Verify pickup OTP"""
    return verify_pickup_otp(booking_id, otp)

@router.post("/delivery/drop/verify", tags=["Delivery"])
def drop_verify(booking_id: int, otp: str):
    """Verify drop OTP and auto-credit rent"""
    return verify_drop_otp(booking_id, otp)

@router.get("/delivery/tasks", tags=["Delivery"])
def user_tasks(authorization: str = Header(None)):
    """Fetch all delivery tasks for current user"""
    if not authorization:
        return {"error": "Missing token"}
    user_id = verify_access_token(authorization.replace("Bearer ", ""))
    if not user_id:
        return {"error": "Invalid token"}
    return {"tasks": get_tasks_for_user(user_id)}


@router.post("/delivery/verify_pickup", tags=["Delivery"])
def verify_pickup(booking_id: int, otp: str, authorization: str = Header(None)):
    """Verify pickup OTP with expiry check. Does not expose OTP values."""
    # Optional: verify token if needed
    task = get_task_by_booking(booking_id)
    if not task:
        return {"error": "Task not found"}
    if task.get("otp_expires_at") and datetime.fromisoformat(task["otp_expires_at"]) < datetime.utcnow():
        return {"error": "OTP expired"}
    if task.get("pickup_otp") != otp:
        return {"error": "Invalid OTP"}
    supabase.table("delivery_tasks").update({
        "pickup_verified": True,
        "status": "picked",
        "last_status_update": datetime.utcnow().isoformat(),
    }).eq("booking_id", booking_id).execute()
    return {"success": True}


@router.post("/delivery/verify_drop", tags=["Delivery"])
def verify_drop(booking_id: int, otp: str, authorization: str = Header(None)):
    """Verify drop OTP with expiry check. Does not expose OTP values."""
    task = get_task_by_booking(booking_id)
    if not task:
        return {"error": "Task not found"}
    if task.get("otp_expires_at") and datetime.fromisoformat(task["otp_expires_at"]) < datetime.utcnow():
        return {"error": "OTP expired"}
    if task.get("drop_otp") != otp:
        return {"error": "Invalid OTP"}
    supabase.table("delivery_tasks").update({
        "drop_verified": True,
        "status": "completed",
        "last_status_update": datetime.utcnow().isoformat(),
    }).eq("booking_id", booking_id).execute()
    return {"success": True}


@router.post("/delivery/update-location", tags=["Delivery"])
def update_location(task_id: int, lat: float, lng: float, authorization: str = Header(None)):
    user_id = _require_user_id(authorization)
    if not user_id:
        return {"error": "Invalid token"}
    return update_live_location(task_id, lat, lng, user_id)


@router.get("/delivery/nearby", tags=["Delivery"])
def nearby_deliveries(lat: float, lng: float, radius_km: float = 5.0):
    """Public endpoint for admin or map previews."""
    return {"deliveries": get_active_deliveries_nearby(lat, lng, radius_km)}

# app/api/routes_delivery.py
from fastapi import APIRouter, Header
from app.services.delivery_service import (
    update_live_location,
    get_active_deliveries_nearby,
)
from app.services.auth_service import verify_access_token

router = APIRouter()


@router.post("/delivery/update_location", tags=["Delivery"])
def update_location(task_id: int, lat: float, lng: float, authorization: str = Header(None)):
    """Update the user's live delivery location."""
    if not authorization:
        return {"error": "Missing access token"}
    user_id = verify_access_token(authorization.replace("Bearer ", ""))
    if not user_id:
        return {"error": "Invalid or expired token"}

    return update_live_location(task_id, lat, lng, user_id)


@router.get("/delivery/nearby", tags=["Delivery"])
def get_nearby(lat: float, lng: float, radius_km: float = 5.0):
    """Fetch nearby deliveries (for admin map or renter discovery)."""
    return {"nearby": get_active_deliveries_nearby(lat, lng, radius_km)}
