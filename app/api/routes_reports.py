# app/api/routes_reports.py
from fastapi import APIRouter, Header
from app.services.report_service import file_report, get_reports_by_user, get_reports_against_user, update_report_status
from app.services.auth_service import verify_access_token

router = APIRouter()

@router.post("/reports", tags=["Reports"])
def create_report(
    reported_user_id: str,
    listing_id: int,
    booking_id: int,
    issue_type: str,
    description: str,
    authorization: str = Header(None)
):
    """Submit a report about any issue related to a transaction."""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    reporter_id = verify_access_token(token)
    if not reporter_id:
        return {"error": "Invalid or expired token"}

    return file_report(reporter_id, reported_user_id, listing_id, booking_id, issue_type, description)


@router.get("/reports/my_reports", tags=["Reports"])
def view_my_reports(authorization: str = Header(None)):
    """View all reports filed by current user."""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid or expired token"}

    return {"reports": get_reports_by_user(user_id)}


@router.get("/reports/against_me", tags=["Reports"])
def view_reports_against_me(authorization: str = Header(None)):
    """View all reports filed against current user."""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid or expired token"}

    return {"reports": get_reports_against_user(user_id)}


@router.put("/reports/{report_id}", tags=["Reports"])
def modify_report_status(report_id: int, status: str):
    """Admin endpoint to mark report as reviewed/resolved."""
    return update_report_status(report_id, status)
