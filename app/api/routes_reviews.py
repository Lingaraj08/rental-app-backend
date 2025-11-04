# app/api/routes_reviews.py
from fastapi import APIRouter, Header
from app.services.review_service import add_review, get_reviews_for_listing, get_reviews_for_owner, get_average_rating
from app.services.auth_service import verify_access_token

router = APIRouter()

@router.post("/reviews", tags=["Reviews"])
def create_review(owner_id: str, listing_id: int, rating: int, comment: str, authorization: str = Header(None)):
    """Add a review (only by authenticated users)."""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    reviewer_id = verify_access_token(token)
    if not reviewer_id:
        return {"error": "Invalid or expired token"}

    return add_review(reviewer_id, owner_id, listing_id, rating, comment)


@router.get("/reviews/listing/{listing_id}", tags=["Reviews"])
def get_listing_reviews(listing_id: int):
    """Fetch all reviews for a listing."""
    return {"reviews": get_reviews_for_listing(listing_id)}


@router.get("/reviews/owner/{owner_id}", tags=["Reviews"])
def get_owner_reviews(owner_id: str):
    """Fetch all reviews for an owner."""
    return {"reviews": get_reviews_for_owner(owner_id)}


@router.get("/reviews/owner/{owner_id}/average", tags=["Reviews"])
def get_owner_average(owner_id: str):
    """Fetch average rating for an owner."""
    return get_average_rating(owner_id)
