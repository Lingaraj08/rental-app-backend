# app/services/storage_service.py

import os
from supabase import create_client, Client
from app.core import settings
from datetime import datetime

supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

BUCKET_NAME = "listing-photos"

def upload_listing_image(file, listing_id: int):
    try:
        # Create a unique filename
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        file_path = f"listings/{listing_id}/{timestamp}_{file.filename}"

        # Upload file bytes
        supabase.storage.from_(BUCKET_NAME).upload(file_path, file.file)

        # Get the public URL
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path)
        return {"public_url": public_url}
    except Exception as e:
        return {"error": str(e)}
