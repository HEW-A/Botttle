import uuid

from flask import Blueprint, jsonify, request

from common.supabase_client import supabase

products_bp = Blueprint("products", __name__)

# users は cart / favorite_bot などを経由した関係とも解釈できて曖昧になるため、
# chatbot.creator_id の外部キー名を明示する。
# !inner にすると、退会済みユーザーの行は結合の段階で除外される。
PRODUCT_COLUMNS = (
    "chatbot_id, bot_name, price, description, thumbnail_url, "
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


def _to_product(row):
    """DBの1行を、APIで返す7項目の辞書に変換する"""
    return {
        "chatbot_id": row["chatbot_id"],
        "bot_name": row["bot_name"],
        "price": row["price"],
        "description": row["description"],
        "thumbnail_url": row["thumbnail_url"],
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

    # 検索フォームの送信時に q 付きで呼ばれる。未指定・空白だけなら通常の一覧を返す
    query = request.args.get("q", "").strip()
    if query:
        return _search_products(query, limit, offset)

    response = (
        _listed_products_query()
        .order("create_at", desc=True)
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


def _search_products(query, limit, offset):
    if len(query) > MAX_QUERY_LENGTH:
        return jsonify({"error": QUERY_TOO_LONG_ERROR}), 400

    terms = _split_terms(query)
    if len(terms) > MAX_TERMS:
        return jsonify({"error": TOO_MANY_TERMS_ERROR}), 400

    # 並び順(bot_name の一致を優先)は supabase/migrations の search_products 関数で決める
    response = supabase.rpc(
        "search_products",
        {"p_query": query, "p_terms": terms, "p_limit": limit, "p_offset": offset},
    ).execute()

    # 関数は username / category_name を結合済みの列として返すので、そのまま7項目に詰める
    return jsonify(
        [
            {
                "chatbot_id": row["chatbot_id"],
                "bot_name": row["bot_name"],
                "price": row["price"],
                "description": row["description"],
                "thumbnail_url": row["thumbnail_url"],
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