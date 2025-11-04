# app/services/wallet_service.py
from app.services.supabase_service import supabase
from datetime import datetime
from typing import Dict, Any, Union

def get_wallet_balance(user_id: str) -> Dict[str, Union[float,int]]:
    res = supabase.table("wallets").select("balance").eq("user_id", user_id).execute()
    if not res.data:
        supabase.table("wallets").insert({"user_id": user_id, "balance": 0, "last_updated": datetime.utcnow().isoformat()}).execute()
        return {"balance": 0}
    return res.data[0]


def get_wallet_record(user_id: str) -> Dict[str, Any]:
    res = supabase.table("wallets").select("*").eq("user_id", user_id).execute()
    if not res.data:
        supabase.table("wallets").insert({"user_id": user_id, "balance": 0, "last_updated": datetime.utcnow().isoformat()}).execute()
        return {"user_id": user_id, "balance": 0}
    return res.data[0]


def debit_wallet(user_id: str, amount: float, description: str) -> Dict[str, Any]:
    wallet = get_wallet_record(user_id)
    new_balance = float(wallet.get("balance", 0)) - float(amount)
    if new_balance < 0:
        return {"error": "Insufficient balance", "balance": wallet.get("balance", 0)}

    supabase.table("wallets").update({
        "balance": new_balance,
        "last_updated": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()

    supabase.table("wallet_transactions").insert({
        "user_id": user_id,
        "type": "debit",
        "amount": amount,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return {"balance": new_balance}


def credit_wallet(user_id: str, amount: float, description: str) -> Dict[str, Any]:
    wallet = get_wallet_record(user_id)
    new_balance = float(wallet.get("balance", 0)) + float(amount)
    supabase.table("wallets").update({
        "balance": new_balance,
        "last_updated": datetime.utcnow().isoformat()
    }).eq("user_id", user_id).execute()

    supabase.table("wallet_transactions").insert({
        "user_id": user_id,
        "type": "credit",
        "amount": amount,
        "description": description,
        "created_at": datetime.utcnow().isoformat()
    }).execute()

    return {"balance": new_balance}


def get_wallet_transactions(user_id: str):
    res = supabase.table("wallet_transactions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
    return res.data or []
