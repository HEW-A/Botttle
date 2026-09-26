from unittest.mock import patch, MagicMock

import pytest

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def test_get_listings_success(client):
    mock_result = MagicMock()
    mock_result.data = [
        {
            "chatbot_id": "bot-1",
            "bot_name": "テストボット",
            "price": 1000,
            "description": "テスト用",
            "sale_status": "listed",
        }
    ]

    with patch("home.routes.supabase") as mock_supabase:
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .neq.return_value
            .execute.return_value
        ) = mock_result

        response = client.get("/api/home/listings")

    assert response.status_code == 200
    assert response.get_json() == mock_result.data

    mock_supabase.table.return_value.select.assert_called_once_with(
        "chatbot_id,bot_name,price,description,sale_status,users(user_id,username,profile_image_url)"
    )

    mock_supabase.table.return_value.select.return_value.neq.assert_called_once_with(
        "sale_status", "unlisted"
    )

def test_get_listings_returns_500_when_supabase_fails(client):
    with patch("home.routes.supabase") as mock_supabase:
        (
            mock_supabase
            .table.return_value
            .select.return_value
            .neq.return_value
            .execute.side_effect
        ) = Exception("db error")

        response = client.get("/api/home/listings")

    assert response.status_code == 500
    body = response.get_json()
    assert "商品の取得に失敗しました" in body["error"]