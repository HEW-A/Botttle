from flask import Blueprint, jsonify

from common.auth_helper import get_current_user
from common.supabase_client import supabase

coins_bp = Blueprint("coins", __name__)


@coins_bp.get("/balance")
def get_balance():
    """ログイン中ユーザーのコイン残高(coin_transaction.amount の合計)を返す"""
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": "ログインが必要です"}), 401

    response = supabase.rpc(
        "get_coin_balance", {"p_user_id": current_user["user_id"]}
    ).execute()
    return jsonify({"balance": response.data or 0})
