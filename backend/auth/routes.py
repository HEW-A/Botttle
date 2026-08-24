from flask import Blueprint, request, jsonify

from common.supabase_client import supabase

auth_bp = Blueprint("auth", __name__)

# 新規登録のapi
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email と password は必須です"}), 400

    try:
        result = supabase.auth.sign_up({
            "email": email,
            "password": password,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    return jsonify({
        "message": "登録に成功しました",
        "user_id": result.user.id,
    }), 201

# ログインのapi
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "email と password は必須です"}), 400

    try:
        result = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    return jsonify({
        "message": "ログインに成功しました",
        "access_token": result.session.access_token,
        "user_id": result.user.id,
    }), 200