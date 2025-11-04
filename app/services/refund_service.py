# app/services/refunds_service.py
import razorpay
from datetime import datetime
from typing import Dict, Any
from app.core.settings import settings
from app.services.supabase_service import supabase

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def process_refund(provider_payment_id: str, user_id: str, amount: float, reason: str) -> Dict[str, Any]:
    """
    Initiate refund via Razorpay using provider_payment_id (Razorpay payment id).
    Log refund in refunds table and update payments.status internally.
    If provider_payment_id is missing (manual refund), credit wallet instead.
    NOTE: Do not rely on DB-level FK to provider_payment_id unless that column is UNIQUE.
    """
    try:
        # Edge case: manual refund without a provider payment id -> wallet credit fallback
        if not provider_payment_id:
            from app.services.wallet_service import credit_wallet
            credit_wallet(user_id, amount, f"Refund issued manually: {reason}")
            return {"success": True, "method": "wallet", "status": "credited"}

        # Razorpay expects amount in paise
        refund = razorpay_client.payment.refund(provider_payment_id, {"amount": int(round(amount * 100))})

        # Normalize refund status
        refund_status = refund.get("status", "initiated")
        if refund_status in ("processed", "completed"):
            refund_status = "succeeded"

        # Persist refund record (store provider_payment_id rather than FK)
        supabase.table("refunds").insert({
            "provider_payment_id": provider_payment_id,
            "user_id": user_id,
            "amount": amount,
            "status": refund_status,
            "reason": reason,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

        # update payments table status to refunded where provider_payment_id matches
        supabase.table("payments").update({"status": "refunded"}).eq("provider_payment_id", provider_payment_id).execute()

        return {"success": True, "refund_id": refund.get("id"), "status": refund_status}
    except razorpay.errors.BadRequestError as e:
        return {"error": f"Razorpay error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
