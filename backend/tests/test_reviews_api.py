from unittest.mock import MagicMock, patch

import pytest

from app import create_app

CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"
USER = {"user_id": "buyer01", "username": "buyer"}
REVIEWED_AT = "2026-11-24T10:00:00+00:00"

REVIEWS_RESULT = {
    "rating_avg": 4.5,
    "review_count": 2,
    "reviews": [
        {"username": "a", "rating": 5, "comment": "便利", "reviewed_at": REVIEWED_AT},
        {"username": "b", "rating": 4, "comment": None, "reviewed_at": REVIEWED_AT},
    ],
}


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _db_result(data):
    result = MagicMock()
    result.data = data
    return result


def _login(user=USER):
    return patch("reviews.routes.get_current_user", return_value=user)


def _update_chain(db):
    """purchases.update(...).eq(buyer).eq(chatbot) の戻り値"""
    return db.table.return_value.update.return_value.eq.return_value.eq.return_value


# ============================================================
# ログイン必須・ID検証
# ============================================================


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_my_review_requires_login(client, method):
    with _login(None), patch("reviews.routes.supabase") as db:
        response = getattr(client, method)(
            f"/api/products/{CHATBOT_ID}/review", json={"rating": 5}
        )

        db.table.assert_not_called()

    assert response.status_code == 401
    assert response.get_json()["error"] == "ログインが必要です"


@pytest.mark.parametrize(
    "method, path",
    [
        ("get", "/api/products/abc/reviews"),
        ("get", "/api/products/abc/review"),
        ("put", "/api/products/abc/review"),
        ("delete", "/api/products/abc/review"),
    ],
)
def test_invalid_chatbot_id_returns_400(client, method, path):
    with _login(), patch("reviews.routes.supabase") as db:
        response = getattr(client, method)(path, json={"rating": 5})

        db.table.assert_not_called()
        db.rpc.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"


# ============================================================
# GET /api/products/<id>/reviews
# ============================================================


