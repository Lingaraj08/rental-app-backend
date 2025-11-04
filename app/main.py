# app/main.py

from fastapi import FastAPI
from app.api import routes_categories  # import your new router file
from app.api import routes_listings
from app.api import routes_auth
from app.api import routes_bookings
from app.api import routes_uploads
from app.api import routes_delivery
from app.api import routes_transactions
from app.api import routes_wallet
from app.api import routes_messages
from app.api import routes_reviews
from app.api import routes_reports
from app.api import routes_notifications
from app.api import routes_admin
from app.api import routes_payments
from app.api import routes_refund
from app.api import routes_kyc
from app.api import routes_ws

app = FastAPI(title="CampuRent")

# Root health check route
@app.get("/")
def health_check():
    return {"status": "ok"}

# Register the categories router
app.include_router(routes_categories.router)
app.include_router(routes_listings.router)
app.include_router(routes_auth.router)
app.include_router(routes_bookings.router)
app.include_router(routes_uploads.router)
app.include_router(routes_delivery.router)
app.include_router(routes_transactions.router)
app.include_router(routes_wallet.router)
app.include_router(routes_messages.router)
app.include_router(routes_reviews.router)
app.include_router(routes_reports.router)
app.include_router(routes_notifications.router)
app.include_router(routes_admin.router)
app.include_router(routes_payments.router)
app.include_router(routes_refund.router)
app.include_router(routes_kyc.router)
app.include_router(routes_ws.router)


# Start realtime event listener on startup
import asyncio
from app.services.realtime_listener import watch_realtime_events

@app.on_event("startup")
async def startup_event():
    """Initialize realtime listener"""
    asyncio.create_task(watch_realtime_events())
    print("🚀 Server + Realtime listener started")
