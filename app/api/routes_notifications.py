from fastapi import APIRouter, Header
from app.services.auth_service import verify_access_token
from app.services.notifications_service import create_notification, get_user_notifications, mark_notification_read

router = APIRouter()

@router.get("/notifications", tags=["Notifications"])
def read_notifications(authorization: str = Header(None)):
    """Fetch all notifications for logged-in user"""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return {"notifications": get_user_notifications(user_id)}

@router.post("/notifications", tags=["Notifications"])
def send_notification(
    title: str,
    message: str,
    type: str = "system",
    related_id: int = None,
    authorization: str = Header(None)
):
    """Manually send a notification (for testing)"""
    if not authorization:
        return {"error": "Missing access token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}
    return create_notification(user_id, title, message, type, related_id)

@router.patch("/notifications/{notification_id}/read", tags=["Notifications"])
def mark_read(notification_id: int):
    """Mark a notification as read"""
    return mark_notification_read(notification_id)
