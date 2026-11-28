from unittest.mock import MagicMock, call, patch
from urllib.parse import quote

import pytest

from app import create_app

CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"

# routes.py の PRODUCT_COLUMNS とは、意図して重複させている。
# 列名や外部キー名のタイポを検知するため、期待値はテスト側に直接書く。
EXPECTED_COLUMNS = (
    "chatbot_id, bot_name, price, description, thumbnail_url, category_id, "
    "users!chatbot_creator_id_fkey!inner(username), "
    "category(category_name)"
)
BASE_FILTERS = [call("is_listed", True), call("users.is_withdrawn", False)]
CATEGORY_ID_ERROR = "category_id は1〜32767の整数で指定してください"


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _db_result(rows):
    result = MagicMock()
    result.data = rows
    return result


def _chain(rows):
    """select / eq / or_ / order / range を何回呼んでも同じモックを返すクエリ"""
    query = MagicMock()
    for name in ("select", "eq", "or_", "order", "range"):
        getattr(query, name).return_value = query
    query.execute.return_value = _db_result(rows)
    return query


def _db_row(**overrides):
    row = {
        "chatbot_id": CHATBOT_ID,
        "bot_name": "テストボット",
        "price": 1000,
        "description": "説明文",
        "thumbnail_url": None,
        "category_id": 3,
        "users": {"username": "taro"},
        "category": {"category_name": "学習・教育型"},
    }
    row.update(overrides)
    return row


def _get(client, url, rows=()):
    """supabase をモックにしてGETし、(レスポンス, クエリ, db) を返す"""
    with patch("products.routes.supabase") as db:
        query = _chain(list(rows))
        db.table.return_value = query
        response = client.get(url)
    return response, query, db


# ============================================================
# 一覧
# ============================================================


def test_list_products_returns_flat_items(client):
    response, query, db = _get(client, "/api/products", [_db_row(auth_email="secret@example.com")])

    db.table.assert_called_once_with("chatbot")
    query.select.assert_called_once_with(EXPECTED_COLUMNS)
    assert query.eq.call_args_list == BASE_FILTERS
    query.or_.assert_not_called()
    assert query.order.call_args_list == [
        call("create_at", desc=True),
        call("chatbot_id", desc=True),
    ]
    query.range.assert_called_once_with(0, 19)

    assert response.status_code == 200
    assert response.get_json() == [
        {
            "chatbot_id": CHATBOT_ID,
            "bot_name": "テストボット",
            "price": 1000,
            "description": "説明文",
            "thumbnail_url": None,
            "category_id": 3,
            "username": "taro",
            "category_name": "学習・教育型",
        }
    ]


def test_list_products_handles_missing_user_and_category(client):
    row = _db_row(users=None, category=None, category_id=None)
    response, _, _ = _get(client, "/api/products", [row])

    assert response.status_code == 200
    body = response.get_json()
    assert body[0]["username"] is None
    assert body[0]["category_id"] is None
    assert body[0]["category_name"] is None


def test_list_products_passes_limit_and_offset_to_range(client):
    response, query, _ = _get(client, "/api/products?limit=5&offset=10")

    query.range.assert_called_once_with(10, 14)
    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize("query_string", ["limit=0", "limit=101", "limit=abc", "offset=-1", "offset=abc"])
def test_list_products_returns_400_for_invalid_paging(client, query_string):
    response, _, db = _get(client, f"/api/products?{query_string}")

    db.table.assert_not_called()
    assert response.status_code == 400
    assert "limit" in response.get_json()["error"]


# ============================================================
# 一覧: カテゴリの絞り込み
# ============================================================


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("3", 3),
        ("1", 1),
        ("32767", 32767),
        ("03", 3),
        # 先頭の半角スペース1個だけは無視する
        ("%201", 1),
        ("%2003", 3),
    ],
)
def test_list_products_filters_by_category(client, raw, expected):
    response, query, _ = _get(client, f"/api/products?category_id={raw}", [_db_row()])

    assert query.eq.call_args_list == BASE_FILTERS + [call("category_id", expected)]
    assert response.status_code == 200


@pytest.mark.parametrize("raw", ["", "%20", "%20%20%20"])
def test_list_products_skips_category_filter_for_empty_value(client, raw):
    # 空・半角スペースだけ(何個でも)は「指定なし」として扱う
    response, query, db = _get(client, f"/api/products?category_id={raw}", [_db_row()])

    db.table.assert_called_once_with("chatbot")
    assert query.eq.call_args_list == BASE_FILTERS
    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_list_products_returns_empty_for_unknown_category(client):
    response, _, _ = _get(client, "/api/products?category_id=999")

    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize(
    "raw",
    [
        "abc",
        "1.5",
        "0",
        "-1",
        "32768",
        "99999",
        "%2B1",  # 符号つき(URLの + は空白になるため %2B で送る)
        "１",  # 全角数字
        "1%20",  # 後ろに空白
        "%201%20",  # 前後に空白
        "%20%201",  # 先頭に空白が2個以上
        "%E3%80%801",  # 先頭に全角スペース
        "%E3%80%80",  # 全角スペースだけ
    ],
)
def test_list_products_returns_400_for_invalid_category(client, raw):
    response, _, db = _get(client, f"/api/products?category_id={raw}")

    db.table.assert_not_called()
    assert response.status_code == 400
    assert response.get_json()["error"] == CATEGORY_ID_ERROR


