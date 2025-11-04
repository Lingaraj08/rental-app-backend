# app/services/kyc_service.py

from datetime import datetime
from app.services.supabase_service import supabase
import requests
import os
import base64
import uuid
from app.core import settings

# Optional: Use Face++ or any free API for verification
FACE_API_KEY = os.getenv("FACE_API_KEY")
FACE_API_SECRET = os.getenv("FACE_API_SECRET")

def verify_face_match(govt_id_url: str, selfie_url: str) -> float:
    """
    Uses a third-party API to compare two faces.
    Returns a match score between 0–1.
    """
    try:
        # Example using Face++ (free tier works well)
        api_url = "https://api-us.faceplusplus.com/facepp/v3/compare"
        data = {
            "api_key": FACE_API_KEY,
            "api_secret": FACE_API_SECRET,
            "image_url1": govt_id_url,
            "image_url2": selfie_url,
        }
        resp = requests.post(api_url, data=data)
        result = resp.json()
        return result.get("confidence", 0) / 100  # normalize to 0–1
    except Exception as e:
        print("Face match API error:", e)
        return 0.0


def submit_kyc(user_id: str, govt_id_url: str, selfie_url: str):
    """Submits KYC with face match, falls back to manual review if score < 0.85"""
    try:
        score = verify_face_match(govt_id_url, selfie_url)
        auto_pass = score >= 0.85

        record = {
            "user_id": user_id,
            "govt_id_url": govt_id_url,
            "selfie_url": selfie_url,
            "face_match_score": score,
            "verified": auto_pass,
            "stage": "auto" if auto_pass else "manual",
            "created_at": datetime.utcnow().isoformat()
        }

        supabase.table("kyc_verifications").insert(record).execute()

        # Save metadata to users table and set verification flag based on auto_pass
        supabase.table("users").update({
            "kyc_verified": bool(auto_pass),
            "kyc_id_doc": govt_id_url,
            "kyc_selfie": selfie_url,
            "kyc_submitted_at": datetime.utcnow().isoformat(),
        }).eq("id", user_id).execute()

        if auto_pass:
            return {"verified": True, "method": "auto", "score": score}

        # fallback to manual
        notify_admin_for_review(user_id)
        return {
            "verified": False,
            "method": "manual_review",
            "message": "Face match below threshold. Sent for admin review.",
            "score": score
        }

    except Exception as e:
        return {"error": str(e)}


def notify_admin_for_review(user_id: str):
    """Notify admin when manual KYC is needed."""
    supabase.table("notifications").insert({
        "user_id": user_id,
        "title": "Manual KYC Review Required",
        "message": f"KYC verification for user {user_id} needs review.",
        "type": "system"
    }).execute()


def review_kyc(user_id: str, admin_id: str, approve: bool, reason: str = None):
    """Admin manually reviews pending KYC submissions."""
    try:
        supabase.table("kyc_verifications").update({
            "verified": approve,
            "reviewer_id": admin_id,
            "reason": reason or ("Approved" if approve else "Rejected"),
            "verified_at": datetime.utcnow().isoformat(),
            "stage": "manual"
        }).eq("user_id", user_id).execute()

        supabase.table("users").update({
            "kyc_verified": approve
        }).eq("id", user_id).execute()

        return {"success": True, "approved": approve}
    except Exception as e:
        return {"error": str(e)}


def upload_kyc_images(user_id: str, id_image_b64: str, selfie_b64: str):
    """Uploads ID and Selfie images to Supabase Storage under private buckets.

    Returns URLs pointing to the stored objects (may require signed access since buckets are private).
    """
    try:
        # Decode Base64 images
        id_bytes = base64.b64decode(id_image_b64)
        selfie_bytes = base64.b64decode(selfie_b64)

        # Unique file names under user folder
        id_path = f"{user_id}/{uuid.uuid4()}_id.png"
        selfie_path = f"{user_id}/{uuid.uuid4()}_selfie.png"

        # Upload to respective buckets
        supabase.storage.from_("user-id-docs").upload(id_path, id_bytes)
        supabase.storage.from_("user-selfies").upload(selfie_path, selfie_bytes)

        # Build object URLs (note: private buckets need signed URLs to access)
        storage_base = getattr(supabase, "storage_url", f"{settings.SUPABASE_URL}/storage/v1")
        return {
            "id_doc_url": f"{storage_base}/object/user-id-docs/{id_path}",
            "selfie_url": f"{storage_base}/object/user-selfies/{selfie_path}",
        }
    except Exception as e:
        return {"error": str(e)}
