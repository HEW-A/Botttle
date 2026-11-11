from unittest.mock import MagicMock, patch

import pytest
from postgrest.exceptions import APIError

from app import create_app

CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"
USER = {"user_id": "buyer01", "username": "buyer"}

# routes.py の CART_COLUMNS とは、意図して重複させている。
# 列名や外部キー名のタイポを検知するため、期待値はテスト側に直接書く。
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
    return patch("cart.routes.get_current_user", return_value=user)


def _cart_row(**overrides):
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
        ("get", "/api/cart"),
        ("post", "/api/cart"),
        ("delete", f"/api/cart/{CHATBOT_ID}"),
        ("delete", "/api/cart"),
    ],
)
def test_returns_401_when_not_logged_in(client, method, path):
    with _login(None), patch("cart.routes.supabase") as db:
        response = getattr(client, method)(path, json={"chatbot_id": CHATBOT_ID})

        db.table.assert_not_called()

    assert response.status_code == 401
    assert response.get_json()["error"] == "ログインが必要です"


# ============================================================
# GET /api/cart
# ============================================================


# table → select → eq(user_id) → eq(is_listed) → eq(is_withdrawn) → order → execute
def _get_chain(db):
    select = db.table.return_value.select
    user_eq = select.return_value.eq
    listed_eq = user_eq.return_value.eq
    withdrawn_eq = listed_eq.return_value.eq
    order = withdrawn_eq.return_value.order
    return select, user_eq, listed_eq, withdrawn_eq, order


def test_get_cart_returns_items(client):
    with _login(), patch("cart.routes.supabase") as db:
        select, user_eq, listed_eq, withdrawn_eq, order = _get_chain(db)
        order.return_value.execute.return_value = _db_result([_cart_row()])

        response = client.get("/api/cart")

        db.table.assert_called_once_with("cart")
        select.assert_called_once_with(EXPECTED_COLUMNS)
        user_eq.assert_called_once_with("user_id", "buyer01")
        listed_eq.assert_called_once_with("chatbot.is_listed", True)
        withdrawn_eq.assert_called_once_with("chatbot.users.is_withdrawn", False)
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


def test_get_cart_returns_empty_list(client):
    with _login(), patch("cart.routes.supabase") as db:
        order = _get_chain(db)[-1]
        order.return_value.execute.return_value = _db_result([])

        response = client.get("/api/cart")

    assert response.status_code == 200
    assert response.get_json() == []


# ============================================================
# POST /api/cart
# ============================================================



# POST は chatbot / purchases / cart の3テーブルを使うため、
# テーブル名ごとに別のモックを返して、呼び出しが混ざらないようにする
def _tables(db):
    tables = {"chatbot": MagicMock(), "purchases": MagicMock(), "cart": MagicMock()}
    db.table.side_effect = lambda name: tables[name]
    return tables


# 商品確認: select → eq(chatbot_id) → eq(is_listed) → eq(is_withdrawn) → execute
def _product_chain(tables):
    id_eq = tables["chatbot"].select.return_value.eq
    listed_eq = id_eq.return_value.eq
    withdrawn_eq = listed_eq.return_value.eq
    return id_eq, listed_eq, withdrawn_eq


def _set_product(tables, rows):
    _product_chain(tables)[-1].return_value.execute.return_value = _db_result(rows)


# 購入済み確認: select → eq(buyer_id) → eq(chatbot_id) → limit → execute
def _purchase_chain(tables):
    buyer_eq = tables["purchases"].select.return_value.eq
    id_eq = buyer_eq.return_value.eq
    limit = id_eq.return_value.limit
    return buyer_eq, id_eq, limit


def _set_purchases(tables, rows):
    _purchase_chain(tables)[-1].return_value.execute.return_value = _db_result(rows)


def _insert(tables):
    return tables["cart"].insert


def _setup_post(db, product_rows=None, purchase_rows=None):
    """出品中の他人の商品・未購入、を初期状態にする"""
    tables = _tables(db)
    if product_rows is None:
        product_rows = [{"chatbot_id": CHATBOT_ID, "creator_id": "seller01"}]
    _set_product(tables, product_rows)
    _set_purchases(tables, purchase_rows or [])
    return tables


def test_add_to_cart_inserts_row(client):
    with _login(), patch("cart.routes.supabase") as db:
        tables = _setup_post(db)

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID})

        id_eq, listed_eq, withdrawn_eq = _product_chain(tables)
        id_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)
        listed_eq.assert_called_once_with("is_listed", True)
        withdrawn_eq.assert_called_once_with("users.is_withdrawn", False)

        buyer_eq, purchase_id_eq, _ = _purchase_chain(tables)
        buyer_eq.assert_called_once_with("buyer_id", "buyer01")
        purchase_id_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

        _insert(tables).assert_called_once_with({"chatbot_id": CHATBOT_ID, "user_id": "buyer01"})

    assert response.status_code == 201
    assert response.get_json() == {"chatbot_id": CHATBOT_ID}


