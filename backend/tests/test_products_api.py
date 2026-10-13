from unittest.mock import patch, MagicMock

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _db_result(rows):
    result = MagicMock()
    result.data = rows
    return result


def _db_row(**overrides):
    row = {
        "chatbot_id": "59e511a0-efcf-4aa8-98cf-d6fa5786e52b",
        "bot_name": "テストボット",
        "price": 1000,
        "description": "説明文",
        "thumbnail_url": None,
        "users": {"username": "taro"},
        "category": {"category_name": "学習・教育型"},
    }
    row.update(overrides)
    return row


def test_list_products_returns_flat_items(client):
    row = _db_row(auth_email="secret@example.com")

    with patch("products.routes.supabase") as mock_supabase:
        chain = mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value
        chain.execute.return_value = _db_result([row])

        response = client.get("/api/products")

        mock_supabase.table.return_value.select.return_value.eq.assert_called_once_with("is_listed", True)

    assert response.status_code == 200
    assert response.get_json() == [{
        "chatbot_id": "59e511a0-efcf-4aa8-98cf-d6fa5786e52b",
        "bot_name": "テストボット",
        "price": 1000,
        "description": "説明文",
        "thumbnail_url": None,
        "username": "taro",
        "category_name": "学習・教育型",
    }]


def test_list_products_handles_missing_user_and_category(client):
    row = _db_row(users=None, category=None)

    with patch("products.routes.supabase") as mock_supabase:
        chain = mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value
        chain.execute.return_value = _db_result([row])

        response = client.get("/api/products")

    assert response.status_code == 200
    body = response.get_json()
    assert body[0]["username"] is None
    assert body[0]["category_name"] is None


def test_get_product_returns_item(client):
    row = _db_row(auth_email="secret@example.com")

    with patch("products.routes.supabase") as mock_supabase:
        chain = mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value
        chain.execute.return_value = _db_result([row])

        response = client.get("/api/products/59e511a0-efcf-4aa8-98cf-d6fa5786e52b")

        mock_supabase.table.return_value.select.return_value.eq.return_value.eq.assert_called_once_with("is_listed", True)

    assert response.status_code == 200
    body = response.get_json()
    assert body["bot_name"] == "テストボット"
    assert body["username"] == "taro"
    assert "auth_email" not in body


def test_get_product_returns_404_when_not_found(client):
    with patch("products.routes.supabase") as mock_supabase:
        chain = mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value
        chain.execute.return_value = _db_result([])

        response = client.get("/api/products/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.get_json()["error"] == "商品が見つかりません"


def test_get_product_returns_400_for_invalid_id(client):
    with patch("products.routes.supabase") as mock_supabase:
        response = client.get("/api/products/abc")

        mock_supabase.table.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"