from unittest.mock import MagicMock, patch

import pytest

from app import create_app

CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"

# routes.py の PRODUCT_COLUMNS とは、意図して重複させている。
# 列名や外部キー名のタイポを検知するため、期待値はテスト側に直接書く。
EXPECTED_COLUMNS = (
    "chatbot_id, bot_name, price, description, thumbnail_url, "
    "users!chatbot_creator_id_fkey!inner(username), "
    "category(category_name)"
)


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
        "chatbot_id": CHATBOT_ID,
        "bot_name": "テストボット",
        "price": 1000,
        "description": "説明文",
        "thumbnail_url": None,
        "users": {"username": "taro"},
        "category": {"category_name": "学習・教育型"},
    }
    row.update(overrides)
    return row


# 共通: table → select → eq(is_listed) → eq(users.is_withdrawn)
def _select_of(db):
    return db.table.return_value.select


def _listed_eq(db):
    return _select_of(db).return_value.eq


def _withdrawn_eq(db):
    return _listed_eq(db).return_value.eq


# 一覧: ... → order → order → range → execute
def _first_order(db):
    return _withdrawn_eq(db).return_value.order


def _second_order(db):
    return _first_order(db).return_value.order


def _range(db):
    return _second_order(db).return_value.range


def _set_list_rows(db, rows):
    _range(db).return_value.execute.return_value = _db_result(rows)


# 詳細: ... → eq(chatbot_id) → execute
def _id_eq(db):
    return _withdrawn_eq(db).return_value.eq


def _set_detail_rows(db, rows):
    _id_eq(db).return_value.execute.return_value = _db_result(rows)


# ============================================================
# 一覧
# ============================================================


def test_list_products_returns_flat_items(client):
    row = _db_row(auth_email="secret@example.com")

    with patch("products.routes.supabase") as db:
        _set_list_rows(db, [row])

        response = client.get("/api/products")

        _select_of(db).assert_called_once_with(EXPECTED_COLUMNS)
        _listed_eq(db).assert_called_once_with("is_listed", True)
        _withdrawn_eq(db).assert_called_once_with("users.is_withdrawn", False)
        _first_order(db).assert_called_once_with("create_at", desc=True)
        _second_order(db).assert_called_once_with("chatbot_id", desc=True)
        _range(db).assert_called_once_with(0, 19)

    assert response.status_code == 200
    assert response.get_json() == [
        {
            "chatbot_id": CHATBOT_ID,
            "bot_name": "テストボット",
            "price": 1000,
            "description": "説明文",
            "thumbnail_url": None,
            "username": "taro",
            "category_name": "学習・教育型",
        }
    ]


def test_list_products_handles_missing_user_and_category(client):
    row = _db_row(users=None, category=None)

    with patch("products.routes.supabase") as db:
        _set_list_rows(db, [row])

        response = client.get("/api/products")

    assert response.status_code == 200
    body = response.get_json()
    assert body[0]["username"] is None
    assert body[0]["category_name"] is None


def test_list_products_passes_limit_and_offset_to_range(client):
    with patch("products.routes.supabase") as db:
        _set_list_rows(db, [])

        response = client.get("/api/products?limit=5&offset=10")

        _range(db).assert_called_once_with(10, 14)

    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize(
    "query",
    [
        "limit=0",
        "limit=101",
        "limit=abc",
        "offset=-1",
        "offset=abc",
    ],
)
def test_list_products_returns_400_for_invalid_paging(client, query):
    with patch("products.routes.supabase") as db:
        response = client.get(f"/api/products?{query}")

        db.table.assert_not_called()

    assert response.status_code == 400
    assert "limit" in response.get_json()["error"]


# ============================================================
# 詳細
# ============================================================


def test_get_product_returns_item(client):
    row = _db_row(auth_email="secret@example.com")

    with patch("products.routes.supabase") as db:
        _set_detail_rows(db, [row])

        response = client.get(f"/api/products/{CHATBOT_ID}")

        _select_of(db).assert_called_once_with(EXPECTED_COLUMNS)
        _listed_eq(db).assert_called_once_with("is_listed", True)
        _withdrawn_eq(db).assert_called_once_with("users.is_withdrawn", False)
        _id_eq(db).assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.status_code == 200
    body = response.get_json()
    assert body["bot_name"] == "テストボット"
    assert body["username"] == "taro"
    assert "auth_email" not in body


def test_get_product_returns_404_when_not_found(client):
    with patch("products.routes.supabase") as db:
        _set_detail_rows(db, [])

        response = client.get("/api/products/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.get_json()["error"] == "商品が見つかりません"


def test_get_product_returns_400_for_invalid_id(client):
    with patch("products.routes.supabase") as db:
        response = client.get("/api/products/abc")

        db.table.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"


@pytest.mark.parametrize(
    "raw_id",
    [
        "urn:uuid:59e511a0-efcf-4aa8-98cf-d6fa5786e52b",
        "59e511a0efcf4aa898cfd6fa5786e52b",
        "59E511A0-EFCF-4AA8-98CF-D6FA5786E52B",
    ],
)
def test_get_product_normalizes_chatbot_id(client, raw_id):
    with patch("products.routes.supabase") as db:
        _set_detail_rows(db, [_db_row()])

        response = client.get(f"/api/products/{raw_id}")

        _id_eq(db).assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.status_code == 200