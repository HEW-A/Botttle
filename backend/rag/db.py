"""
Supabaseクライアント（バックエンド専用。secret キーを使う）
既存の common/supabase_client.py のクライアントをそのまま使う。
"""

from rag import config  # noqa: F401  .env を読み込ませるため


def get_supabase():
    # 使うときに読み込む（rag を単体で import してもエラーにならないように）
    from common.supabase_client import supabase
    return supabase
