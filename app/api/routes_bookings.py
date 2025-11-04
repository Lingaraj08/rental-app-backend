# app/api/routes_bookings.py
from fastapi import APIRouter, Header
from app.services.bookings_service import create_booking, get_bookings_for_user, update_booking_status
from app.services.auth_service import verify_access_token
from app.services.supabase_service import supabase

router = APIRouter()

@router.post("/bookings", tags=["Bookings"])
def new_booking(listing_id: int, owner_id: str, start_date: str, end_date: str, authorization: str = Header(None)):
    """Create a booking and charge ₹20 booking fee from wallet"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    renter_id = verify_access_token(token)
    if not renter_id:
        return {"error": "Invalid token"}
    # Enforce KYC verification before allowing booking
    renter = supabase.table("users").select("kyc_verified").eq("id", renter_id).execute().data
    if not renter or not renter[0].get("kyc_verified"):
        return {"error": "KYC verification required before booking an item"}
    return create_booking(listing_id, renter_id, owner_id, start_date, end_date)

@router.patch("/bookings/{booking_id}", tags=["Bookings"])
def update_status(booking_id: int, status: str):
    """Update booking status"""
    return update_booking_status(booking_id, status)

@router.get("/my_bookings", tags=["Bookings"])
def my_bookings(authorization: str = Header(None)):
    """Get bookings where user is renter or owner"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return {"bookings": get_bookings_for_user(user_id)}
