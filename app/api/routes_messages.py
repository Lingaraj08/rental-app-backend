# app/api/routes_messages.py
from fastapi import APIRouter, Header
from app.services.message_service import send_message, get_conversation, mark_as_read
from app.services.auth_service import verify_access_token

router = APIRouter()

@router.post("/messages", tags=["Messages"])
def send_chat_message(receiver_id: str, listing_id: int, message: str, authorization: str = Header(None)):
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    sender_id = verify_access_token(token)
    if not sender_id:
        return {"error": "Invalid token"}

    # Our service signature is (sender_id, receiver_id, content, listing_id=None)
    return send_message(sender_id, receiver_id, message, listing_id)


@router.get("/messages/{other_id}", tags=["Messages"])
def get_chat_history(other_id: str, listing_id: int = None, authorization: str = Header(None)):
    if not authorization:
        return {"error": "Missing token"}
    token = authorization.replace("Bearer ", "")
    user_id = verify_access_token(token)
    if not user_id:
        return {"error": "Invalid token"}

    return {"messages": get_conversation(user_id, other_id, listing_id)}


@router.post("/messages/read/{message_id}", tags=["Messages"])
def mark_message_read(message_id: int):
    return mark_as_read(message_id)
