from collections import Counter

from flask import Blueprint, jsonify

from common.supabase_client import supabase

categories_bp = Blueprint("categories", __name__)

# Supabase(PostgREST)が1回のリクエストで返す最大件数に合わせて分割取得する
PAGE_SIZE = 1000

# products/routes.py と同じく、chatbot.creator_id の外部キー名を明示する。
# !inner にすると、退会済みユーザーの商品を users.is_withdrawn で除外できる。
COUNT_COLUMNS = "category_id, users!chatbot_creator_id_fkey!inner(user_id)"


def _count_listed_products():
    """出品中で、出品者が退会していない商品の数を category_id ごとに数える"""
    counts = Counter()
    start = 0
    while True:
        response = (
            supabase.table("chatbot")
            .select(COUNT_COLUMNS)
            .eq("is_listed", True)
            .eq("users.is_withdrawn", False)
            .order("chatbot_id")
            .range(start, start + PAGE_SIZE - 1)
            .execute()
        )
        rows = response.data
        for row in rows:
            # カテゴリ未設定の商品は数えない
            if row.get("category_id") is not None:
                counts[row["category_id"]] += 1
        if len(rows) < PAGE_SIZE:
            return counts
        start += PAGE_SIZE


@categories_bp.route("")
def list_categories():
    categories = (
        supabase.table("category")
        .select("category_id, category_name")
        .order("category_id")
        .execute()
    )
    counts = _count_listed_products()

    # 商品が0件のカテゴリも product_count = 0 として返す
    return jsonify(
        [
            {
                "category_id": row["category_id"],
                "category_name": row["category_name"],
                "product_count": counts.get(row["category_id"], 0),
            }
            for row in categories.data
        ]
    )