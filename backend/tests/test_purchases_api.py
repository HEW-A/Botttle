from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from app import create_app

CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"
USER = {"user_id": "buyer01", "username": "buyer"}

RPC_RESULT = {
    "purchases": [{"purchase_id": "p-1", "chatbot_id": CHATBOT_ID, "price": 1000}],
    "total": 1000,
    "balance": 500,
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


def _login(module, user=USER):
    return patch(f"{module}.routes.get_current_user", return_value=user)


def _rpc_error(message):
    return APIError({"message": message, "code": "P0001", "hint": None, "details": None})


# ============================================================
# ログイン必須
# ============================================================


@pytest.mark.parametrize(
    "module, method, path",
    [
        ("purchases", "post", "/api/purchases/cart"),
        ("purchases", "post", "/api/purchases"),
        ("coins", "get", "/api/coins/balance"),
    ],
)
def test_returns_401_when_not_logged_in(client, module, method, path):
    with _login(module, None), patch(f"{module}.routes.supabase") as db:
        response = getattr(client, method)(path, json={"chatbot_id": CHATBOT_ID})

        db.rpc.assert_not_called()

    assert response.status_code == 401
    assert response.get_json()["error"] == "ログインが必要です"


# ============================================================
# POST /api/purchases/cart
# ============================================================


def test_purchase_cart_calls_rpc_with_cart_mode(client):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(RPC_RESULT)

        response = client.post("/api/purchases/cart", json={"expected_total": 1000})

        db.rpc.assert_called_once_with(
            "purchase_chatbots",
            {"p_buyer_id": "buyer01", "p_chatbot_ids": None, "p_expected_total": 1000},
        )

    assert response.status_code == 201
    assert response.get_json() == RPC_RESULT


def test_purchase_cart_without_body(client):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(RPC_RESULT)

        response = client.post("/api/purchases/cart")

        db.rpc.assert_called_once_with(
            "purchase_chatbots",
            {"p_buyer_id": "buyer01", "p_chatbot_ids": None, "p_expected_total": None},
        )

    assert response.status_code == 201


@pytest.mark.parametrize("expected_total", [-1, 1.5, "1000", True])
def test_purchase_cart_rejects_invalid_expected_total(client, expected_total):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        response = client.post("/api/purchases/cart", json={"expected_total": expected_total})

        db.rpc.assert_not_called()

    assert response.status_code == 400


# ============================================================
# POST /api/purchases
# ============================================================


def test_purchase_product_normalizes_id(client):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(RPC_RESULT)

        response = client.post(
            "/api/purchases", json={"chatbot_id": CHATBOT_ID.replace("-", "").upper()}
        )

        db.rpc.assert_called_once_with(
            "purchase_chatbots",
            {"p_buyer_id": "buyer01", "p_chatbot_ids": [CHATBOT_ID], "p_expected_total": None},
        )

    assert response.status_code == 201
    assert response.get_json() == RPC_RESULT


@pytest.mark.parametrize("body", [{}, {"chatbot_id": "abc"}, {"chatbot_id": 123}, []])
def test_purchase_product_rejects_invalid_id(client, body):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        response = client.post("/api/purchases", json=body)

        db.rpc.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"


# ============================================================
# DB関数のエラー → HTTPステータス
# ============================================================


@pytest.mark.parametrize(
    "code, status",
    [
        ("USER_NOT_FOUND", 401),
        ("CART_EMPTY", 400),
        ("PRODUCT_NOT_FOUND", 404),
        ("OWN_PRODUCT", 400),
        ("ALREADY_PURCHASED", 409),
        ("TOTAL_MISMATCH", 409),
        ("INSUFFICIENT_BALANCE", 400),
    ],
)
def test_maps_rpc_errors(client, code, status):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        db.rpc.return_value.execute.side_effect = _rpc_error(code)

        response = client.post("/api/purchases", json={"chatbot_id": CHATBOT_ID})

    assert response.status_code == status
    assert "error" in response.get_json()


def test_unknown_rpc_error_returns_500(client):
    with _login("purchases"), patch("purchases.routes.supabase") as db:
        db.rpc.return_value.execute.side_effect = _rpc_error("COIN_TYPE_NOT_FOUND")

        response = client.post("/api/purchases/cart")

    assert response.status_code == 500


# ============================================================
# GET /api/coins/balance
# ============================================================


def test_get_balance(client):
    with _login("coins"), patch("coins.routes.supabase") as db:
        db.rpc.return_value.execute.return_value = _db_result(1500)

        response = client.get("/api/coins/balance")

        db.rpc.assert_called_once_with("get_coin_balance", {"p_user_id": "buyer01"})

    assert response.status_code == 200
    assert response.get_json() == {"balance": 1500}
