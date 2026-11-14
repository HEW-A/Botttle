import uuid

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from common.auth_helper import get_current_user
from common.supabase_client import supabase

cart_bp = Blueprint("cart", __name__)

# cart から chatbot を結合し、商品一覧APIと同じ項目を返す。
# chatbot → users は cart / favorite_bot 経由の関係とも解釈できて曖昧になるため、
# 外部キー名を明示する。
# !inner にすると、出品停止中・出品者が退会済みの商品は結合の段階で除外される。
CART_COLUMNS = (
    "chatbot_id, create_at, "
    "chatbot!inner(bot_name, price, description, thumbnail_url, "
    "users!chatbot_creator_id_fkey!inner(username), "
    "category(category_name))"
)

# PostgreSQL の UNIQUE 制約違反のエラーコード
UNIQUE_VIOLATION = "23505"

LOGIN_REQUIRED_ERROR = "ログインが必要です"
INVALID_ID_ERROR = "無効なchatbot_idです"


def _normalize_chatbot_id(value):
    """UUIDとして正しければ正規化した文字列、正しくなければNoneを返す"""
    if not isinstance(value, str):
        return None
    try:
        # urn:uuid: 形式やハイフンなしもUUIDとして通るため、
        # 正規化した文字列をクエリに使う(元の文字列は渡さない)
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _to_cart_item(row):
    """DBの1行を、APIで返す辞書に変換する"""
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


@cart_bp.get("")
def get_cart():
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    response = (
        supabase.table("cart")
        .select(CART_COLUMNS)
        .eq("user_id", current_user["user_id"])
        .eq("chatbot.is_listed", True)
        .eq("chatbot.users.is_withdrawn", False)
        .order("create_at", desc=True)
        .execute()
    )
    return jsonify([_to_cart_item(row) for row in response.data])


@cart_bp.post("")
def add_to_cart():
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    body = request.get_json(silent=True) or {}
    chatbot_id = _normalize_chatbot_id(body.get("chatbot_id") if isinstance(body, dict) else None)
    if chatbot_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    # 商品一覧に出ていない商品でも、APIを直接呼べば追加できてしまうため、
    # 出品中で出品者が退会していないことをここでも確認する
    product = (
        supabase.table("chatbot")
        .select("chatbot_id, creator_id, users!chatbot_creator_id_fkey!inner(is_withdrawn)")
        .eq("chatbot_id", chatbot_id)
        .eq("is_listed", True)
        .eq("users.is_withdrawn", False)
        .execute()
    )
    if not product.data:
        return jsonify({"error": "商品が見つかりません"}), 404

    if product.data[0]["creator_id"] == current_user["user_id"]:
        return jsonify({"error": "自分の商品はカートに入れられません"}), 400

    # チャットボットは利用権の購入なので、一度買ったものは再購入させない。
    # purchases.is_deleted は購入履歴を画面で非表示にするためだけのフラグで、
    # 返金・購入取り消しは存在しないため、is_deleted に関係なく購入済みとして扱う。
    purchased = (
        supabase.table("purchases")
        .select("purchase_id")
        .eq("buyer_id", current_user["user_id"])
        .eq("chatbot_id", chatbot_id)
        .limit(1)
        .execute()
    )
    if purchased.data:
        return jsonify({"error": "この商品はすでに購入済みです"}), 400

    try:
        supabase.table("cart").insert(
            {"chatbot_id": chatbot_id, "user_id": current_user["user_id"]}
        ).execute()
    except APIError as e:
        # (user_id, chatbot_id) の UNIQUE 制約で二重追加を防いでいる
        if getattr(e, "code", None) == UNIQUE_VIOLATION:
            return jsonify({"error": "この商品はすでにカートに入っています"}), 409
        raise

    return jsonify({"chatbot_id": chatbot_id}), 201


@cart_bp.delete("/<chatbot_id>")
def remove_from_cart(chatbot_id):
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    response = (
        supabase.table("cart")
        .delete()
        .eq("user_id", current_user["user_id"])
        .eq("chatbot_id", normalized_id)
        .execute()
    )
    if not response.data:
        return jsonify({"error": "カートにこの商品はありません"}), 404

    return jsonify({"chatbot_id": normalized_id})


@cart_bp.delete("")
def clear_cart():
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    response = (
        supabase.table("cart")
        .delete()
        .eq("user_id", current_user["user_id"])
        .execute()
    )
    return jsonify({"deleted_count": len(response.data)})
