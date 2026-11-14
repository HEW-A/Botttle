import uuid

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from common.auth_helper import get_current_user
from common.supabase_client import supabase

purchases_bp = Blueprint("purchases", __name__)

LOGIN_REQUIRED_ERROR = "ログインが必要です"
INVALID_ID_ERROR = "無効なchatbot_idです"
INVALID_TOTAL_ERROR = "expected_total は0以上の整数で指定してください"

# DB関数 purchase_chatbots が RAISE EXCEPTION で返すエラーコードと、APIで返す内容の対応。
# 残高確認・購入記録の追加・コインの減算・カートからの削除を1トランザクションで行うため、
# 購入処理はすべてDB関数側にまとめている(supabase/migrations/20261114100000_create_purchase_functions.sql)。
PURCHASE_ERRORS = {
    "USER_NOT_FOUND": (401, LOGIN_REQUIRED_ERROR),
    "CART_EMPTY": (400, "カートに購入できる商品がありません"),
    "PRODUCT_NOT_FOUND": (404, "商品が見つかりません"),
    "OWN_PRODUCT": (400, "自分の商品は購入できません"),
    "ALREADY_PURCHASED": (409, "すでに購入済みの商品が含まれています"),
    "TOTAL_MISMATCH": (409, "商品の価格が変更されています。内容を確認してから購入してください"),
    "INSUFFICIENT_BALANCE": (400, "コインの残高が不足しています"),
}


def _normalize_chatbot_id(value):
    """UUIDとして正しければ正規化した文字列、正しくなければNoneを返す"""
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _parse_expected_total(body):
    """
    expected_total を取り出す。
    未指定なら (True, None)、正しい整数なら (True, 値)、不正なら (False, None) を返す。
    """
    if "expected_total" not in body or body["expected_total"] is None:
        return True, None
    value = body["expected_total"]
    # bool は int のサブクラスなので、True/False を整数として受け付けないよう除外する
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return False, None
    return True, value


def _purchase(buyer_id, chatbot_ids, expected_total):
    try:
        response = supabase.rpc(
            "purchase_chatbots",
            {
                "p_buyer_id": buyer_id,
                "p_chatbot_ids": chatbot_ids,
                "p_expected_total": expected_total,
            },
        ).execute()
    except APIError as e:
        error = PURCHASE_ERRORS.get(getattr(e, "message", None))
        if error is None:
            raise
        status, message = error
        return jsonify({"error": message}), status

    return jsonify(response.data), 201


def _read_body():
    body = request.get_json(silent=True)
    return body if isinstance(body, dict) else {}


@purchases_bp.post("/cart")
def purchase_cart():
    """カート内の商品をまとめて購入する"""
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    ok, expected_total = _parse_expected_total(_read_body())
    if not ok:
        return jsonify({"error": INVALID_TOTAL_ERROR}), 400

    return _purchase(current_user["user_id"], None, expected_total)


@purchases_bp.post("")
def purchase_product():
    """指定した商品を1つ購入する"""
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    body = _read_body()
    chatbot_id = _normalize_chatbot_id(body.get("chatbot_id"))
    if chatbot_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    ok, expected_total = _parse_expected_total(body)
    if not ok:
        return jsonify({"error": INVALID_TOTAL_ERROR}), 400

    return _purchase(current_user["user_id"], [chatbot_id], expected_total)