def test_list_products_combines_category_and_paging(client):
    response, query, _ = _get(client, "/api/products?category_id=2&limit=5&offset=5")

    assert query.eq.call_args_list == BASE_FILTERS + [call("category_id", 2)]
    query.range.assert_called_once_with(5, 9)
    assert response.status_code == 200


# ============================================================
# 詳細
# ============================================================


def test_get_product_returns_item(client):
    response, query, _ = _get(client, f"/api/products/{CHATBOT_ID}", [_db_row(auth_email="secret@example.com")])

    query.select.assert_called_once_with(EXPECTED_COLUMNS)
    assert query.eq.call_args_list == BASE_FILTERS + [call("chatbot_id", CHATBOT_ID)]

    assert response.status_code == 200
    body = response.get_json()
    assert body["bot_name"] == "テストボット"
    assert body["username"] == "taro"
    assert body["category_id"] == 3
    assert "auth_email" not in body


def test_get_product_returns_404_when_not_found(client):
    response, _, _ = _get(client, "/api/products/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.get_json()["error"] == "商品が見つかりません"


def test_get_product_returns_400_for_invalid_id(client):
    response, _, db = _get(client, "/api/products/abc")

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
    response, query, _ = _get(client, f"/api/products/{raw_id}", [_db_row()])

    assert query.eq.call_args_list[-1] == call("chatbot_id", CHATBOT_ID)
    assert response.status_code == 200


# ============================================================
# 検索(一覧API に q を付けた場合)
# ============================================================


def _rpc_row(**overrides):
    row = {
        "chatbot_id": CHATBOT_ID,
        "bot_name": "プログラミング先生",
        "price": 500,
        "description": "やさしく教えます",
        "thumbnail_url": None,
        "category_id": 3,
        "username": "taro",
        "category_name": "学習・教育型",
    }
    row.update(overrides)
    return row


def _set_search_rows(db, rows):
    db.rpc.return_value.execute.return_value = _db_result(rows)


def test_search_calls_rpc_and_returns_flat_items(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [_rpc_row(extra="ignored")])

        response = client.get("/api/products?q=プログラミング")

        db.rpc.assert_called_once_with(
            "search_products",
            {
                "p_query": "プログラミング",
                "p_terms": ["プログラミング"],
                "p_category_id": None,
                "p_limit": 20,
                "p_offset": 0,
            },
        )
        db.table.assert_not_called()

    assert response.status_code == 200
    assert response.get_json() == [
        {
            "chatbot_id": CHATBOT_ID,
            "bot_name": "プログラミング先生",
            "price": 500,
            "description": "やさしく教えます",
            "thumbnail_url": None,
            "category_id": 3,
            "username": "taro",
            "category_name": "学習・教育型",
        }
    ]


def test_search_splits_terms_by_half_and_full_width_spaces(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [])

        response = client.get("/api/products", query_string={"q": "  プログラミング　簡単  Python "})

        args = db.rpc.call_args.args[1]
        assert args["p_query"] == "プログラミング　簡単  Python"
        assert args["p_terms"] == ["プログラミング", "簡単", "Python"]

    assert response.status_code == 200
    assert response.get_json() == []


def test_search_removes_duplicate_terms_ignoring_case(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [])

        client.get("/api/products", query_string={"q": "Python python 入門 PYTHON"})

        assert db.rpc.call_args.args[1]["p_terms"] == ["Python", "入門"]


def test_search_passes_special_characters_as_is(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [])

        client.get("/api/products", query_string={"q": "100% a_b (x,y)"})

        assert db.rpc.call_args.args[1]["p_terms"] == ["100%", "a_b", "(x,y)"]


def test_search_passes_limit_and_offset(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [])

        client.get("/api/products?q=bot&limit=5&offset=10")

        args = db.rpc.call_args.args[1]
        assert args["p_limit"] == 5
        assert args["p_offset"] == 10


@pytest.mark.parametrize("q", ["", "   ", "　"])
def test_search_with_blank_query_returns_normal_list(client, q):
    response, query, db = _get(client, f"/api/products?q={quote(q)}", [_db_row()])

    db.rpc.assert_not_called()
    query.range.assert_called_once_with(0, 19)

    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_search_returns_400_for_too_long_query(client):
    with patch("products.routes.supabase") as db:
        response = client.get("/api/products", query_string={"q": "あ" * 101})

        db.rpc.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "検索キーワードは100文字以内で指定してください"


def test_search_accepts_query_of_max_length(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [])

        response = client.get("/api/products", query_string={"q": "あ" * 100})

    assert response.status_code == 200


def test_search_returns_400_for_too_many_terms(client):
    q = " ".join(f"w{i}" for i in range(11))

    with patch("products.routes.supabase") as db:
        response = client.get("/api/products", query_string={"q": q})

        db.rpc.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == "検索キーワードは10語以内で指定してください"


def test_search_checks_paging_before_query(client):
    with patch("products.routes.supabase") as db:
        response = client.get("/api/products?q=bot&limit=0")

        db.rpc.assert_not_called()

    assert response.status_code == 400
    assert "limit" in response.get_json()["error"]


def test_search_passes_category_id(client):
    with patch("products.routes.supabase") as db:
        _set_search_rows(db, [])

        response = client.get("/api/products?q=bot&category_id=3")

        assert db.rpc.call_args.args[1]["p_category_id"] == 3

    assert response.status_code == 200


def test_search_checks_category_before_query(client):
    with patch("products.routes.supabase") as db:
        response = client.get("/api/products?q=bot&category_id=abc")

        db.rpc.assert_not_called()

    assert response.status_code == 400
    assert response.get_json()["error"] == CATEGORY_ID_ERROR
