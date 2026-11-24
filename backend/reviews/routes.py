import uuid
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request

from common.auth_helper import get_current_user
from common.supabase_client import supabase

# 商品に対するレビューなので、URLは /api/products/<chatbot_id>/... に置く
reviews_bp = Blueprint("reviews", __name__)

LOGIN_REQUIRED_ERROR = "ログインが必要です"
INVALID_ID_ERROR = "無効なchatbot_idです"
PRODUCT_NOT_FOUND_ERROR = "商品が見つかりません"
NOT_PURCHASED_ERROR = "購入した商品のみレビューできます"
REVIEW_NOT_FOUND_ERROR = "レビューが見つかりません"

RATING_MIN = 1
RATING_MAX = 5
RATING_ERROR = f"rating は{RATING_MIN}〜{RATING_MAX}の整数で指定してください"

MAX_COMMENT_LENGTH = 1000
COMMENT_ERROR = f"comment は{MAX_COMMENT_LENGTH}文字以内の文字列で指定してください"

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
PAGING_ERROR = f"limit は1〜{MAX_LIMIT}、offset は0以上の整数で指定してください"

REVIEW_COLUMNS = "rating, comment, reviewed_at"


def _normalize_chatbot_id(value):
    """UUIDとして正しければ正規化した文字列、正しくなければNoneを返す"""
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _parse_int(value, default):
    """未指定ならdefault、整数ならその値、整数でなければNoneを返す"""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return None


def _parse_rating(value):
    """1〜5の整数ならその値、それ以外はNoneを返す"""
    # bool は int のサブクラスなので、True/False を整数として受け付けないよう除外する
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    if not (RATING_MIN <= value <= RATING_MAX):
        return None
    return value


def _parse_comment(value):
    """
    本文は任意。(True, 保存する値) か、不正なら (False, None) を返す。
    未指定・null・空白だけの場合は本文なしとして None を保存する。
    """
    if value is None:
        return True, None
    if not isinstance(value, str):
        return False, None
    value = value.strip()
    if len(value) > MAX_COMMENT_LENGTH:
        return False, None
    return True, value or None


def _to_review(row):
    return {
        "rating": row["rating"],
        "comment": row["comment"],
        "reviewed_at": row["reviewed_at"],
    }


def _own_purchases(table_query, user_id, chatbot_id):
    """ログイン中のユーザーが、指定した商品を購入した記録に絞り込む"""
    # purchases.is_deleted は履歴の非表示用なので、レビューできるかの判定には使わない
    return table_query.eq("buyer_id", user_id).eq("chatbot_id", chatbot_id)


@reviews_bp.get("/<chatbot_id>/reviews")
def list_reviews(chatbot_id):
    """商品のレビュー一覧(平均評価・件数つき)。ログイン不要"""
    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    limit = _parse_int(request.args.get("limit"), DEFAULT_LIMIT)
    offset = _parse_int(request.args.get("offset"), 0)
    if limit is None or offset is None or not (1 <= limit <= MAX_LIMIT) or offset < 0:
        return jsonify({"error": PAGING_ERROR}), 400

    response = supabase.rpc(
        "get_product_reviews",
        {"p_chatbot_id": normalized_id, "p_limit": limit, "p_offset": offset},
    ).execute()

    # 出品中でない・出品者が退会済みの商品は、関数が null を返す
    if response.data is None:
        return jsonify({"error": PRODUCT_NOT_FOUND_ERROR}), 404

    return jsonify(response.data)


@reviews_bp.get("/<chatbot_id>/review")
def get_my_review(chatbot_id):
    """
    ログイン中のユーザー自身のレビュー。
    レビュー投稿フォームの表示(購入済みか・既存のレビューの初期値)に使う。
    """
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    response = (
        _own_purchases(
            supabase.table("purchases").select(REVIEW_COLUMNS),
            current_user["user_id"],
            normalized_id,
        )
        .limit(1)
        .execute()
    )

    if not response.data:
        return jsonify({"purchased": False, "review": None})

    row = response.data[0]
    review = _to_review(row) if row["rating"] is not None else None
    return jsonify({"purchased": True, "review": review})


@reviews_bp.put("/<chatbot_id>/review")
def put_review(chatbot_id):
    """購入した商品のレビューを投稿する。すでに投稿済みなら内容を上書きする"""
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        body = {}

    rating = _parse_rating(body.get("rating"))
    if rating is None:
        return jsonify({"error": RATING_ERROR}), 400

    ok, comment = _parse_comment(body.get("comment"))
    if not ok:
        return jsonify({"error": COMMENT_ERROR}), 400

    now = datetime.now(timezone.utc).isoformat()
    response = _own_purchases(
        supabase.table("purchases").update(
            {"rating": rating, "comment": comment, "reviewed_at": now, "update_at": now}
        ),
        current_user["user_id"],
        normalized_id,
    ).execute()

    # 更新された行が無い = この商品を購入していない
    if not response.data:
        return jsonify({"error": NOT_PURCHASED_ERROR}), 403

    return jsonify(_to_review(response.data[0]))


@reviews_bp.delete("/<chatbot_id>/review")
def delete_review(chatbot_id):
    """自分のレビューを取り消す(購入記録は残す)"""
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": LOGIN_REQUIRED_ERROR}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    now = datetime.now(timezone.utc).isoformat()
    response = (
        _own_purchases(
            supabase.table("purchases").update(
                {"rating": None, "comment": None, "reviewed_at": None, "update_at": now}
            ),
            current_user["user_id"],
            normalized_id,
        )
        .not_.is_("rating", "null")
        .execute()
    )

    if not response.data:
        return jsonify({"error": REVIEW_NOT_FOUND_ERROR}), 404

    return "", 204
