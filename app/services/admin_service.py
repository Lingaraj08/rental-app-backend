# app/services/admin_service.py
from app.services.supabase_service import supabase
from datetime import datetime
import random

def get_all_users():
    try:
        r = supabase.table("users").select("*").execute()
        return r.data
    except Exception as e:
        return {"error": str(e)}

def delete_user(user_id: str):
    try:
        r = supabase.table("users").delete().eq("id", user_id).execute()
        return {"deleted": r.data}
    except Exception as e:
        return {"error": str(e)}

def get_all_listings():
    try:
        r = supabase.table("listings").select("*").execute()
        return r.data
    except Exception as e:
        return {"error": str(e)}

def delete_listing(listing_id: int):
    try:
        r = supabase.table("listings").delete().eq("id", listing_id).execute()
        return {"deleted": r.data}
    except Exception as e:
        return {"error": str(e)}

def get_reports():
    try:
        r = supabase.table("reports").select("*").order("created_at", desc=True).execute()
        return r.data
    except Exception as e:
        return {"error": str(e)}

def update_report_status(report_id: int, status: str):
    try:
        r = supabase.table("reports").update({"status": status}).eq("id", report_id).execute()
        return r.data
    except Exception as e:
        return {"error": str(e)}

def get_platform_stats():
    try:
        users = supabase.table("users").select("id").execute()
        listings = supabase.table("listings").select("id").execute()
        bookings = supabase.table("bookings").select("id").execute()
        reports = supabase.table("reports").select("id").execute()

        return {
            "total_users": len(users.data or []),
            "total_listings": len(listings.data or []),
            "total_bookings": len(bookings.data or []),
            "total_reports": len(reports.data or [])
        }
    except Exception as e:
        return {"error": str(e)}


def review_kyc(user_id: str, reviewer_id: str, approve: bool, reason: str | None = None):
    """Manually approve/reject a user's KYC and reflect it in users table."""
    try:
        supabase.table("kyc_verifications").update({
            "verified": approve,
            "reviewer_id": reviewer_id,
            "reason": reason,
            "verified_at": datetime.utcnow().isoformat() if approve else None,
        }).eq("user_id", user_id).execute()

        supabase.table("users").update({"kyc_verified": approve}).eq("id", user_id).execute()

        return {"user_id": user_id, "approved": approve}
    except Exception as e:
        return {"error": str(e)}


# ------------------- NEW ADDITIONS -------------------

def log_admin_action_sync(admin_id: str, action_type: str, target_table: str, target_id: int, details: str | None = None):
    """Logs admin activity for audit and traceability."""
    try:
        supabase.table("admin_actions").insert({
            "admin_id": admin_id,
            "action_type": action_type,
            "target_table": target_table,
            "target_id": target_id,
            "details": details,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        # Non-fatal: avoid breaking main flow on log failure
        print(f"Failed to log admin action: {e}")


def get_all_delivery_tasks():
    """Admin fetch of all delivery tasks"""
    try:
        res = supabase.table("delivery_tasks").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}


def override_verification(task_id: int, admin_id: str, verification_type: str):
    """Admin manually verifies pickup/drop if OTP fails."""
    try:
        if verification_type not in ["pickup", "drop"]:
            return {"error": "Invalid verification type"}

        update_data = {
            f"{verification_type}_verified": True,
            f"{verification_type}_otp": "ADMIN_OVERRIDE",
            "last_status_update": datetime.utcnow().isoformat(),
        }

        res = supabase.table("delivery_tasks").update(update_data).eq("id", task_id).execute()
        log_and_notify_admin(
            admin_id,
            f"{verification_type}_override",
            "delivery_tasks",
            task_id,
            "Manual verification override by admin",
        )

        return {"success": True, "updated": res.data}
    except Exception as e:
        return {"error": str(e)}


def regenerate_otp(task_id: int, admin_id: str):
    """Allows admin to regenerate OTP in case user didn’t receive one."""
    try:
        new_otp = str(random.randint(100000, 999999))
        res = supabase.table("delivery_tasks").update({"pickup_otp": new_otp, "last_status_update": datetime.utcnow().isoformat()}).eq("id", task_id).execute()

        log_and_notify_admin(
            admin_id,
            "regenerate_otp",
            "delivery_tasks",
            task_id,
            f"New OTP: {new_otp}",
        )

        return {"success": True, "new_otp": new_otp}
    except Exception as e:
        return {"error": str(e)}


def get_admin_actions():
    """Retrieve all logged admin actions for audit."""
    try:
        res = supabase.table("admin_actions").select("*").order("created_at", desc=True).execute()
        return res.data
    except Exception as e:
        return {"error": str(e)}

# ---------- ADMIN EVENT HOOKS & NOTIFICATIONS ----------

def send_admin_notification_sync(admin_id: str, title: str, message: str):
    """Sends a notification to admin (for internal audit or alerting)."""
    try:
        supabase.table("notifications").insert({
            "user_id": admin_id,
            "title": title,
            "message": message,
            "type": "system",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        print(f"⚠️ Failed to send admin notification: {e}")


def log_and_notify_admin(admin_id: str, action_type: str, target_table: str, target_id: int, details: str):
    """Combines log + notification for important admin events."""
    # Log first
    log_admin_action_sync(admin_id, action_type, target_table, target_id, details)

    # Then notify all admins (or just the acting one)
    send_admin_notification_sync(
        admin_id,
        title=f"Admin Action: {action_type}",
        message=f"Action on {target_table} (ID: {target_id}) — {details}"
    )


def auto_close_stale_deliveries():
    """Marks delivery tasks older than 48h as 'completed' if not already closed."""
    try:
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=48)
        res = supabase.table("delivery_tasks").select("*").lt("created_at", cutoff.isoformat()).neq("status", "completed").execute()

        if not res.data:
            return {"message": "No stale deliveries"}

        for task in res.data:
            supabase.table("delivery_tasks").update({"status": "completed"}).eq("id", task["id"]).execute()
            log_admin_action_sync("system", "auto_close", "delivery_tasks", task["id"], "Auto-closed stale delivery")

        return {"closed_tasks": len(res.data)}
    except Exception as e:
        return {"error": str(e)}

async def send_admin_notification(admin_id: str, title: str, message: str):
    """Async version for contexts using Supabase async client."""
    try:
        await supabase.table("notifications").insert({
            "user_id": admin_id,
            "title": title,
            "message": message,
            "type": "system",
            "is_read": False,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        print(f"⚠️ Failed to send admin notification: {e}")


async def log_admin_action(admin_id: str, action_type: str, target_table: str, target_id: int, details: str | None = None):
    """Async version for contexts using Supabase async client."""
    try:
        await supabase.table("admin_actions").insert({
            "admin_id": admin_id,
            "action_type": action_type,
            "target_table": target_table,
            "target_id": target_id,
            "details": details,
            "created_at": datetime.utcnow().isoformat(),
        }).execute()
    except Exception as e:
        print(f"⚠️ Failed to log admin action: {e}")

