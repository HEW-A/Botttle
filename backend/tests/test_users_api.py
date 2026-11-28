from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from app import create_app


USER_ID = "taro123"
OTHER_USER_ID = "hanako456"
USER = {
    "user_id": USER_ID,
    "username": "太郎",
    "profile_image_url": None,
    "developer_profile": "自己紹介",
    "create_at": "2026-01-02T00:00:00+00:00",
}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _result(data):
    result = MagicMock()
    result.data = data
    return result


def _query(data):
    query = MagicMock()
    for name in ("select", "eq", "limit", "in_", "or_", "update"):
        getattr(query, name).return_value = query
    query.execute.return_value = _result(data)
    return query


def _profile_db(user_rows=None, bots=None, sales=None, battles=None, purchases=None, balance=0):
    db = MagicMock()
    queries = {
        "users": _query([USER] if user_rows is None else user_rows),
        "chatbot": _query([] if bots is None else bots),
        "purchases": _query([] if sales is None else sales),
        "bot_arena": _query([] if battles is None else battles),
    }

    purchase_queries = [queries["purchases"]]
    if purchases is not None:
        purchase_queries.append(_query(purchases))

    def table(name):
        if name == "purchases":
            return purchase_queries.pop(0)
        return queries[name]

    db.table.side_effect = table
    db.rpc.return_value.execute.return_value = _result(balance)
    return db, queries


def test_get_public_profile_hides_private_values(client):
    db, queries = _profile_db(
        bots=[
            {"chatbot_id": "bot-a", "is_listed": True},
            {"chatbot_id": "bot-b", "is_listed": False},
        ],
        sales=[{"purchase_id": "sale-1"}, {"purchase_id": "sale-2"}],
        battles=[
            {"bot_a_id": "bot-a", "bot_b_id": "other", "bot_winner_id": "bot-a"},
            {"bot_a_id": "bot-b", "bot_b_id": "other", "bot_winner_id": "other"},
        ],
    )

    with patch("users.routes.supabase", db), patch(
        "users.routes.get_current_user", return_value=None
    ):
        response = client.get(f"/api/users/{USER_ID}")

    assert response.status_code == 200
    assert response.get_json() == {
        "user_id": USER_ID,
        "username": "太郎",
        "profile_image_url": None,
        "developer_profile": "自己紹介",
        "created_at": "2026-01-02T00:00:00+00:00",
        "is_self": False,
        "stats": {"listed_count": 1, "sold_count": 2, "wins": 1, "losses": 1},
    }
    queries["users"].select.assert_called_once_with(
        "user_id, username, profile_image_url, developer_profile, create_at"
    )
    db.rpc.assert_not_called()


def test_get_own_profile_includes_purchase_count_and_balance(client):
    db, _ = _profile_db(
        bots=[{"chatbot_id": "bot-a", "is_listed": False}],
        sales=[],
        purchases=[{"purchase_id": "purchase-1"}, {"purchase_id": "purchase-2"}],
        balance=1250,
    )

    with patch("users.routes.supabase", db), patch(
        "users.routes.get_current_user", return_value={"user_id": USER_ID}
    ):
        response = client.get(f"/api/users/{USER_ID}")

    body = response.get_json()
    assert response.status_code == 200
    assert body["is_self"] is True
    assert body["purchase_count"] == 2
    assert body["coin_balance"] == 1250
    db.rpc.assert_called_once_with("get_coin_balance", {"p_user_id": USER_ID})


@pytest.mark.parametrize("user_id", ["x", "invalid-id", "a" * 21])
def test_get_profile_returns_404_for_invalid_user_id(client, user_id):
    with patch("users.routes.supabase") as db:
        response = client.get(f"/api/users/{user_id}")

    assert response.status_code == 404
    db.table.assert_not_called()


def test_get_profile_returns_404_for_missing_or_withdrawn_user(client):
    db, _ = _profile_db(user_rows=[])
    with patch("users.routes.supabase", db):
        response = client.get(f"/api/users/{USER_ID}")

    assert response.status_code == 404


def test_update_profile_requires_login(client):
    with patch("users.routes.get_current_user", return_value=None), patch(
        "users.routes.supabase"
    ) as db:
        response = client.patch(
            f"/api/users/{USER_ID}", json={"username": "新しい名前", "developer_profile": "紹介"}
        )

    assert response.status_code == 401
    db.table.assert_not_called()


def test_update_profile_rejects_other_user(client):
    with patch(
        "users.routes.get_current_user", return_value={"user_id": OTHER_USER_ID}
    ), patch("users.routes.supabase") as db:
        response = client.patch(
            f"/api/users/{USER_ID}", json={"username": "新しい名前", "developer_profile": "紹介"}
        )

    assert response.status_code == 403
    db.table.assert_not_called()


@pytest.mark.parametrize(
    "body, expected_error",
    [
        ({}, "表示名を入力してください"),
        ({"username": "   ", "developer_profile": "紹介"}, "表示名を入力してください"),
        ({"username": "名" * 21, "developer_profile": "紹介"}, "表示名は20文字以内"),
        ({"username": "太郎", "developer_profile": 123}, "自己紹介は文字列"),
        ({"username": "太郎", "developer_profile": "紹" * 161}, "自己紹介は160文字以内"),
    ],
)
def test_update_profile_validates_input(client, body, expected_error):
    with patch(
        "users.routes.get_current_user", return_value={"user_id": USER_ID}
    ), patch("users.routes.supabase") as db:
        response = client.patch(f"/api/users/{USER_ID}", json=body)

    assert response.status_code == 400
    assert expected_error in response.get_json()["error"]
    db.table.assert_not_called()


def test_update_profile_saves_trimmed_values(client):
    updated = {"username": "新しい名前", "developer_profile": "新しい紹介"}
    query = _query([updated])
    db = MagicMock()
    db.table.return_value = query

    with patch(
        "users.routes.get_current_user", return_value={"user_id": USER_ID}
    ), patch("users.routes.supabase", db):
        response = client.patch(
            f"/api/users/{USER_ID}",
            json={"username": "  新しい名前  ", "developer_profile": "  新しい紹介  "},
        )

    assert response.status_code == 200
    assert response.get_json() == updated
    values = query.update.call_args.args[0]
    assert values["username"] == "新しい名前"
    assert values["developer_profile"] == "新しい紹介"
    assert "updated_at" in values


def test_update_profile_returns_409_for_duplicate_username(client):
    query = _query([])
    query.execute.side_effect = APIError(
        {"message": "duplicate key", "code": "23505", "hint": None, "details": None}
    )
    db = MagicMock()
    db.table.return_value = query

    with patch(
        "users.routes.get_current_user", return_value={"user_id": USER_ID}
    ), patch("users.routes.supabase", db):
        response = client.patch(
            f"/api/users/{USER_ID}", json={"username": "使用済み", "developer_profile": ""}
        )

    assert response.status_code == 409
    assert response.get_json()["error"] == "この表示名は既に使用されています"
