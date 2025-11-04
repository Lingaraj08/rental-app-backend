# app/services/supabase_service.py

from supabase import create_client, Client
from app.core import settings

# Create Supabase client
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

def get_all_categories():
    """
    Fetch all categories from the 'categories' table.
    Returns a list of dicts.
    """
    try:
        response = supabase.table("categories").select("*").execute()
        # Print response for debugging
        print("Supabase Response:", response)
        return response.data if response.data else {"message": "No categories found"}
    except Exception as e:
        return {"error": str(e)}
