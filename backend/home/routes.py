from flask import Blueprint, jsonify
from common.supabase_client import supabase

home_bp = Blueprint("home", __name__)

UNLISTED_STATUS = "unlisted"

@home_bp.route("/listings",methods= ["GET"])
def get_listings():
    try:
        result = (
            supabase.table("chatbot")
            .select("*")
            .neq("sale_status",UNLISTED_STATUS)
            .execute()
        )
        return jsonify(result.data)
    except Exception as e:
        return jsonify({"error":f"商品の取得に失敗しました: {str(e)}"}),500