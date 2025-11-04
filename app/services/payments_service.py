# app/services/payments_service.py
import razorpay
from datetime import datetime
from typing import Dict, Any
from app.core.settings import settings
from app.services.supabase_service import supabase
from app.services.wallet_service import credit_wallet

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_payment_order(user_id: str, amount: float, purpose: str) -> Dict[str, Any]:
    """
    Create a Razorpay order and persist it to payments table.
    Stores provider_order_id in payments.provider_order_id to match your schema.
    Returns order id and key id for client checkout.
    """
    try:
        order_data = {
            "amount": int(round(amount * 100)),  # paise
            "currency": "INR",
            "payment_capture": 1
        }
        order = razorpay_client.order.create(order_data)

        record = {
            "user_id": user_id,
            "amount": amount,
            "currency": "INR",
            "provider": "razorpay",
            "provider_order_id": order.get("id"),
            "status": "created",
            "metadata": {"purpose": purpose},
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("payments").insert(record).execute()

        return {"order_id": order.get("id"), "key_id": settings.RAZORPAY_KEY_ID}

    except Exception as e:
        return {"error": str(e)}


def verify_payment_signature(provider_order_id: str, provider_payment_id: str, signature: str) -> Dict[str, Any]:
    """
    Verify Razorpay signature and on success update payments and credit user's wallet.
    Uses provider_order_id to find the payment row.
    """
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": provider_order_id,
            "razorpay_payment_id": provider_payment_id,
            "razorpay_signature": signature
        })

        # update payment record
        supabase.table("payments").update({
            "provider_payment_id": provider_payment_id,
            "signature": signature,
            "status": "succeeded",
            "verified_at": datetime.utcnow().isoformat()
        }).eq("provider_order_id", provider_order_id).execute()

        # fetch payment to credit wallet
        payment_res = supabase.table("payments").select("*").eq("provider_order_id", provider_order_id).execute()
        if not payment_res.data:
            return {"error": "Payment record not found after verification"}

        payment = payment_res.data[0]
        # credit wallet (top-up)
        credit_wallet(payment["user_id"], float(payment["amount"]), f"Top-up {payment.get('metadata', {}).get('purpose', '')}")

        # add wallet transaction already handled in credit_wallet
        return {"success": True, "message": "Payment verified and wallet credited"}

    except razorpay.errors.SignatureVerificationError:
        supabase.table("payments").update({"status": "failed"}).eq("provider_order_id", provider_order_id).execute()
        return {"error": "Invalid payment signature"}
    except Exception as e:
        return {"error": str(e)}
