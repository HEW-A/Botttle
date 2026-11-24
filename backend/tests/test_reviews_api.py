from unittest.mock import MagicMock, patch

import pytest

from app import create_app


CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"
USER = {"user_id": "buyer01", "username": "buyer"}

EXPECTED_REVIEW_COLUMNS = (
    "purchase_id, rating, comment, update_at, "
    "users!purchases_buyer_id_fkey(username)"
)
EXPECTED_MY_COLUMNS = "purchase_id, rating, comment, update_at"


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
    return patch("reviews.routes.get_current_user", return_value=user)


def _find_chain(db):
    buyer_eq = db.table.return_value.select.return_value.eq
    chatbot_eq = buyer_eq.return_value.eq
    limit = chatbot_eq.return_value.limit
    return buyer_eq, chatbot_eq, limit


def _set_purchase(db, rows):
    _find_chain(db)[-1].return_value.execute.return_value = _db_result(rows)


def _purchase_row(**overrides):
    row = {
        "purchase_id": "purchase-1",
        "rating": 5,
        "comment": "使いやすいです",
        "update_at": "2026-11-14T00:00:00+00:00",
    }
    row.update(overrides)
    return row


def test_get_reviews_returns_integer_ratings_and_decimal_average(client):
    rows = [
        {**_purchase_row(), "users": {"username": "taro"}},
        {
            **_purchase_row(
                purchase_id="purchase-2", rating=4, comment="便利でした"
            ),
            "users": {"username": "hanako"},
        },
        {**_purchase_row(purchase_id="purchase-3", rating=None), "users": None},
    ]

    with patch("reviews.routes.supabase") as db:
        chatbot_eq = db.table.return_value.select.return_value.eq
        chatbot_eq.return_value.execute.return_value = _db_result(rows)

        response = client.get(f"/api/reviews/{CHATBOT_ID}")

        db.table.assert_called_once_with("purchases")
        db.table.return_value.select.assert_called_once_with(EXPECTED_REVIEW_COLUMNS)
        chatbot_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.status_code == 200
    body = response.get_json()
    assert body["average_rating"] == 4.5
    assert body["review_count"] == 2
    assert body["reviews"][0]["rating"] == 5
    assert body["reviews"][0]["username"] == "taro"


def test_get_reviews_returns_400_for_invalid_id(client):
    with patch("reviews.routes.supabase") as db:
        response = client.get("/api/reviews/not-a-uuid")
        db.table.assert_not_called()

    assert response.status_code == 400


def test_get_my_review_requires_login(client):
    with _login(None), patch("reviews.routes.supabase") as db:
        response = client.get(f"/api/reviews/{CHATBOT_ID}/mine")
        db.table.assert_not_called()

    assert response.status_code == 401


def test_get_my_review_reports_not_purchased(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _set_purchase(db, [])

        response = client.get(f"/api/reviews/{CHATBOT_ID}/mine")

    assert response.status_code == 200
    assert response.get_json() == {"can_review": False, "review": None}


def test_get_my_review_returns_existing_review(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _set_purchase(db, [_purchase_row()])

        response = client.get(f"/api/reviews/{CHATBOT_ID}/mine")

        buyer_eq, chatbot_eq, _ = _find_chain(db)
        db.table.return_value.select.assert_called_once_with(EXPECTED_MY_COLUMNS)
        buyer_eq.assert_called_once_with("buyer_id", "buyer01")
        chatbot_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.status_code == 200
    assert response.get_json()["review"]["rating"] == 5


def test_save_review_stores_integer(client):
    purchase = _purchase_row(rating=None, comment=None)

    with _login(), patch("reviews.routes.supabase") as db:
        _set_purchase(db, [purchase])
        saved = _purchase_row(comment="とても便利です")
        buyer_eq = db.table.return_value.update.return_value.eq
        buyer_eq.return_value.eq.return_value.execute.return_value = _db_result([saved])

        response = client.put(
            f"/api/reviews/{CHATBOT_ID}",
            json={"rating": 5, "comment": "  とても便利です  "},
        )

        update_data = db.table.return_value.update.call_args.args[0]
        assert update_data["rating"] == 5
        assert update_data["comment"] == "とても便利です"
        assert "update_at" in update_data
        buyer_eq.assert_called_once_with("purchase_id", "purchase-1")
        buyer_eq.return_value.eq.assert_called_once_with("buyer_id", "buyer01")

    assert response.status_code == 200
    assert response.get_json()["rating"] == 5


@pytest.mark.parametrize(
    "rating",
    [None, True, "abc", 0, 6, 4.5, float("nan"), float("inf")],
)
def test_save_review_rejects_invalid_rating(client, rating):
    with _login(), patch("reviews.routes.supabase") as db:
        response = client.put(
            f"/api/reviews/{CHATBOT_ID}",
            json={"rating": rating, "comment": "コメント"},
        )
        db.table.assert_not_called()

    assert response.status_code == 400
    assert "rating" in response.get_json()["error"]


@pytest.mark.parametrize("comment", [None, 123, "", "   "])
def test_save_review_rejects_invalid_comment(client, comment):
    with _login(), patch("reviews.routes.supabase") as db:
        response = client.put(
            f"/api/reviews/{CHATBOT_ID}",
            json={"rating": 5, "comment": comment},
        )
        db.table.assert_not_called()

    assert response.status_code == 400
    assert "comment" in response.get_json()["error"]


def test_save_review_rejects_long_comment(client):
    with _login(), patch("reviews.routes.supabase") as db:
        response = client.put(
            f"/api/reviews/{CHATBOT_ID}",
            json={"rating": 5, "comment": "a" * 1001},
        )
        db.table.assert_not_called()

    assert response.status_code == 400


def test_save_review_rejects_non_purchaser(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _set_purchase(db, [])

        response = client.put(
            f"/api/reviews/{CHATBOT_ID}",
            json={"rating": 5, "comment": "コメント"},
        )

        db.table.return_value.update.assert_not_called()

    assert response.status_code == 403
    assert response.get_json()["error"] == "購入したボットのみ評価できます"
