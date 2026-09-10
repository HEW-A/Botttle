from unittest.mock import MagicMock, patch
from flask import Flask

from common.auth_helper import get_current_user

app = Flask(__name__)


def test_get_current_user_returns_none_when_no_cookie():
    with app.test_request_context("/", headers={}):
        # Cookieを一切付けずにリクエストを再現
        result = get_current_user()
        assert result is None


def test_get_current_user_returns_none_when_token_invalid():
    with app.test_request_context("/", headers={"Cookie": "access_token=invalid_token"}):
        with patch("common.auth_helper.supabase") as mock_supabase:
            # supabase.auth.get_user が例外を投げる状況を再現
            mock_supabase.auth.get_user.side_effect = Exception("invalid token")

            result = get_current_user()
            assert result is None


def test_get_current_user_returns_user_row_when_valid():
    with app.test_request_context("/", headers={"Cookie": "access_token=valid_token"}):
        with patch("common.auth_helper.supabase") as mock_supabase:
            # ① supabase.auth.get_user が、正常なユーザー情報を返す状況を再現
            fake_auth_user = MagicMock()
            fake_auth_user.user.id = "supabase-uid-123"
            mock_supabase.auth.get_user.return_value = fake_auth_user

            # ② supabase.table("users").select(...) が、該当行を返す状況を再現
            fake_user_row = {"id": "user-id-123", "user_id": "taro2026", "username": "たろう"}
            mock_table_result = MagicMock()
            mock_table_result.data = [fake_user_row]
            mock_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_table_result

            result = get_current_user()
            assert result == fake_user_row