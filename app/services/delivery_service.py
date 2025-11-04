# app/services/delivery_service.py
from datetime import datetime, timedelta
import random, string

from app.services.supabase_service import supabase

OTP_TTL_MINUTES = 30

def _gen_otp(n: int = 6) -> str:
    return ''.join(random.choices(string.digits, k=n))

def _utcnow_iso() -> str:
    return datetime.utcnow().isoformat()

def _get_booking(booking_id: int):
    res = supabase.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    return res.data[0] if res.data else None

def _get_task_by_booking(booking_id: int):
    res = supabase.table("delivery_tasks").select("*").eq("booking_id", booking_id).limit(1).execute()
    return res.data[0] if res.data else None

def get_tasks_for_user(user_id: str):
    """All delivery tasks where user participates (owner or renter)."""
    res = supabase.table("delivery_tasks").select("*")\
        .or_(f"owner_id.eq.{user_id},renter_id.eq.{user_id}")\
        .order("created_at", desc=True).execute()
    return res.data

def create_self_delivery_task(booking_id: int, actor_user_id: str):
    """
    Create a self-managed delivery task for a booking.
    Preconditions:
      - booking must exist and be approved (or at least not rejected)
      - actor must be either owner or renter of the booking
    """
    booking = _get_booking(booking_id)
    if not booking:
        return {"error": "Booking not found"}
    if booking.get("status") not in ("approved", "requested", "completed"):  # relax if you want only approved
        return {"error": f"Booking status not eligible: {booking.get('status')}"}

    owner_id = booking.get("owner_id")
    renter_id = booking.get("renter_id")
    if actor_user_id not in (owner_id, renter_id):
        return {"error": "Not authorized to create delivery task for this booking"}

    existing = _get_task_by_booking(booking_id)
    if existing:
        return {"task": existing, "warning": "Task already exists"}

    pickup_otp = _gen_otp()
    drop_otp = _gen_otp()
    expires_at = (datetime.utcnow() + timedelta(minutes=OTP_TTL_MINUTES)).isoformat()

    row = {
        "booking_id": booking_id,
        "owner_id": owner_id,
        "renter_id": renter_id,
        "pickup_otp": pickup_otp,
        "drop_otp": drop_otp,
        "otp_expires_at": expires_at,
        "pickup_verified": False,
        "drop_verified": False,
        "mode": "self",
        "status": "pending",
        "created_at": _utcnow_iso(),
        "last_status_update": _utcnow_iso(),
    }
    ins = supabase.table("delivery_tasks").insert(row).execute()
    # DO NOT return OTPs to client; they should be sent via secure channel (later SMS/email).
    safe = ins.data[0] if ins.data else None
    if safe and "pickup_otp" in safe:   safe["pickup_otp"] = "SET"
    if safe and "drop_otp" in safe:     safe["drop_otp"] = "SET"
    return {"task": safe}

def verify_pickup_otp(booking_id: int, otp: str, actor_user_id: str):
    task = _get_task_by_booking(booking_id)
    if not task:
        return {"error": "Task not found"}
    if actor_user_id not in (task.get("owner_id"), task.get("renter_id")):
        return {"error": "Not authorized"}
    # expiry check
    exp = task.get("otp_expires_at")
    if exp and datetime.fromisoformat(exp) < datetime.utcnow():
        return {"error": "OTP expired"}
    if task.get("pickup_verified"):
        return {"error": "Pickup already verified"}
    if otp != task.get("pickup_otp"):
        return {"error": "Invalid OTP"}

    upd = supabase.table("delivery_tasks").update({
        "pickup_verified": True,
        "status": "picked",
        "pickup_otp": None,  # burn the OTP
        "last_status_update": _utcnow_iso(),
    }).eq("booking_id", booking_id).execute()
    return {"success": True, "task": upd.data[0] if upd.data else None}

def verify_drop_otp(booking_id: int, otp: str, actor_user_id: str):
    task = _get_task_by_booking(booking_id)
    if not task:
        return {"error": "Task not found"}
    if actor_user_id not in (task.get("owner_id"), task.get("renter_id")):
        return {"error": "Not authorized"}
    exp = task.get("otp_expires_at")
    if exp and datetime.fromisoformat(exp) < datetime.utcnow():
        return {"error": "OTP expired"}
    if not task.get("pickup_verified"):
        return {"error": "Pickup not verified yet"}
    if task.get("drop_verified"):
        return {"error": "Drop already verified"}
    if otp != task.get("drop_otp"):
        return {"error": "Invalid OTP"}

    upd = supabase.table("delivery_tasks").update({
        "drop_verified": True,
        "status": "completed",
        "drop_otp": None,  # burn the OTP
        "last_status_update": _utcnow_iso(),
    }).eq("booking_id", booking_id).execute()
    return {"success": True, "task": upd.data[0] if upd.data else None}


# --- Geo helpers ---

def update_live_location(task_id: int, lat: float, lng: float, actor_user_id: str):
    """Update live location for a delivery task (either owner or renter)"""
    try:
        task = supabase.table("delivery_tasks").select("*").eq("id", task_id).execute()
        if not task.data:
            return {"error": "Task not found"}

        task = task.data[0]
        if actor_user_id not in (task.get("owner_id"), task.get("renter_id")):
            return {"error": "Not authorized"}

        res = supabase.table("delivery_tasks").update({
            "current_lat": lat,
            "current_lng": lng,
            "last_update": datetime.utcnow().isoformat(),
        }).eq("id", task_id).execute()

        return {"success": True, "updated": res.data[0] if res.data else None}
    except Exception as e:
        return {"error": str(e)}


def get_task_by_booking(booking_id: int):
    """Public wrapper to fetch a single delivery task by booking id."""
    try:
        return _get_task_by_booking(booking_id)
    except Exception:
        return None


def get_active_deliveries_nearby(lat: float, lng: float, radius_km: float = 5.0):
    """
    Fetch deliveries within given radius (approx using simple haversine filter).
    For admin/map views or for showing nearby deliveries.
    """
    try:
        res = supabase.table("delivery_tasks").select("*").execute()
        if not res.data:
            return []

        from math import radians, sin, cos, sqrt, atan2
        nearby = []
        for row in res.data:
            if not row.get("current_lat") or not row.get("current_lng"):
                continue
            # rough haversine
            R = 6371
            dlat = radians(row["current_lat"] - lat)
            dlon = radians(row["current_lng"] - lng)
            a = sin(dlat/2)**2 + cos(radians(lat)) * cos(radians(row["current_lat"])) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            if distance <= radius_km:
                row["distance_km"] = round(distance, 2)
                nearby.append(row)
        return nearby
    except Exception as e:
        return {"error": str(e)}