def test_add_to_cart_normalizes_chatbot_id(client):
    with _login(), patch("cart.routes.supabase") as db:
        tables = _setup_post(db)

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID.upper()})

        _insert(tables).assert_called_once_with({"chatbot_id": CHATBOT_ID, "user_id": "buyer01"})

    assert response.status_code == 201


@pytest.mark.parametrize(
    "body",
    [None, {}, {"chatbot_id": "abc"}, {"chatbot_id": 123}, ["not", "dict"]],
)
def test_add_to_cart_returns_400_for_invalid_id(client, body):
    with _login(), patch("cart.routes.supabase") as db:
        response = client.post("/api/cart", json=body)

        db.table.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "無効なchatbot_idです"


def test_add_to_cart_returns_404_when_product_not_listed(client):
    with _login(), patch("cart.routes.supabase") as db:
        tables = _setup_post(db, product_rows=[])

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID})

        _insert(tables).assert_not_called()

    assert response.status_code == 404
    assert response.get_json()["error"] == "商品が見つかりません"


def test_add_to_cart_blocks_own_product(client):
    with _login(), patch("cart.routes.supabase") as db:
        tables = _setup_post(db, product_rows=[{"chatbot_id": CHATBOT_ID, "creator_id": "buyer01"}])

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID})

        _insert(tables).assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "自分の商品はカートに入れられません"


def test_add_to_cart_blocks_purchased_product(client):
    with _login(), patch("cart.routes.supabase") as db:
        # is_deleted(購入履歴の非表示)の有無に関係なく弾くため、条件に含めていないことも確認する
        tables = _setup_post(db, purchase_rows=[{"purchase_id": "p1"}])

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID})

        _, purchase_id_eq, _ = _purchase_chain(tables)
        purchase_id_eq.return_value.eq.assert_not_called()
        _insert(tables).assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "この商品はすでに購入済みです"


def test_add_to_cart_returns_409_when_already_in_cart(client):
    with _login(), patch("cart.routes.supabase") as db:
        tables = _setup_post(db)
        _insert(tables).return_value.execute.side_effect = APIError(
            {"code": "23505", "message": "duplicate key value violates unique constraint"}
        )

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID})

    assert response.status_code == 409
    assert response.get_json()["error"] == "この商品はすでにカートに入っています"


def test_add_to_cart_returns_500_for_other_db_errors(client):
    with _login(), patch("cart.routes.supabase") as db:
        tables = _setup_post(db)
        _insert(tables).return_value.execute.side_effect = APIError(
            {"code": "23503", "message": "foreign key violation"}
        )

        response = client.post("/api/cart", json={"chatbot_id": CHATBOT_ID})

    assert response.status_code == 500


# ============================================================
# DELETE /api/cart/<chatbot_id>
# ============================================================


# table → delete → eq(user_id) → eq(chatbot_id) → execute
def _delete_one_chain(db):
    user_eq = db.table.return_value.delete.return_value.eq
    id_eq = user_eq.return_value.eq
    return user_eq, id_eq


def test_remove_from_cart_deletes_row(client):
    with _login(), patch("cart.routes.supabase") as db:
        user_eq, id_eq = _delete_one_chain(db)
        id_eq.return_value.execute.return_value = _db_result([{"cart_id": 1}])

        response = client.delete(f"/api/cart/{CHATBOT_ID}")

        db.table.assert_called_once_with("cart")
        user_eq.assert_called_once_with("user_id", "buyer01")
        id_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)

    assert response.status_code == 200
    assert response.get_json() == {"chatbot_id": CHATBOT_ID}


def test_remove_from_cart_returns_404_when_not_in_cart(client):
    with _login(), patch("cart.routes.supabase") as db:
        _delete_one_chain(db)[1].return_value.execute.return_value = _db_result([])

        response = client.delete(f"/api/cart/{CHATBOT_ID}")

    assert response.status_code == 404
    assert response.get_json()["error"] == "カートにこの商品はありません"


def test_remove_from_cart_returns_400_for_invalid_id(client):
    with _login(), patch("cart.routes.supabase") as db:
        response = client.delete("/api/cart/abc")

        db.table.assert_not_called()

    assert response.status_code == 400


# ============================================================
# DELETE /api/cart
# ============================================================


def test_clear_cart_deletes_only_own_rows(client):
    with _login(), patch("cart.routes.supabase") as db:
        user_eq = db.table.return_value.delete.return_value.eq
        user_eq.return_value.execute.return_value = _db_result([{"cart_id": 1}, {"cart_id": 2}])

        response = client.delete("/api/cart")

        db.table.assert_called_once_with("cart")
        user_eq.assert_called_once_with("user_id", "buyer01")

    assert response.status_code == 200
    assert response.get_json() == {"deleted_count": 2}
