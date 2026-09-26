from flask import Blueprint, jsonify
from common.supabase_client import supabase

home_bp = Blueprint("home", __name__)

UNLISTED_STATUS = "unlisted"

@home_bp.route("/listings",methods= ["GET"])
def get_listings():
    try:
        result = (
            supabase.table("chatbot")
            .select("chatbot_id,bot_name,price,description,sale_status,users(user_id,username,profile_image_url),category(category_id,category_name)")
            .neq("sale_status",UNLISTED_STATUS)
            .execute()
        )
        return jsonify(result.data)
    except Exception as e:
        print(e)
        return jsonify({"error":f"商品の取得に失敗しました: {str(e)}"}),500