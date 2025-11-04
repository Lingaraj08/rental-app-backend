from app.services.supabase_service import supabase

def create_notification(user_id: str, title: str, message: str, type: str = "system", related_id: int = None):
    try:
        data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": type,
            "related_id": related_id
        }
        res = supabase.table("notifications").insert(data).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}

def get_user_notifications(user_id: str):
    try:
        res = supabase.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}

def mark_notification_read(notification_id: int):
    try:
        res = supabase.table("notifications").update({"is_read": True}).eq("id", notification_id).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}
