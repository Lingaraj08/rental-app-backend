# app/api/routes_listings.py
from fastapi import APIRouter, Header
from app.services.listings_service import get_all_listings, add_listing, delete_listing
from app.services.auth_service import verify_access_token
from app.services.supabase_service import supabase

router = APIRouter()

@router.get("/listings", tags=["Listings"])
def all_listings():
    """Get all listings"""
    return {"listings": get_all_listings()}

@router.get("/my_listings", tags=["Listings"])
def my_listings(authorization: str = Header(None)):
    """Fetch listings posted by the logged-in user"""
    if not authorization:
        return {"error": "Missing token"}
    user_id = verify_access_token(authorization.replace("Bearer ", ""))
    if not user_id:
        return {"error": "Invalid token"}
    res = supabase.table("listings").select("*").eq("owner_id", user_id).execute()
    return {"listings": res.data}

@router.post("/listings", tags=["Listings"])
def create_listing(title: str, description: str, price_per_day: float, category_id: int, authorization: str = Header(None)):
    """Create new listing (requires wallet with at least ₹25)"""
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    owner_id = verify_access_token(token)
    if not owner_id:
        return {"error": "Invalid token"}

    # Enforce KYC verification before allowing listing creation
    user_rows = supabase.table("users").select("kyc_verified").eq("id", owner_id).execute().data
    if not user_rows or not user_rows[0].get("kyc_verified"):
        return {"error": "KYC verification required before listing an item"}

    # Create listing and charge the listing fee in the service
    return add_listing(title, description, price_per_day, category_id, owner_id)

@router.delete("/listings/{listing_id}", tags=["Listings"])
def remove_listing(listing_id: int):
    """Delete a listing"""
    return delete_listing(listing_id)
