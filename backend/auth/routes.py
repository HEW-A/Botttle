import os

from flask import Blueprint, request, jsonify

from common.supabase_client import supabase

auth_bp = Blueprint("auth", __name__)

# 本番環境ではCookieにSecure属性を付ける（HTTPSでのみ送信）
COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
ACCESS_TOKEN_COOKIE = "access_token"
REFRESH_TOKEN_COOKIE = "refresh_token"

# 連絡先メールを入力しなかったユーザー向けに、Supabase Auth用のダミーメールを発行するドメイン
DUMMY_EMAIL_DOMAIN = "users.botttle.internal"

MIN_PASSWORD_LENGTH = 8


def _set_session_cookies(response, session):
    """Supabaseのセッション情報をhttponly Cookieとしてレスポンスに乗せる"""
    response.set_cookie(
        ACCESS_TOKEN_COOKIE,
        session.access_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="Lax",
    )
    response.set_cookie(
        REFRESH_TOKEN_COOKIE,
        session.refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="Lax",
    )


def _clear_session_cookies(response):
    response.delete_cookie(ACCESS_TOKEN_COOKIE)
    response.delete_cookie(REFRESH_TOKEN_COOKIE)


def _find_user_row(column, value):
    """usersテーブルを指定カラムで検索し、1件目（無ければNone）を返す"""
    result = supabase.table("users").select("*").eq(column, value).limit(1).execute()
    return result.data[0] if result.data else None


# 新規登録のapi
@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    user_id = data.get("user_id")
    username = data.get("username")
    password = data.get("password")
    email = data.get("email") or None

    if not user_id or not username or not password:
        return jsonify({"error": "user_id と username と password は必須です"}), 400

    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify({"error": f"パスワードは{MIN_PASSWORD_LENGTH}文字以上で入力してください"}), 400

    if _find_user_row("user_id", user_id):
        return jsonify({"error": "このユーザーIDは既に使用されています"}), 400

    # 連絡先メール未入力の場合は、Supabase Auth用のダミーメールを生成する
    auth_email = email or f"{user_id}@{DUMMY_EMAIL_DOMAIN}"

    try:
        result = supabase.auth.sign_up({
            "email": auth_email,
            "password": password,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    try:
        supabase.table("users").insert({
            "supabase_uid": result.user.id,
            "user_id": user_id,
            "username": username,
            "auth_email": auth_email,
            "user_mailaddless": email,
        }).execute()
    except Exception as e:
        return jsonify({"error": str(e)}), 400

    response = jsonify({
        "message": "登録に成功しました",
        "user_id": user_id,
        "username": username,
    })
    response.status_code = 201

    # メール確認が無効な設定の場合、sign_up直後にセッションが発行されるのでCookieを乗せる
    if result.session:
        _set_session_cookies(response, result.session)

    return response

# ログインのapi
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user_id = data.get("user_id")
    password = data.get("password")

    if not user_id or not password:
        return jsonify({"error": "user_id と password は必須です"}), 400

    user_row = _find_user_row("user_id", user_id)
    if not user_row:
        return jsonify({"error": "ユーザーIDまたはパスワードが正しくありません"}), 401

    try:
        result = supabase.auth.sign_in_with_password({
            "email": user_row["auth_email"],
            "password": password,
        })
    except Exception:
        return jsonify({"error": "ユーザーIDまたはパスワードが正しくありません"}), 401

    response = jsonify({
        "message": "ログインに成功しました",
        "user_id": user_row["user_id"],
        "username": user_row["username"],
    })
    _set_session_cookies(response, result.session)

    return response


# ログアウトのapi
@auth_bp.route("/logout", methods=["POST"])
def logout():
    response = jsonify({"message": "ログアウトしました"})
    _clear_session_cookies(response)
    return response


# ログイン中のユーザー情報を返すapi（Cookieのaccess_tokenをSupabaseで検証）
@auth_bp.route("/me", methods=["GET"])
def me():
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if not access_token:
        return jsonify({"error": "ログインしていません"}), 401

    try:
        result = supabase.auth.get_user(access_token)
    except Exception as e:
        return jsonify({"error": str(e)}), 401

    if not result or not result.user:
        return jsonify({"error": "ログインしていません"}), 401

    user_row = _find_user_row("supabase_uid", result.user.id)
    if not user_row:
        return jsonify({"error": "ユーザー情報が見つかりません"}), 404

    return jsonify({
        "user_id": user_row["user_id"],
        "username": user_row["username"],
        "email": user_row["user_mailaddless"],
    }), 200