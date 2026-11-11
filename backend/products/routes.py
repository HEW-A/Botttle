import re
import uuid

from flask import Blueprint, jsonify, request

from common.supabase_client import supabase

products_bp = Blueprint("products", __name__)

# users は cart / favorite_bot などを経由した関係とも解釈できて曖昧になるため、
# chatbot.creator_id の外部キー名を明示する。
# !inner にすると、退会済みユーザーの行は結合の段階で除外される。
PRODUCT_COLUMNS = (
    "chatbot_id, bot_name, price, description, thumbnail_url, category_id, "
    "users!chatbot_creator_id_fkey!inner(username), "
    "category(category_name)"
)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
PAGING_ERROR = f"limit は1〜{MAX_LIMIT}、offset は0以上の整数で指定してください"

# category.category_id は smallint で、1から採番される
CATEGORY_ID_MIN = 1
CATEGORY_ID_MAX = 32767
CATEGORY_ID_ERROR = f"category_id は{CATEGORY_ID_MIN}〜{CATEGORY_ID_MAX}の整数で指定してください"
# 半角数字だけを許可する(前後の空白・符号・小数点は400にする)
CATEGORY_ID_PATTERN = re.compile(r"[0-9]+")

SEARCH_MAX_LENGTH = 60


def _to_product(row):
    """DBの1行を、APIで返す8項目の辞書に変換する"""
    return {
        "chatbot_id": row["chatbot_id"],
        "bot_name": row["bot_name"],
        "price": row["price"],
        "description": row["description"],
        "thumbnail_url": row["thumbnail_url"],
        "category_id": row.get("category_id"),
        "username": (row.get("users") or {}).get("username"),
        "category_name": (row.get("category") or {}).get("category_name"),
    }


def _parse_int(value, default):
    """未指定ならdefault、整数ならその値、整数でなければNoneを返す"""
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return None


def _parse_category_id(value):
    """
    未指定ならNone、正しい値ならint、不正な値なら False を返す。
    DBの smallint の範囲外をそのまま渡すとDB側で500になるため、ここで止める。
    """
    if value is None:
        return None
    if not CATEGORY_ID_PATTERN.fullmatch(value):
        return False
    number = int(value)
    if not (CATEGORY_ID_MIN <= number <= CATEGORY_ID_MAX):
        return False
    return number


def _search_words(value):
    """
    検索キーワードを単語のリストにする。検索しない場合は空リストを返す。
    - * はPostgRESTで「何でも一致」に変換されるため取り除いて前後をつなげる
    - 前後の半角スペースを消してから60文字で切る
    - 半角スペースだけを区切りにする(全角スペースはただの文字)
    """
    if value is None:
        return []
    keyword = value.replace("*", "").strip(" ")[:SEARCH_MAX_LENGTH]
    return [word for word in keyword.split(" ") if word]


def _like_value(word):
    """
    単語を、部分一致検索用のPostgRESTの値にする。
    1. LIKEで特別な意味を持つ \\ % _ をエスケープして、ただの文字にする
    2. 前後に * を付けて部分一致にする(PostgRESTが % に変換する)
    3. , ( ) などを含んでも壊れないよう、ダブルクォートで囲む
    """
    escaped = word.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"*{escaped}*"
    quoted = pattern.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{quoted}"'


def _search_filter(words):
    """
    全単語を含む(AND)、各単語はBot名か説明文のどちらかに含む(OR)条件を作る。
    or_ に1条件だけ渡すことで、1つのクエリパラメータにまとめている。
    """
    conditions = ",".join(
        f"or(bot_name.ilike.{_like_value(w)},description.ilike.{_like_value(w)})"
        for w in words
    )
    return f"and({conditions})"


def _listed_products_query():
    """出品中で、出品者が退会していない商品のクエリ(一覧・詳細で共通)"""
    return (
        supabase.table("chatbot")
        .select(PRODUCT_COLUMNS)
        .eq("is_listed", True)
        .eq("users.is_withdrawn", False)
    )


@products_bp.route("")
def list_products():
    limit = _parse_int(request.args.get("limit"), DEFAULT_LIMIT)
    offset = _parse_int(request.args.get("offset"), 0)

    if limit is None or offset is None or not (1 <= limit <= MAX_LIMIT) or offset < 0:
        return jsonify({"error": PAGING_ERROR}), 400

    category_id = _parse_category_id(request.args.get("category_id"))
    if category_id is False:
        return jsonify({"error": CATEGORY_ID_ERROR}), 400

    words = _search_words(request.args.get("q"))

    query = _listed_products_query()
    if category_id is not None:
        # 存在しないIDの場合は、該当なしとして [] が返る
        query = query.eq("category_id", category_id)
    if words:
        query = query.or_(_search_filter(words))

    response = (
        query.order("create_at", desc=True)
        .order("chatbot_id", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return jsonify([_to_product(row) for row in response.data])


@products_bp.route("/<chatbot_id>")
def get_product(chatbot_id):
    try:
        # urn:uuid: 形式やハイフンなしもUUIDとして通るため、
        # 正規化した文字列をクエリに使う(元の文字列は渡さない)
        normalized_id = str(uuid.UUID(chatbot_id))
    except ValueError:
        return jsonify({"error": "無効なchatbot_idです"}), 400

    response = _listed_products_query().eq("chatbot_id", normalized_id).execute()
    if not response.data:
        return jsonify({"error": "商品が見つかりません"}), 404

    return jsonify(_to_product(response.data[0]))