# app/api/routes_uploads.py

from fastapi import APIRouter, File, UploadFile, Header
from app.services.storage_service import upload_listing_image
from app.services.auth_service import verify_access_token
from app.services.listings_service import supabase

router = APIRouter()

@router.post("/upload/{listing_id}", tags=["Uploads"])
def upload_image(
    listing_id: int,
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    """Upload a listing image and attach it to the listing."""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}

    # Upload to Supabase storage
    result = upload_listing_image(file, listing_id)
    if "error" in result:
        return result

    # Update listing record with image URL
    public_url = result["public_url"]
    supabase.table("listings").update({"image_url": public_url}).eq("id", listing_id).execute()

    return {"message": "Image uploaded successfully", "url": public_url}
