# app/services/message_service.py
from datetime import datetime
from typing import Optional
from app.services.supabase_service import supabase

def send_message(sender_id: str, receiver_id: str, content: str, listing_id: Optional[int] = None):
    """Send a message from one user to another. Optionally associate to a listing."""
    data = {
        "sender_id": sender_id,
        "receiver_id": receiver_id,
        "content": content,
        "created_at": datetime.utcnow().isoformat(),
        "is_read": False,
    }
    if listing_id is not None:
        data["listing_id"] = listing_id
    result = supabase.table("messages").insert(data).execute()
    return result.data


def get_messages(user_id: str, contact_id: str, listing_id: Optional[int] = None):
    """Fetch conversation between two users. Optionally filter by listing."""
    query = (
        supabase.table("messages")
        .select("*")
        .or_(f"(sender_id.eq.{user_id},receiver_id.eq.{contact_id}),(sender_id.eq.{contact_id},receiver_id.eq.{user_id})")
        .order("created_at", desc=False)
    )
    if listing_id is not None:
        query = query.eq("listing_id", listing_id)
    result = query.execute()
    return result.data


def mark_message_as_read(message_id: int):
    """Mark a specific message as read"""
    result = supabase.table("messages").update({"is_read": True}).eq("id", message_id).execute()
    return result.data


# New helper names for compatibility with optional design
def get_conversation(user_id: str, other_id: str, listing_id: Optional[int] = None):
    """Alias for get_messages with optional listing filter."""
    return get_messages(user_id, other_id, listing_id)


def mark_as_read(message_id: int):
    """Alias for mark_message_as_read."""
    return mark_message_as_read(message_id)
