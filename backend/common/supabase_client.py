import os
from supabase import Client, create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SECRET_KEY")

if not supabase_url or not supabase_key:
    raise RuntimeError(
        "SUPABASE_URL または SUPABASE_SECRET_KEY が .env に設定されていません"
    )

# アプリ全体で共通して使うsupabaseクライアント
supabase: Client = create_client(supabase_url, supabase_key)