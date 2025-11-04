# app/services/bookings_service.py
from datetime import datetime
from typing import Dict, Any
from app.services.supabase_service import supabase
from app.services.wallet_service import debit_wallet

BOOKING_FEE = 20.0


def create_booking(listing_id: int, renter_id: str, owner_id: str, start_date: str, end_date: str) -> Dict[str, Any]:
    try:
        # Enforce KYC verification before proceeding
        user_rows = supabase.table("users").select("kyc_verified").eq("id", renter_id).execute().data
        if not user_rows:
            return {"error": "User not found or not eligible to book"}
        user = user_rows[0]
        if not user.get("kyc_verified"):
            return {"error": "KYC verification required before booking."}

        # charge booking fee immediately
        debit_res = debit_wallet(renter_id, BOOKING_FEE, f"Booking fee for listing {listing_id}")
        if isinstance(debit_res, dict) and debit_res.get("error"):
            return {"error": "Insufficient wallet balance. Please top-up first.", "details": debit_res}

        # fetch listing price_per_day (fallback to price)
        listing_res = supabase.table("listings").select("price_per_day, price").eq("id", listing_id).execute()
        if not listing_res.data:
            return {"error": "Listing not found"}
        listing = listing_res.data[0]
        rent_per_day = float(listing.get("price_per_day") or listing.get("price") or 0)

        # parse dates
        from datetime import datetime as _dt
        start = _dt.strptime(start_date, "%Y-%m-%d")
        end = _dt.strptime(end_date, "%Y-%m-%d")
        days = max(1, (end - start).days)

        rent_amount = rent_per_day * days
        total_amount = rent_amount + BOOKING_FEE

        booking_data = {
            "listing_id": listing_id,
            "renter_id": renter_id,
            "owner_id": owner_id,
            "start_date": start_date,
            "end_date": end_date,
            "rent_amount": rent_amount,
            "total_amount": total_amount,
            "platform_fee": 0,
            "delivery_fee": 0,
            "status": "requested",
            "created_at": datetime.utcnow().isoformat()
        }

        res = supabase.table("bookings").insert(booking_data).execute()
        return {"booking": res.data}
    except Exception as e:
        return {"error": str(e)}


def update_booking_status(booking_id: int, status: str) -> Dict[str, Any]:
    try:
        res = supabase.table("bookings").update({"status": status}).eq("id", booking_id).execute()
        return {"updated": res.data}
    except Exception as e:
        return {"error": str(e)}


def get_bookings_for_user(user_id: str):
    try:
        res = supabase.table("bookings").select("*").or_(f"renter_id.eq.{user_id},owner_id.eq.{user_id}").execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}
