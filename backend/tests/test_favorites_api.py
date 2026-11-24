
from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from app import create_app

CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"
USER = {"user_id": "buyer01", "username": "buyer"}

# routes.py の FAVORITE_COLUMNS と同じ内容にする
EXPECTED_COLUMNS = (
    "chatbot_id, create_at, "
    "chatbot!inner(bot_name, price, description, thumbnail_url, "
    "users!chatbot_creator_id_fkey!inner(username), "
    "category(category_name))"
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


def _login(user=USER):
    return patch("favorites.routes.get_current_user", return_value=user)


def _favorite_row(**overrides):
    row = {
        "chatbot_id": CHATBOT_ID,
        "create_at": "2026-11-11T00:00:00+00:00",
        "chatbot": {
            "bot_name": "テストボット",
            "price": 1000,
            "description": "説明文",
            "thumbnail_url": None,
            "users": {"username": "taro"},
            "category": {"category_name": "学習・教育型"},
        },
    }
    row.update(overrides)
    return row


# ============================================================
# ログイン必須
# ============================================================

@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/api/favorites"),
        ("post", "/api/favorites"),
        ("delete", f"/api/favorites/{CHATBOT_ID}"),
    ],
)
def test_returns_401_when_not_logged_in(client, method, path):
    with _login(None), patch("favorites.routes.supabase") as db:
        response = getattr(client, method)(
            path, json={"chatbot_id": CHATBOT_ID}
        )

        db.table.assert_not_called()

    assert response.status_code == 401
    assert response.get_json()["error"] == "ログインが必要です"


# ============================================================
# GET /api/favorites
# ============================================================

def _get_chain(db):
    select = db.table.return_value.select
    user_eq = select.return_value.eq
    listed_eq = user_eq.return_value.eq
    withdrawn_eq = listed_eq.return_value.eq
    order = withdrawn_eq.return_value.order
    return select, user_eq, listed_eq, withdrawn_eq, order


def test_get_favorites_returns_items(client):
    with _login(), patch("favorites.routes.supabase") as db:
        select, user_eq, listed_eq, withdrawn_eq, order = _get_chain(db)

        order.return_value.execute.return_value = _db_result(
            [_favorite_row()]
        )

        response = client.get("/api/favorites")

        db.table.assert_called_once_with("favorite_bot")
        select.assert_called_once_with(EXPECTED_COLUMNS)
        user_eq.assert_called_once_with("user_id", "buyer01")
        listed_eq.assert_called_once_with("chatbot.is_listed", True)
        withdrawn_eq.assert_called_once_with(
            "chatbot.users.is_withdrawn", False
        )
        order.assert_called_once_with("create_at", desc=True)

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
            "added_at": "2026-11-11T00:00:00+00:00",
        }
    ]


def test_get_favorites_returns_empty_list(client):
    with _login(), patch("favorites.routes.supabase") as db:
        order = _get_chain(db)[-1]
        order.return_value.execute.return_value = _db_result([])

        response = client.get("/api/favorites")

    assert response.status_code == 200
    assert response.get_json() == []


# ============================================================
# POST /api/favorites
# ============================================================

def _tables(db):
    tables = {"chatbot": MagicMock(),"favorite_bot": MagicMock(),}
    db.table.side_effect = lambda name: tables[name]
    return tables


def _product_chain(tables):
    id_eq = tables["chatbot"].select.return_value.eq
    listed_eq = id_eq.return_value.eq
    withdrawn_eq = listed_eq.return_value.eq
    return id_eq, listed_eq, withdrawn_eq


def _set_product(tables, rows):
    _product_chain(tables)[-1].return_value.execute.return_value = ( _db_result(rows))


