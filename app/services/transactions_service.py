# app/services/transactions_service.py
from datetime import date, datetime
from typing import Dict, Any
from app.services.supabase_service import supabase
from app.services.wallet_service import credit_wallet

def create_transaction(renter_id: str, listing_id: int, start_date: date, end_date: date) -> Dict[str, Any]:
    try:
        listing_res = supabase.table("listings").select("*").eq("id", listing_id).execute()
        if not listing_res.data:
            return {"error": "Listing not found"}
        listing = listing_res.data[0]

        owner_id = listing.get("owner_id")
        price_per_day = float(listing.get("price_per_day") or listing.get("price") or 0)
        platform_fee = float(listing.get("platform_fee", 0))

        if end_date < start_date:
            return {"error": "Invalid date range"}

        rental_days = (end_date - start_date).days or 1
        total_amount = (price_per_day * rental_days) + platform_fee

        transaction_data = {
            "renter_id": renter_id,
            "owner_id": owner_id,
            "listing_id": listing_id,
            "start_date": str(start_date),
            "end_date": str(end_date),
            "total_amount": total_amount,
            "payment_status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }

        res = supabase.table("rental_transactions").insert(transaction_data).execute()

        # optionally credit owner immediately or after payment verification based on your flow
        try:
            credit_wallet(owner_id, price_per_day * rental_days, f"Rental income for listing {listing_id}")
        except Exception:
            # don't fail transaction creation if wallet credit fails
            pass

        return {"created": res.data}
    except Exception as e:
        return {"error": str(e)}


def get_user_transactions(user_id: str):
    try:
        res = supabase.table("rental_transactions").select("*").eq("renter_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}
