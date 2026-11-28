import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from postgrest.exceptions import APIError

from common.auth_helper import get_current_user
from common.supabase_client import supabase


users_bp = Blueprint("users", __name__)

USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_]{2,19}$")
MAX_USERNAME_LENGTH = 20
MAX_PROFILE_LENGTH = 160
PROFILE_COLUMNS = (
    "user_id, username, profile_image_url, developer_profile, create_at"
)


def _valid_user_id(user_id):
    return isinstance(user_id, str) and USER_ID_PATTERN.fullmatch(user_id) is not None


def _find_user(user_id):
    response = (
        supabase.table("users")
        .select(PROFILE_COLUMNS)
        .eq("user_id", user_id)
        .eq("is_withdrawn", False)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _get_created_bots(user_id):
    response = (
        supabase.table("chatbot")
        .select("chatbot_id, is_listed")
        .eq("creator_id", user_id)
        .execute()
    )
    return response.data


def _get_sales_count(chatbot_ids):
    if not chatbot_ids:
        return 0
    response = (
        supabase.table("purchases")
        .select("purchase_id")
        .in_("chatbot_id", chatbot_ids)
        .execute()
    )
    return len(response.data)


def _get_arena_stats(chatbot_ids):
    if not chatbot_ids:
        return 0, 0

    id_list = ",".join(chatbot_ids)
    response = (
        supabase.table("bot_arena")
        .select("bot_a_id, bot_b_id, bot_winner_id")
        .or_(f"bot_a_id.in.({id_list}),bot_b_id.in.({id_list})")
        .execute()
    )

    owned_ids = set(chatbot_ids)
    wins = 0
    losses = 0
    for battle in response.data:
        winner_id = battle.get("bot_winner_id")
        if winner_id in owned_ids:
            wins += 1

        loser_id = (
            battle.get("bot_b_id")
            if winner_id == battle.get("bot_a_id")
            else battle.get("bot_a_id")
        )
        if loser_id in owned_ids:
            losses += 1

    return wins, losses


def _get_purchase_count(user_id):
    response = (
        supabase.table("purchases")
        .select("purchase_id")
        .eq("buyer_id", user_id)
        .eq("is_deleted", False)
        .execute()
    )
    return len(response.data)


def _get_coin_balance(user_id):
    response = supabase.rpc("get_coin_balance", {"p_user_id": user_id}).execute()
    return response.data or 0


def _build_profile(user, current_user):
    user_id = user["user_id"]
    is_self = current_user is not None and current_user["user_id"] == user_id
    bots = _get_created_bots(user_id)
    chatbot_ids = [bot["chatbot_id"] for bot in bots]
    wins, losses = _get_arena_stats(chatbot_ids)

    profile = {
        "user_id": user_id,
        "username": user["username"],
        "developer_profile": user.get("developer_profile"),
        "profile_image_url": user.get("profile_image_url"),
        "created_at": user["create_at"],
        "is_self": is_self,
        "stats": {
            "listed_count": sum(bool(bot.get("is_listed")) for bot in bots),
            "sold_count": _get_sales_count(chatbot_ids),
            "wins": wins,
            "losses": losses,
        },
    }

    # 購入履歴と残高は本人の画面にだけ表示する情報なので、他人には返さない。
    if is_self:
        profile["purchase_count"] = _get_purchase_count(user_id)
        profile["coin_balance"] = _get_coin_balance(user_id)

    return profile


def _read_update_values():
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return None, "更新内容を指定してください"

    username = body.get("username")
    if not isinstance(username, str) or not username.strip():
        return None, "表示名を入力してください"
    username = username.strip()
    if len(username) > MAX_USERNAME_LENGTH:
        return None, f"表示名は{MAX_USERNAME_LENGTH}文字以内で入力してください"

    developer_profile = body.get("developer_profile")
    if developer_profile is not None and not isinstance(developer_profile, str):
        return None, "自己紹介は文字列で指定してください"
    developer_profile = (developer_profile or "").strip()
    if len(developer_profile) > MAX_PROFILE_LENGTH:
        return None, f"自己紹介は{MAX_PROFILE_LENGTH}文字以内で入力してください"

    return {
        "username": username,
        "developer_profile": developer_profile or None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }, None


@users_bp.get("/health")
def health():
    return jsonify({"status": "ok", "domain": "users"})


@users_bp.get("/<user_id>")
def get_profile(user_id):
    if not _valid_user_id(user_id):
        return jsonify({"error": "ユーザーが見つかりません"}), 404

    user = _find_user(user_id)
    if user is None:
        return jsonify({"error": "ユーザーが見つかりません"}), 404

    return jsonify(_build_profile(user, get_current_user()))


@users_bp.patch("/<user_id>")
def update_profile(user_id):
    if not _valid_user_id(user_id):
        return jsonify({"error": "ユーザーが見つかりません"}), 404

    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": "ログインが必要です"}), 401
    if current_user["user_id"] != user_id:
        return jsonify({"error": "他のユーザーのプロフィールは編集できません"}), 403

    values, error = _read_update_values()
    if error:
        return jsonify({"error": error}), 400

    try:
        response = (
            supabase.table("users")
            .update(values)
            .eq("user_id", user_id)
            .eq("is_withdrawn", False)
            .execute()
        )
    except APIError as exception:
        if getattr(exception, "code", None) == "23505":
            return jsonify({"error": "この表示名は既に使用されています"}), 409
        raise

    if not response.data:
        return jsonify({"error": "ユーザーが見つかりません"}), 404

    updated_user = response.data[0]
    return jsonify(
        {
            "username": updated_user["username"],
            "developer_profile": updated_user.get("developer_profile"),
        }
    )
