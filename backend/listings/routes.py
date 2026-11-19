from datetime import datetime, timezone
import uuid
from urllib.parse import unquote, urlparse

from flask import Blueprint, current_app, jsonify, request

from common.auth_helper import get_current_user
from common.supabase_client import supabase


listings_bp = Blueprint("listings", __name__)

THUMBNAIL_BUCKET = "chatbot_thumbnails"
MAX_THUMBNAIL_SIZE = 5 * 1024 * 1024
MAX_BOT_NAME_LENGTH = 40
MAX_DESCRIPTION_LENGTH = 5000
MAX_PRICE = 2_147_483_647

BOT_COLUMNS = (
    "chatbot_id, bot_name, creator_id, price, description, "
    "category_id, thumbnail_url, is_listed"
)
CATEGORY_COLUMNS = "category_id, category_name"


def _normalize_chatbot_id(value):
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _find_owned_bot(chatbot_id, user_id):
    response = (
        supabase.table("chatbot")
        .select(BOT_COLUMNS)
        .eq("chatbot_id", chatbot_id)
        .eq("creator_id", user_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def _list_categories():
    response = (
        supabase.table("category")
        .select(CATEGORY_COLUMNS)
        .order("category_id")
        .execute()
    )
    return response.data


def _parse_form(body):
    bot_name = (body.get("bot_name") or "").strip()
    if not bot_name:
        return None, "商品名は必須です"
    if len(bot_name) > MAX_BOT_NAME_LENGTH:
        return None, f"商品名は{MAX_BOT_NAME_LENGTH}文字以内で入力してください"

    description = (body.get("description") or "").strip()
    if not description:
        return None, "説明文は必須です"
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return None, f"説明文は{MAX_DESCRIPTION_LENGTH}文字以内で入力してください"

    price_text = (body.get("price") or "").strip()
    try:
        price = int(price_text)
    except (TypeError, ValueError):
        return None, "販売価格は1円以上の整数で指定してください"
    if str(price) != price_text or not (1 <= price <= MAX_PRICE):
        return None, "販売価格は1円以上の整数で指定してください"

    category_text = (body.get("category_id") or "").strip()
    try:
        category_id = int(category_text)
    except (TypeError, ValueError):
        return None, "カテゴリを選択してください"
    if str(category_id) != category_text or category_id < 1:
        return None, "カテゴリを選択してください"

    return {
        "bot_name": bot_name,
        "description": description,
        "price": price,
        "category_id": category_id,
    }, None


def _read_thumbnail(file):
    if file is None or not file.filename:
        return None

    file_bytes = file.read(MAX_THUMBNAIL_SIZE + 1)
    if not file_bytes:
        raise ValueError("サムネイル画像が空です")
    if len(file_bytes) > MAX_THUMBNAIL_SIZE:
        raise ValueError("サムネイル画像は5MB以内にしてください")

    if file_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        return file_bytes, "image/png", "png"
    if file_bytes.startswith(b"\xff\xd8\xff"):
        return file_bytes, "image/jpeg", "jpg"
    if (
        len(file_bytes) >= 12
        and file_bytes[:4] == b"RIFF"
        and file_bytes[8:12] == b"WEBP"
    ):
        return file_bytes, "image/webp", "webp"

    raise ValueError("サムネイル画像はJPEG、PNG、WebP形式で指定してください")


def _category_exists(category_id):
    response = (
        supabase.table("category")
        .select("category_id")
        .eq("category_id", category_id)
        .limit(1)
        .execute()
    )
    return bool(response.data)


def _upload_thumbnail(chatbot_id, thumbnail):
    file_bytes, content_type, extension = thumbnail
    file_path = f"{chatbot_id}/{uuid.uuid4()}.{extension}"
    supabase.storage.from_(THUMBNAIL_BUCKET).upload(
        file_path,
        file_bytes,
        {"content-type": content_type},
    )
    public_url = supabase.storage.from_(THUMBNAIL_BUCKET).get_public_url(file_path)
    return file_path, public_url


def _thumbnail_path_from_url(url, chatbot_id):
    """このBotの公開サムネイルURLから、Storage内のパスを取り出す。"""
    if not url:
        return None

    marker = f"/storage/v1/object/public/{THUMBNAIL_BUCKET}/"
    path = unquote(urlparse(url).path)
    if marker not in path:
        return None

    file_path = path.split(marker, 1)[1]
    if not file_path.startswith(f"{chatbot_id}/"):
        return None
    return file_path


def _remove_thumbnail(file_path):
    if not file_path:
        return
    try:
        supabase.storage.from_(THUMBNAIL_BUCKET).remove([file_path])
    except Exception:
        current_app.logger.exception("サムネイル画像の削除に失敗しました")


def _storage_error_response(message, error):
    current_app.logger.exception(message)
    body = {"error": message}
    if current_app.debug:
        body["detail"] = str(error)
    return jsonify(body), 500


@listings_bp.get("/<chatbot_id>")
def get_listing(chatbot_id):
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": "ログインが必要です"}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": "無効なchatbot_idです"}), 400

    bot = _find_owned_bot(normalized_id, current_user["user_id"])
    if bot is None:
        return jsonify({"error": "出品できるチャットボットが見つかりません"}), 404

    return jsonify({"chatbot": bot, "categories": _list_categories()})


@listings_bp.put("/<chatbot_id>")
def publish_listing(chatbot_id):
    current_user = get_current_user()
    if current_user is None:
        return jsonify({"error": "ログインが必要です"}), 401

    normalized_id = _normalize_chatbot_id(chatbot_id)
    if normalized_id is None:
        return jsonify({"error": "無効なchatbot_idです"}), 400

    bot = _find_owned_bot(normalized_id, current_user["user_id"])
    if bot is None:
        return jsonify({"error": "出品できるチャットボットが見つかりません"}), 404

    values, error = _parse_form(request.form)
    if error:
        return jsonify({"error": error}), 400

    if not _category_exists(values["category_id"]):
        return jsonify({"error": "指定されたカテゴリが見つかりません"}), 400

    try:
        thumbnail = _read_thumbnail(request.files.get("thumbnail"))
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    uploaded_path = None
    old_thumbnail_path = None
    if thumbnail is not None:
        try:
            uploaded_path, public_url = _upload_thumbnail(normalized_id, thumbnail)
        except Exception as error:
            return _storage_error_response(
                "サムネイル画像の保存に失敗しました", error
            )
        values["thumbnail_url"] = public_url
        old_thumbnail_path = _thumbnail_path_from_url(
            bot.get("thumbnail_url"), normalized_id
        )

    values["is_listed"] = True
    values["update_at"] = datetime.now(timezone.utc).isoformat()

    try:
        response = (
            supabase.table("chatbot")
            .update(values)
            .eq("chatbot_id", normalized_id)
            .eq("creator_id", current_user["user_id"])
            .execute()
        )
    except Exception:
        current_app.logger.exception("出品情報の保存に失敗しました")
        _remove_thumbnail(uploaded_path)
        return jsonify({"error": "出品情報の保存に失敗しました"}), 500

    if not response.data:
        current_app.logger.error("出品情報の更新結果が空でした")
        _remove_thumbnail(uploaded_path)
        return jsonify({"error": "出品情報の保存に失敗しました"}), 500

    if uploaded_path and old_thumbnail_path and old_thumbnail_path != uploaded_path:
        _remove_thumbnail(old_thumbnail_path)

    return jsonify(response.data[0])
