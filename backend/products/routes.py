import uuid
from flask import Blueprint,jsonify
from common.supabase_client import supabase
products_bp = Blueprint("products",__name__)

@products_bp.route("/health")
def health():
    return jsonify({"status":"ok"})

@products_bp.route("")
def list_products():
    response=(
        supabase.table("chatbot")
        .select(
            "chatbot_id, bot_name,price,description,thumbnail_url,"
            "users(username),category(category_name)"
        )
        .eq("is_listed",True)
        .order("create_at",desc=True)
        .execute()
    )
    products=[
        {
            "chatbot_id":row["chatbot_id"],
            "bot_name":row["bot_name"],
            "price":row["price"],
            "description":row["description"],
            "thumbnail_url":row["thumbnail_url"],
            "username":(row.get("users") or {}).get("username"),
            "category_name":(row.get("category") or {}).get("category_name"),
        }
        for row in response.data
    ]
    return jsonify(products)

@products_bp.route("/<chatbot_id>")
def get_product(chatbot_id):
    try:
        uuid.UUID(chatbot_id)
    except ValueError:
        return jsonify({"error":"無効なchatbot_idです"}),400
    response=(
        supabase.table("chatbot")
        .select(
            "chatbot_id, bot_name,price,description,thumbnail_url,"
            "users(username),category(category_name)"
        )
        .eq("chatbot_id",chatbot_id)
        .eq("is_listed",True)
        .execute()
    )
    if not response.data:
        return jsonify({"error":"商品が見つかりません"}),404
    row = response.data[0]
    return jsonify({
        "chatbot_id":row["chatbot_id"],
        "bot_name":row["bot_name"],
        "price":row["price"],
        "description":row["description"],
        "thumbnail_url":row["thumbnail_url"],
        "username":(row.get("users") or {}).get("username"),
        "category_name":(row.get("category") or {}).get("category_name"),
    })