def test_add_favorite_inserts_row(client):
    with _login(), patch("favorites.routes.supabase") as db:
        tables = _tables(db)

        _set_product(
            tables,
            [{"chatbot_id": CHATBOT_ID}]
        )

        response = client.post(
            "/api/favorites",
            json={"chatbot_id": CHATBOT_ID}
        )

        id_eq, listed_eq, withdrawn_eq = _product_chain(tables)

        id_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)
        listed_eq.assert_called_once_with("is_listed", True)
        withdrawn_eq.assert_called_once_with(
            "users.is_withdrawn", False
        )

        tables["favorite_bot"].insert.assert_called_once_with({
            "chatbot_id": CHATBOT_ID,
            "user_id": "buyer01",
        })

    assert response.status_code == 201
    assert response.get_json() == {"chatbot_id": CHATBOT_ID}


def test_add_favorite_normalizes_chatbot_id(client):
    with _login(), patch("favorites.routes.supabase") as db:
        tables = _tables(db)

        _set_product(
            tables,
            [{"chatbot_id": CHATBOT_ID}]
        )

        response = client.post(
            "/api/favorites",
            json={"chatbot_id": CHATBOT_ID.upper()}
        )

        tables["favorite_bot"].insert.assert_called_once_with({
            "chatbot_id": CHATBOT_ID,
            "user_id": "buyer01",
        })

    assert response.status_code == 201


@pytest.mark.parametrize(
    "body",
    [
        None,
        {},
        {"chatbot_id": "abc"},
        {"chatbot_id": 123},
        ["not", "dict"],
    ],
)
def test_add_favorite_returns_400_for_invalid_id(client, body):
    with _login(), patch("favorites.routes.supabase") as db:
        response = client.post("/api/favorites", json=body)

        db.table.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"


def test_add_favorite_returns_404_when_product_not_found(client):
    with _login(), patch("favorites.routes.supabase") as db:
        tables = _tables(db)
        _set_product(tables, [])

        response = client.post(
            "/api/favorites",
            json={"chatbot_id": CHATBOT_ID}
        )

        tables["favorite_bot"].insert.assert_not_called()

    assert response.status_code == 404
    assert response.get_json()["error"] == "商品が見つかりません"


def test_add_favorite_returns_409_when_already_registered(client):
    with _login(), patch("favorites.routes.supabase") as db:
        tables = _tables(db)
        _set_product(
            tables,
            [{"chatbot_id": CHATBOT_ID}]
        )

        tables["favorite_bot"].insert.return_value.execute.side_effect = (
            APIError({
                "code": "23505",
                "message": "duplicate key value violates unique constraint",
            })
        )

        response = client.post(
            "/api/favorites",
            json={"chatbot_id": CHATBOT_ID}
        )

    assert response.status_code == 409
    assert response.get_json()["error"] == (
        "この商品は既にお気に入りに登録されています"
    )


# ============================================================
# DELETE /api/favorites/<chatbot_id>
# ============================================================

def _delete_chain(db):
    user_eq = db.table.return_value.delete.return_value.eq
    id_eq = user_eq.return_value.eq
    return user_eq, id_eq


def test_remove_favorite_deletes_row(client):
    with _login(), patch("favorites.routes.supabase") as db:
        user_eq, id_eq = _delete_chain(db)

        id_eq.return_value.execute.return_value = _db_result(
            [{"chatbot_id": CHATBOT_ID}]
        )

        response = client.delete(
            f"/api/favorites/{CHATBOT_ID}"
        )

        db.table.assert_called_once_with("favorite_bot")
        user_eq.assert_called_once_with("user_id", "buyer01")
        id_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.status_code == 200
    assert response.get_json() == {"chatbot_id": CHATBOT_ID}


def test_remove_favorite_returns_404_when_not_registered(client):
    with _login(), patch("favorites.routes.supabase") as db:
        _delete_chain(db)[1].return_value.execute.return_value = (
            _db_result([])
        )

        response = client.delete(
            f"/api/favorites/{CHATBOT_ID}"
        )

    assert response.status_code == 404
    assert response.get_json()["error"] == (
        "お気に入りにこの商品はありません"
    )


def test_remove_favorite_returns_400_for_invalid_id(client):
    with _login(), patch("favorites.routes.supabase") as db:
        response = client.delete("/api/favorites/abc")

        db.table.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"
