from flask import request
from common.supabase_client import supabase

ACCESS_TOKEN_COOKIE = "access_token"


def get_current_user():
    """
    Cookieのaccess_tokenを検証し、ログイン中のユーザー情報(usersテーブルの行)を返す。
    未ログイン・トークン無効の場合は None を返す。
    """
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE)

    if not access_token:
        return None

    try:
        result = supabase.auth.get_user(access_token)
    except Exception:
        return None

    if not result or not result.user:
        return None

    user_row = supabase.table("users").select("*").eq("supabase_uid", result.user.id).limit(1).execute()

    return user_row.data[0] if user_row.data else None