# app/services/review_service.py
from datetime import datetime
from app.services.supabase_service import supabase


def add_review(reviewer_id: str, owner_id: str, listing_id: int, rating: int, comment: str):
    """Add a review for a completed rental."""
    try:
        # Basic input validation
        if rating < 1 or rating > 5:
            return {"error": "Rating must be between 1 and 5"}

        data = {
            "reviewer_id": reviewer_id,
            "owner_id": owner_id,
            "listing_id": listing_id,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.utcnow().isoformat()
        }

        res = supabase.table("reviews").insert(data).execute()
        return {"created": res.data}
    except Exception as e:
        return {"error": str(e)}


def get_reviews_for_listing(listing_id: int):
    """Fetch all reviews for a particular listing."""
    try:
        res = supabase.table("reviews").select("*").eq("listing_id", listing_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}


def get_reviews_for_owner(owner_id: str):
    """Fetch all reviews for an owner."""
    try:
        res = supabase.table("reviews").select("*").eq("owner_id", owner_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}


def get_average_rating(owner_id: str):
    """Calculate average rating for an owner."""
    try:
        res = supabase.table("reviews").select("rating").eq("owner_id", owner_id).execute()
        if not res.data:
            return {"average_rating": 0, "total_reviews": 0}
        ratings = [r["rating"] for r in res.data]
        avg = round(sum(ratings) / len(ratings), 2)
        return {"average_rating": avg, "total_reviews": len(ratings)}
    except Exception as e:
        return {"error": str(e)}
