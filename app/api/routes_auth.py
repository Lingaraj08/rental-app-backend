# app/api/routes_auth.py
from fastapi import APIRouter
from app.services.auth_service import signup_user, login_user

router = APIRouter()

@router.post("/auth/signup", tags=["Auth"])
def signup(email: str, password: str):
    """Register a new user in Supabase Auth."""
    return signup_user(email, password)

@router.post("/auth/login", tags=["Auth"])
def login(email: str, password: str):
    """Log in an existing user."""
    return login_user(email, password)
