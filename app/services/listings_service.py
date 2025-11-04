# app/services/listings_service.py
from datetime import datetime
from typing import Dict, Any
from app.services.supabase_service import supabase
from app.services.wallet_service import debit_wallet

LISTING_FEE = 25.0


def get_all_listings():
    try:
        res = supabase.table("listings").select("*").execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}


def add_listing(title: str, description: str, price: float, category_id: int, owner_id: str, require_paid: bool = True) -> Dict[str, Any]:
    """
    Create a listing and optionally debit LISTING_FEE from owner's wallet.
    """
    try:
        if require_paid:
            debit_res = debit_wallet(owner_id, LISTING_FEE, f"Listing fee for '{title}'")
            if isinstance(debit_res, dict) and debit_res.get("error"):
                return {"error": "Listing fee debit failed", "details": debit_res}

        data = {
            "title": title,
            "description": description,
            "price_per_day": price,
            "owner_id": owner_id,
            "category_id": category_id,
            "is_paid_listing_fee": bool(require_paid),
            "created_at": datetime.utcnow().isoformat()
        }
        res = supabase.table("listings").insert(data).execute()
        return {"created": res.data}
    except Exception as e:
        return {"error": str(e)}


def delete_listing(listing_id: int):
    try:
        res = supabase.table("listings").delete().eq("id", listing_id).execute()
        return {"deleted": res.data}
    except Exception as e:
        return {"error": str(e)}
