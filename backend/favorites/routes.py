
import uuid

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from common.auth_helper import get_current_user
from common.supabase_client import supabase

favorites_bp = Blueprint("favorites", __name__)

UNIQUE_VIOLATION = "23505"

LOGIN_REQUIRED_ERROR = "ログインが必要です"
INVALID_ID_ERROR = "無効なchatbot_idです"

# お気に入りと商品・出品者の情報をまとめて取得する
FAVORITE_COLUMNS = (
    "chatbot_id, create_at, "
    "chatbot!inner(bot_name, price, description, thumbnail_url, "
    "users!chatbot_creator_id_fkey!inner(username), "
    "category(category_name))"
)


def _normalize_chatbot_id(value):
    """UUIDとして正しい値なら正規化して返す"""
    if not isinstance(value, str):
        return None

    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _to_favorite_item(row):
    """DBのデータをAPIの返却形式に変換する"""
    chatbot = row.get("chatbot") or {}

    return {
        "chatbot_id": row["chatbot_id"],
        "bot_name": chatbot.get("bot_name"),
        "price": chatbot.get("price"),
        "description": chatbot.get("description"),
        "thumbnail_url": chatbot.get("thumbnail_url"),
        "username": (chatbot.get("users") or {}).get("username"),
        "category_name": (chatbot.get("category") or {}).get("category_name"),
        "added_at": row["create_at"],
    }


# =====================================
# GET /api/favorites
# お気に入り一覧
# =====================================
@favorites_bp.get("")
def get_favorites():

    current_user = get_current_user()

    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    response = (
        supabase.table("favorite_bot")
        .select(FAVORITE_COLUMNS)
        .eq("user_id", current_user["user_id"])
        .eq("chatbot.is_listed", True)
        .eq("chatbot.users.is_withdrawn", False)
        .order("create_at", desc=True)
        .execute()
    )

    return jsonify([
        _to_favorite_item(row)
        for row in response.data
    ])


# =====================================
# POST /api/favorites
# お気に入り登録
# =====================================
@favorites_bp.post("")
def add_favorite():

    current_user = get_current_user()

    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    body = request.get_json(silent=True) or {}

    chatbot_id = _normalize_chatbot_id(
        body.get("chatbot_id") if isinstance(body, dict) else None
    )

    if chatbot_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    # 商品が出品中で、出品者が退会していないか確認
    product = (
        supabase.table("chatbot")
        .select(
            "chatbot_id, "
            "users!chatbot_creator_id_fkey!inner(is_withdrawn)"
        )
        .eq("chatbot_id", chatbot_id)
        .eq("is_listed", True)
        .eq("users.is_withdrawn", False)
        .execute()
    )

    if not product.data:
        return jsonify({"error": "商品が見つかりません"}), 404

    try:
        supabase.table("favorite_bot").insert({
            "chatbot_id": chatbot_id,
            "user_id": current_user["user_id"]
        }).execute()

    except APIError as e:
        if getattr(e, "code", None) == UNIQUE_VIOLATION:
            return jsonify({
                "error": "この商品は既にお気に入りに登録されています"
            }), 409

        raise

    return jsonify({"chatbot_id": chatbot_id}), 201


# =====================================
# DELETE /api/favorites/<chatbot_id>
# お気に入り解除
# =====================================
@favorites_bp.delete("/<chatbot_id>")
def remove_favorite(chatbot_id):

    current_user = get_current_user()

    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)

    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    response = (
        supabase.table("favorite_bot")
        .delete()
        .eq("user_id", current_user["user_id"])
        .eq("chatbot_id", normalized_id)
        .execute()
    )

    if not response.data:
        return jsonify({
            "error": "お気に入りにこの商品はありません"
        }), 404

    return jsonify({"chatbot_id": normalized_id})