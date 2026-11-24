from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import uuid

from flask import Blueprint, jsonify, request

from common.auth_helper import get_current_user
from common.supabase_client import supabase


reviews_bp = Blueprint("reviews", __name__)

REVIEW_COLUMNS = (
    "purchase_id, rating, comment, update_at, "
    "users!purchases_buyer_id_fkey(username)"
)
MY_REVIEW_COLUMNS = "purchase_id, rating, comment, update_at"

MIN_RATING = Decimal("1")
MAX_RATING = Decimal("5")
MAX_COMMENT_LENGTH = 1000

INVALID_ID_ERROR = "無効なchatbot_idです"
LOGIN_REQUIRED_ERROR = "ログインが必要です"
INVALID_RATING_ERROR = "rating は1〜5の整数で指定してください"


def _normalize_chatbot_id(value):
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _encode_rating(value):
    """1〜5の整数評価だけをDBのinteger列へ保存できる形にする。"""
    if isinstance(value, bool):
        return None
    try:
        rating = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None

    if not rating.is_finite() or rating < MIN_RATING or rating > MAX_RATING:
        return None
    if rating != rating.to_integral_value():
        return None
    return int(rating)


def _decode_rating(value):
    if value is None:
        return None
    return int(value)


def _to_review(row):
    return {
        "purchase_id": row["purchase_id"],
        "username": (row.get("users") or {}).get("username"),
        "rating": _decode_rating(row.get("rating")),
        "comment": row.get("comment"),
        "updated_at": row.get("update_at"),
    }


def _to_my_review(row):
    if row.get("rating") is None:
        return None
    return {
        "purchase_id": row["purchase_id"],
        "rating": _decode_rating(row["rating"]),
        "comment": row.get("comment") or "",
        "updated_at": row.get("update_at"),
    }


def _find_purchase(chatbot_id, user_id):
    response = (
        supabase.table("purchases")
        .select(MY_REVIEW_COLUMNS)
        .eq("buyer_id", user_id)
        .eq("chatbot_id", chatbot_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


@reviews_bp.get("/<chatbot_id>")
def get_reviews(chatbot_id):
    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    response = (
        supabase.table("purchases")
        .select(REVIEW_COLUMNS)
        .eq("chatbot_id", normalized_id)
        .execute()
    )
    reviews = [
        _to_review(row)
        for row in response.data
        if row.get("rating") is not None and (row.get("comment") or "").strip()
    ]
    average_rating = None
    if reviews:
        average_rating = round(
            sum(review["rating"] for review in reviews) / len(reviews), 1
        )

    return jsonify(
        {
            "average_rating": average_rating,
            "review_count": len(reviews),
            "reviews": reviews,
        }
    )


@reviews_bp.get("/<chatbot_id>/mine")
def get_my_review(chatbot_id):
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    purchase = _find_purchase(normalized_id, current_user["user_id"])
    if purchase is None:
        return jsonify({"can_review": False, "review": None})

    return jsonify({"can_review": True, "review": _to_my_review(purchase)})


@reviews_bp.put("/<chatbot_id>")
def save_review(chatbot_id):
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        body = {}

    encoded_rating = _encode_rating(body.get("rating"))
    if encoded_rating is None:
        return jsonify({"error": INVALID_RATING_ERROR}), 400

    comment = body.get("comment")
    if not isinstance(comment, str) or not comment.strip():
        return jsonify({"error": "comment は必須です"}), 400
    comment = comment.strip()
    if len(comment) > MAX_COMMENT_LENGTH:
        return jsonify(
            {"error": f"comment は{MAX_COMMENT_LENGTH}文字以内で入力してください"}
        ), 400

    purchase = _find_purchase(normalized_id, current_user["user_id"])
    if purchase is None:
        return jsonify({"error": "購入したボットのみ評価できます"}), 403

    updated_at = datetime.now(timezone.utc).isoformat()
    response = (
        supabase.table("purchases")
        .update(
            {
                "rating": encoded_rating,
                "comment": comment,
                "update_at": updated_at,
            }
        )
        .eq("purchase_id", purchase["purchase_id"])
        .eq("buyer_id", current_user["user_id"])
        .execute()
    )
    if not response.data:
        return jsonify({"error": "レビューの保存に失敗しました"}), 500

    saved = response.data[0]
    return jsonify(
        {
            "purchase_id": saved["purchase_id"],
            "rating": _decode_rating(saved["rating"]),
            "comment": saved["comment"],
            "updated_at": saved.get("update_at"),
        }
    )
