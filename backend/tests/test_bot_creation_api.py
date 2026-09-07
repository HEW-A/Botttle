import io
from unittest.mock import patch, MagicMock

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _dummy_file():
    return (io.BytesIO(b"dummy pdf content"), "manual.pdf")


# ============================================================
# 認証チェック
# ============================================================

def test_create_bot_requires_login(client):
    data = {
        "bot_name": "テストボット",
        "files": _dummy_file(),
    }

    with patch("bot_creation.routes.get_current_user", return_value=None):
        response = client.post("/api/bots", data=data, content_type="multipart/form-data")

    assert response.status_code == 401
    assert response.get_json()["error"] == "ログインが必要です"


# ============================================================
# 入力チェック
# ============================================================

def test_create_bot_requires_bot_name(client):
    fake_user = {"id": "user-uuid-1"}
    data = {"files": _dummy_file()}

    with patch("bot_creation.routes.get_current_user", return_value=fake_user):
        response = client.post("/api/bots", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json()["error"] == "bot_name と creator_id は必須です"


def test_create_bot_requires_files(client):
    fake_user = {"id": "user-uuid-1"}
    data = {"bot_name": "テストボット"}

    with patch("bot_creation.routes.get_current_user", return_value=fake_user):
        response = client.post("/api/bots", data=data, content_type="multipart/form-data")

    assert response.status_code == 400
    assert response.get_json()["error"] == "PDFファイルが送られていません"


# ============================================================
# chatbot登録の失敗
# ============================================================

def test_create_bot_returns_500_when_chatbot_insert_fails(client):
    fake_user = {"id": "user-uuid-1"}
    data = {
        "bot_name": "テストボット",
        "files": _dummy_file(),
    }

    with patch("bot_creation.routes.get_current_user", return_value=fake_user), \
         patch("bot_creation.routes.supabase") as mock_supabase:

        mock_supabase.table.return_value.insert.return_value.execute.side_effect = Exception("db error")

        response = client.post("/api/bots", data=data, content_type="multipart/form-data")

    assert response.status_code == 500
    assert "チャットボットの登録に失敗しました" in response.get_json()["error"]


# ============================================================
# 正常系
# ============================================================

def test_create_bot_success(client):
    fake_user = {"id": "user-uuid-1"}
    data = {
        "bot_name": "テストボット",
        "description": "説明文",
        "category_id": "category-uuid-1",
        "files": _dummy_file(),
    }

    with patch("bot_creation.routes.get_current_user", return_value=fake_user), \
         patch("bot_creation.routes.supabase") as mock_supabase, \
         patch("bot_creation.routes._process_pdfs", return_value=(
             [{"pdf_id": "pdf-1", "file_name": "manual.pdf"}], []
         )):

        mock_chatbot_result = MagicMock()
        mock_chatbot_result.data = [{"chatbot_id": "chatbot-uuid-1"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_chatbot_result

        response = client.post("/api/bots", data=data, content_type="multipart/form-data")

    assert response.status_code == 201
    body = response.get_json()
    assert body["chatbot_id"] == "chatbot-uuid-1"
    assert body["uploaded"] == [{"pdf_id": "pdf-1", "file_name": "manual.pdf"}]
    assert body["failed"] == []
    assert "1件のPDFを保存しました" in body["message"]


def test_create_bot_success_with_partial_pdf_failures(client):
    """PDFが一部失敗しても、chatbot作成自体は201で成功すること"""
    fake_user = {"id": "user-uuid-1"}
    data = {
        "bot_name": "テストボット",
        "files": _dummy_file(),
    }

    with patch("bot_creation.routes.get_current_user", return_value=fake_user), \
         patch("bot_creation.routes.supabase") as mock_supabase, \
         patch("bot_creation.routes._process_pdfs", return_value=(
             [], [{"file_name": "manual.pdf", "reason": "PDFファイルではありません"}]
         )):

        mock_chatbot_result = MagicMock()
        mock_chatbot_result.data = [{"chatbot_id": "chatbot-uuid-1"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_chatbot_result

        response = client.post("/api/bots", data=data, content_type="multipart/form-data")

    assert response.status_code == 201
    body = response.get_json()
    assert body["uploaded"] == []
    assert body["failed"] == [{"file_name": "manual.pdf", "reason": "PDFファイルではありません"}]
    assert "0件のPDFを保存しました" in body["message"]