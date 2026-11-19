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

MAX_QUERY_LENGTH = 100
MAX_TERMS = 10
QUERY_TOO_LONG_ERROR = f"検索キーワードは{MAX_QUERY_LENGTH}文字以内で指定してください"
TOO_MANY_TERMS_ERROR = f"検索キーワードは{MAX_TERMS}語以内で指定してください"

# category.category_id は smallint で、1から採番される
CATEGORY_ID_MIN = 1
CATEGORY_ID_MAX = 32767
CATEGORY_ID_ERROR = f"category_id は{CATEGORY_ID_MIN}〜{CATEGORY_ID_MAX}の整数で指定してください"
# 半角数字だけを許可する(後ろの空白・符号・小数点・全角は400にする)
CATEGORY_ID_PATTERN = re.compile(r"[0-9]+")


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
    指定なしならNone、正しい値ならint、不正な値なら False を返す。
    - 未指定・空・半角スペースだけ(何個でも)は、指定なしとして扱う
    - 先頭の半角スペース1個だけは無視する(" 1" は 1)
    - 先頭に2個以上、後ろに空白、全角スペースなどは不正(400)
    DBの smallint の範囲外をそのまま渡すとDB側で500になるため、ここで止める。
    """
    if value is None or value.strip(" ") == "":
        return None
    if value.startswith(" "):
        value = value[1:]
    if not CATEGORY_ID_PATTERN.fullmatch(value):
        return False
    number = int(value)
    if not (CATEGORY_ID_MIN <= number <= CATEGORY_ID_MAX):
        return False
    return number


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

    # 検索フォームの送信時に q 付きで呼ばれる。未指定・空白だけなら通常の一覧を返す
    keyword = request.args.get("q", "").strip()
    if keyword:
        return _search_products(keyword, category_id, limit, offset)

    query = _listed_products_query()
    if category_id is not None:
        # 存在しないIDの場合は、該当なしとして [] が返る
        query = query.eq("category_id", category_id)

    response = (
        query.order("create_at", desc=True)
        .order("chatbot_id", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return jsonify([_to_product(row) for row in response.data])


def _split_terms(query):
    """空白(全角スペースも含む)で区切り、大文字・小文字違いの重複を除いた語のリストを返す"""
    terms = {}
    for term in query.split():
        terms.setdefault(term.lower(), term)
    return list(terms.values())


def _search_products(query, category_id, limit, offset):
    if len(query) > MAX_QUERY_LENGTH:
        return jsonify({"error": QUERY_TOO_LONG_ERROR}), 400

    terms = _split_terms(query)
    if len(terms) > MAX_TERMS:
        return jsonify({"error": TOO_MANY_TERMS_ERROR}), 400

    # 並び順(bot_name の一致を優先)は supabase/migrations の search_products 関数で決める
    response = supabase.rpc(
        "search_products",
        {
            "p_query": query,
            "p_terms": terms,
            "p_category_id": category_id,
            "p_limit": limit,
            "p_offset": offset,
        },
    ).execute()

    # 関数は username / category_name を結合済みの列として返すので、一覧と同じ8項目に詰める
    return jsonify(
        [
            {
                "chatbot_id": row["chatbot_id"],
                "bot_name": row["bot_name"],
                "price": row["price"],
                "description": row["description"],
                "thumbnail_url": row["thumbnail_url"],
                "category_id": row["category_id"],
                "username": row["username"],
                "category_name": row["category_name"],
            }
            for row in response.data
        ]
    )


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