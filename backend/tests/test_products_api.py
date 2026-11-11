from unittest.mock import MagicMock, call, patch

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


def _search_value(word):
    """1単語の検索条件(テストの期待値)"""
    return f'or(bot_name.ilike."*{word}*",description.ilike."*{word}*")'


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


@pytest.mark.parametrize("raw, expected", [("3", 3), ("1", 1), ("32767", 32767), ("03", 3)])
def test_list_products_filters_by_category(client, raw, expected):
    response, query, _ = _get(client, f"/api/products?category_id={raw}", [_db_row()])

    assert query.eq.call_args_list == BASE_FILTERS + [call("category_id", expected)]
    assert response.status_code == 200


def test_list_products_returns_empty_for_unknown_category(client):
    response, _, _ = _get(client, "/api/products?category_id=999")

    assert response.status_code == 200
    assert response.get_json() == []


@pytest.mark.parametrize(
    "raw",
    ["abc", "1.5", "0", "-1", "32768", "99999", "%201%20", "+1", "", "１"],
)
def test_list_products_returns_400_for_invalid_category(client, raw):
    response, _, db = _get(client, f"/api/products?category_id={raw}")

    db.table.assert_not_called()
    assert response.status_code == 400
    assert response.get_json()["error"] == CATEGORY_ID_ERROR


# ============================================================
# 一覧: 検索
# ============================================================


def test_list_products_searches_single_word(client):
    response, query, _ = _get(client, "/api/products?q=英語", [_db_row()])

    query.or_.assert_called_once_with(f"and({_search_value('英語')})")
    assert response.status_code == 200


def test_list_products_searches_all_words(client):
    # 連続する半角スペースも1つの区切りとして扱う
    _, query, _ = _get(client, "/api/products?q=英語%20%20%20練習")

    query.or_.assert_called_once_with(
        f"and({_search_value('英語')},{_search_value('練習')})"
    )


def test_list_products_does_not_split_on_fullwidth_space(client):
    _, query, _ = _get(client, "/api/products?q=英語　練習")

    query.or_.assert_called_once_with(f"and({_search_value('英語　練習')})")


def test_list_products_escapes_special_characters(client):
    # % _ \ はLIKE用にエスケープし、さらに \ と " はPostgREST用にエスケープする
    _, query, _ = _get(client, "/api/products?q=" + "100%25_a,(b)%22c%5Cd%26e")

    expected = '100\\\\%\\\\_a,(b)\\"c\\\\\\\\d&e'
    query.or_.assert_called_once_with(f"and({_search_value(expected)})")


def test_list_products_removes_asterisk_and_joins(client):
    _, query, _ = _get(client, "/api/products?q=a*b")

    query.or_.assert_called_once_with(f"and({_search_value('ab')})")


@pytest.mark.parametrize("raw", ["", "%20%20%20", "***", "*%20*"])
def test_list_products_skips_search_for_empty_keyword(client, raw):
    response, query, _ = _get(client, f"/api/products?q={raw}")

    query.or_.assert_not_called()
    assert response.status_code == 200


def test_list_products_cuts_keyword_to_60_characters(client):
    _, query, _ = _get(client, "/api/products?q=" + "あ" * 70)

    query.or_.assert_called_once_with(f"and({_search_value('あ' * 60)})")


def test_list_products_strips_spaces_before_cutting(client):
    _, query, _ = _get(client, "/api/products?q=%20%20" + "あ" * 60 + "い")

    query.or_.assert_called_once_with(f"and({_search_value('あ' * 60)})")


def test_list_products_combines_category_search_and_paging(client):
    response, query, _ = _get(client, "/api/products?category_id=2&q=英語&limit=5&offset=5")

    assert query.eq.call_args_list == BASE_FILTERS + [call("category_id", 2)]
    query.or_.assert_called_once_with(f"and({_search_value('英語')})")
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