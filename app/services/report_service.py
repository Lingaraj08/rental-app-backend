# app/services/report_service.py
from app.services.supabase_service import supabase
from datetime import datetime

def file_report(reporter_id: str, reported_user_id: str, listing_id: int, booking_id: int, issue_type: str, description: str):
    """Submit a report for any issue (damage, fraud, delay, etc.)"""
    try:
        data = {
            "reporter_id": reporter_id,
            "reported_user_id": reported_user_id,
            "listing_id": listing_id,
            "booking_id": booking_id,
            "issue_type": issue_type,
            "description": description,
            "status": "pending",
            "created_at": datetime.utcnow().isoformat()
        }
        res = supabase.table("reports").insert(data).execute()
        return {"created": res.data}
    except Exception as e:
        return {"error": str(e)}


def get_reports_by_user(user_id: str):
    """Get all reports filed by a user."""
    try:
        res = supabase.table("reports").select("*").eq("reporter_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}


def get_reports_against_user(user_id: str):
    """Get all reports against a user."""
    try:
        res = supabase.table("reports").select("*").eq("reported_user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}


def update_report_status(report_id: int, status: str):
    """Admin or system can mark report as reviewed/resolved."""
    try:
        res = supabase.table("reports").update({"status": status}).eq("id", report_id).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}