def test_list_reviews_calls_rpc_with_defaults(client):
    with patch("reviews.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(REVIEWS_RESULT)

        response = client.get(f"/api/products/{CHATBOT_ID.upper()}/reviews")

        db.rpc.assert_called_once_with(
            "get_product_reviews",
            {"p_chatbot_id": CHATBOT_ID, "p_limit": 20, "p_offset": 0},
        )

    assert response.status_code == 200
    assert response.get_json() == REVIEWS_RESULT


def test_list_reviews_passes_paging(client):
    with patch("reviews.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(REVIEWS_RESULT)

        client.get(f"/api/products/{CHATBOT_ID}/reviews?limit=5&offset=10")

        db.rpc.assert_called_once_with(
            "get_product_reviews",
            {"p_chatbot_id": CHATBOT_ID, "p_limit": 5, "p_offset": 10},
        )


@pytest.mark.parametrize("query", ["limit=0", "limit=101", "limit=a", "offset=-1", "offset=x"])
def test_list_reviews_rejects_invalid_paging(client, query):
    with patch("reviews.routes.supabase") as db:
        response = client.get(f"/api/products/{CHATBOT_ID}/reviews?{query}")

        db.rpc.assert_not_called()

    assert response.status_code == 400


def test_list_reviews_returns_404_when_product_not_found(client):
    with patch("reviews.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(None)

        response = client.get(f"/api/products/{CHATBOT_ID}/reviews")

    assert response.status_code == 404
    assert response.get_json()["error"] == "商品が見つかりません"


# ============================================================
# GET /api/products/<id>/review
# ============================================================


def _select_chain(db):
    return (
        db.table.return_value.select.return_value.eq.return_value.eq.return_value.limit.return_value
    )


def test_get_my_review_when_not_purchased(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _select_chain(db).execute.return_value = _db_result([])

        response = client.get(f"/api/products/{CHATBOT_ID}/review")

    assert response.status_code == 200
    assert response.get_json() == {"purchased": False, "review": None}


def test_get_my_review_when_purchased_without_review(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _select_chain(db).execute.return_value = _db_result(
            [{"rating": None, "comment": None, "update_at": "2026-11-20T00:00:00+00:00"}]
        )

        response = client.get(f"/api/products/{CHATBOT_ID}/review")

    assert response.get_json() == {"purchased": True, "review": None}


def test_get_my_review_filters_by_buyer_and_product(client):
    row = {"rating": 4, "comment": "良い", "update_at": REVIEWED_AT}
    with _login(), patch("reviews.routes.supabase") as db:
        _select_chain(db).execute.return_value = _db_result([row])

        response = client.get(f"/api/products/{CHATBOT_ID}/review")

        db.table.assert_called_once_with("purchases")
        db.table.return_value.select.assert_called_once_with("rating, comment, update_at")
        select = db.table.return_value.select.return_value
        select.eq.assert_called_once_with("buyer_id", "buyer01")
        select.eq.return_value.eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.get_json() == {
        "purchased": True,
        "review": {"rating": 4, "comment": "良い", "reviewed_at": REVIEWED_AT},
    }


# ============================================================
# PUT /api/products/<id>/review
# ============================================================


def test_put_review_updates_own_purchase(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _update_chain(db).execute.return_value = _db_result(
            [{"purchase_id": "p-1", "rating": 5, "comment": "便利", "update_at": REVIEWED_AT}]
        )

        response = client.put(
            f"/api/products/{CHATBOT_ID}/review", json={"rating": 5, "comment": "  便利 \n"}
        )

        db.table.assert_called_once_with("purchases")
        values = db.table.return_value.update.call_args.args[0]
        update = db.table.return_value.update.return_value
        update.eq.assert_called_once_with("buyer_id", "buyer01")
        update.eq.return_value.eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert values["rating"] == 5
    assert values["comment"] == "便利"
    assert "update_at" in values
    assert "reviewed_at" not in values
    assert response.status_code == 200
    assert response.get_json() == {"rating": 5, "comment": "便利", "reviewed_at": REVIEWED_AT}


@pytest.mark.parametrize("comment", [None, "", "   "])
def test_put_review_comment_is_optional(client, comment):
    body = {"rating": 3} if comment is None else {"rating": 3, "comment": comment}
    with _login(), patch("reviews.routes.supabase") as db:
        _update_chain(db).execute.return_value = _db_result(
            [{"rating": 3, "comment": None, "update_at": REVIEWED_AT}]
        )

        response = client.put(f"/api/products/{CHATBOT_ID}/review", json=body)

        values = db.table.return_value.update.call_args.args[0]

    assert response.status_code == 200
    assert values["comment"] is None


def test_put_review_accepts_max_length_comment(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _update_chain(db).execute.return_value = _db_result(
            [{"rating": 1, "comment": "あ" * 1000, "update_at": REVIEWED_AT}]
        )

        response = client.put(
            f"/api/products/{CHATBOT_ID}/review", json={"rating": 1, "comment": "あ" * 1000}
        )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "body",
    [None, {}, {"rating": None}, {"rating": 0}, {"rating": 6}, {"rating": 4.5},
     {"rating": "5"}, {"rating": True}, []],
)
def test_put_review_rejects_invalid_rating(client, body):
    with _login(), patch("reviews.routes.supabase") as db:
        response = client.put(f"/api/products/{CHATBOT_ID}/review", json=body)

        db.table.assert_not_called()

    assert response.status_code == 400
    assert "rating" in response.get_json()["error"]


@pytest.mark.parametrize("comment", [123, ["a"], {"a": 1}, "あ" * 1001])
def test_put_review_rejects_invalid_comment(client, comment):
    with _login(), patch("reviews.routes.supabase") as db:
        response = client.put(
            f"/api/products/{CHATBOT_ID}/review", json={"rating": 5, "comment": comment}
        )

        db.table.assert_not_called()

    assert response.status_code == 400
    assert "comment" in response.get_json()["error"]


def test_put_review_returns_403_when_not_purchased(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _update_chain(db).execute.return_value = _db_result([])

        response = client.put(f"/api/products/{CHATBOT_ID}/review", json={"rating": 5})

    assert response.status_code == 403
    assert response.get_json()["error"] == "購入した商品のみレビューできます"


# ============================================================
# DELETE /api/products/<id>/review
# ============================================================


def _delete_chain(db):
    return _update_chain(db).not_.is_.return_value


def test_delete_review_clears_rating_and_comment(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _delete_chain(db).execute.return_value = _db_result([{"purchase_id": "p-1"}])

        response = client.delete(f"/api/products/{CHATBOT_ID}/review")

        values = db.table.return_value.update.call_args.args[0]
        update = db.table.return_value.update.return_value
        update.eq.assert_called_once_with("buyer_id", "buyer01")
        update.eq.return_value.eq.assert_called_once_with("chatbot_id", CHATBOT_ID)
        _update_chain(db).not_.is_.assert_called_once_with("rating", "null")

    assert values["rating"] is None
    assert values["comment"] is None
    assert "update_at" in values
    assert "reviewed_at" not in values
    assert response.status_code == 204


def test_delete_review_returns_404_when_no_review(client):
    with _login(), patch("reviews.routes.supabase") as db:
        _delete_chain(db).execute.return_value = _db_result([])

        response = client.delete(f"/api/products/{CHATBOT_ID}/review")

    assert response.status_code == 404
    assert response.get_json()["error"] == "レビューが見つかりません"
