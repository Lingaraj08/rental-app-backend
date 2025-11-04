# app/api/routes_categories.py

from fastapi import APIRouter
from app.services.supabase_service import get_all_categories

# Create a router object — this groups related routes (in this case, category routes)
router = APIRouter()

@router.get("/categories", tags=["Categories"])
def read_categories():
    """
    API endpoint to fetch all categories from Supabase.
    """
    data = get_all_categories()
    return {"categories": data}
