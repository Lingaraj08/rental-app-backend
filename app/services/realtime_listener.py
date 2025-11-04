# app/services/realtime_listener.py

import asyncio
import importlib
from supabase import AsyncClient, create_async_client
from app.core import settings
from app.services.admin_service import send_admin_notification, log_admin_action


async def watch_realtime_events():
    """Async listener that reacts to realtime changes in key tables."""
    print("🟡 Starting Realtime Listener...")

    # Create async client
    supabase: AsyncClient = await create_async_client(settings.SUPABASE_URL, settings.SUPABASE_ANON_KEY)

    # Create a realtime channel
    channel = supabase.channel("server-events")

    # --------------- DELIVERY STATUS WATCHER ---------------
    async def handle_delivery_update(payload):
        new_data = payload.get("new", {})
        old_data = payload.get("old", {})
        status = new_data.get("status")
        task_id = new_data.get("id")

        # Case 1: Delivery status changed
        if status and status != old_data.get("status"):
            if status in ["picked", "completed"]:
                await send_admin_notification(
                    admin_id="system",
                    title=f"Delivery {status}",
                    message=f"Delivery task #{task_id} marked as {status}.",
                )
                await log_admin_action(
                    "system",
                    "delivery_status_update",
                    "delivery_tasks",
                    task_id,
                    f"Status changed to {status}",
                )

        # Case 2: Live location update
        lat = new_data.get("current_lat")
        lng = new_data.get("current_lng")
        if lat and lng and (
            lat != old_data.get("current_lat") or lng != old_data.get("current_lng")
        ):
            print(f"📍 Live update — Task #{task_id}: ({lat}, {lng})")

            # Fetch both users involved
            renter_id = new_data.get("renter_id")
            owner_id = new_data.get("owner_id")
            # Broadcast to both users
            manager = None
            try:
                websocket_module = importlib.import_module("app.core.websocket_manager")
                manager = getattr(websocket_module, "manager", None)
            except Exception:
                manager = None

            update_message = {
                "type": "delivery_update",
                "task_id": task_id,
                "lat": lat,
                "lng": lng,
                "status": new_data.get("status"),
            }

            # Send updates
            if manager:
                if renter_id:
                    await manager.send_to_user(renter_id, update_message)
                if owner_id:
                    await manager.send_to_user(owner_id, update_message)
            else:
                print("⚠️ WebSocket manager not available; skipping realtime user updates.")

    channel.on_postgres_changes(
        event="UPDATE",
        schema="public",
        table="delivery_tasks",
        callback=handle_delivery_update,
    )

    # --------------- REPORT WATCHER ---------------
    async def handle_new_report(payload):
        report = payload.get("new", {})
        await send_admin_notification(
            admin_id="system",
            title="New Report Filed",
            message=f"Issue type: {report.get('issue_type')} for listing #{report.get('listing_id')}",
        )
        await log_admin_action(
            "system",
            "new_report",
            "reports",
            report.get("id"),
            "Auto-logged on report submission",
        )

    channel.on_postgres_changes(
        event="INSERT",
        schema="public",
        table="reports",
        callback=handle_new_report,
    )

    # --------------- PAYMENT WATCHER ---------------
    async def handle_payment_update(payload):
        payment = payload.get("new", {})
        if payment.get("status") == "succeeded":
            await send_admin_notification(
                admin_id="system",
                title="Payment Success",
                message=f"User {payment.get('user_id')} paid ₹{payment.get('amount')} successfully.",
            )
            await log_admin_action(
                "system",
                "payment_success",
                "payments",
                payment.get("id"),
                "Payment confirmed",
            )

    channel.on_postgres_changes(
        event="UPDATE",
        schema="public",
        table="payments",
        callback=handle_payment_update,
    )

    # Subscribe to all
    await channel.subscribe()
    print("✅ Subscribed to realtime: delivery_tasks, reports, payments")

    # Keep listener alive
    while True:
        await asyncio.sleep(30)
