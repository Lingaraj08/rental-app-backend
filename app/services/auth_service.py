# app/services/auth_service.py
from supabase import create_client, Client
from app.core import settings

# Use the service role or anon key depending on required operations. Here we use anon
# because auth client uses anon key for user signups/signins.
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)


def signup_user(email: str, password: str):
    try:
        r = supabase.auth.sign_up({"email": email, "password": password})
        return {"user": getattr(r, "user", None)}
    except Exception as e:
        return {"error": str(e)}


def login_user(email: str, password: str):
    try:
        r = supabase.auth.sign_in_with_password({"email": email, "password": password})
        return {"session": getattr(r, "session", None)}
    except Exception as e:
        return {"error": str(e)}


def get_user_details(access_token: str):
    try:
        r = supabase.auth.get_user(access_token)
        return {"user": getattr(r, "user", None)}
    except Exception as e:
        return {"error": str(e)}


def verify_access_token(access_token: str):
    try:
        r = supabase.auth.get_user(access_token)
        if r and getattr(r, "user", None):
            return r.user.id
        return None
    except Exception as e:
        print("Auth verify error:", e)
        return None
