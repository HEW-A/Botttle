import os
from supabase import Client, ClientOptions, create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url or not supabase_key:
    raise RuntimeError(
        "SUPABASE_URL または SUPABASE_SECRET_KEY が .env に設定されていません"
    )

# アプリ全体で共通して使うsupabaseクライアント（DB・Storage・RPC用。service_role権限で動く）
# 注意: このクライアントで auth.sign_in_with_password / auth.sign_up を呼ばないこと。
# supabase-py はサインインすると以降のリクエストのAuthorizationヘッダーをそのユーザーのJWTに
# 差し替えるため、全リクエストのDB操作がそのユーザー権限（RLS適用）になってしまう。
# トークンの検証（auth.get_user(access_token)）はセッションを変えないので使ってよい。
supabase: Client = create_client(supabase_url, supabase_key)


def create_auth_client() -> Client:
    """ログイン・新規登録専用のクライアントを作る。

    サインインでセッション状態が書き換わっても共有クライアントに影響しないよう、
    リクエストごとに新しく作って使い捨てる。
    """
    return create_client(
        supabase_url,
        supabase_key,
        options=ClientOptions(auto_refresh_token=False, persist_session=False),
    )