from unittest.mock import MagicMock, call, patch

import pytest

from app import create_app

# routes.py の COUNT_COLUMNS とは、意図して重複させている(タイポ検知のため)
EXPECTED_COUNT_COLUMNS = "category_id, users!chatbot_creator_id_fkey!inner(user_id)"


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _db_result(rows):
    result = MagicMock()
    result.data = rows
    return result


def _chain(*pages):
    """メソッドを何回呼んでも同じモックを返し、execute はページを順に返すクエリ"""
    query = MagicMock()
    for name in ("select", "eq", "order", "range"):
        getattr(query, name).return_value = query
    query.execute.side_effect = [_db_result(rows) for rows in pages]
    return query


def _get(client, categories, *chatbot_pages):
    category_query = _chain(categories)
    chatbot_query = _chain(*chatbot_pages)
    queries = {"category": category_query, "chatbot": chatbot_query}

    with patch("categories.routes.supabase") as db:
        db.table.side_effect = lambda name: queries[name]
        response = client.get("/api/categories")
    return response, category_query, chatbot_query


CATEGORIES = [
    {"category_id": 1, "category_name": "カスタマーサポート型"},
    {"category_id": 2, "category_name": "予約・受付型"},
    {"category_id": 3, "category_name": "学習・教育型"},
]


def test_list_categories_returns_counts_including_zero(client):
    chatbots = [
        {"category_id": 1, "users": {"user_id": "a"}},
        {"category_id": 3, "users": {"user_id": "b"}},
        {"category_id": 1, "users": {"user_id": "c"}},
        {"category_id": None, "users": {"user_id": "d"}},  # カテゴリ未設定は数えない
    ]
    response, _, _ = _get(client, CATEGORIES, chatbots)

    assert response.status_code == 200
    assert response.get_json() == [
        {"category_id": 1, "category_name": "カスタマーサポート型", "product_count": 2},
        {"category_id": 2, "category_name": "予約・受付型", "product_count": 0},
        {"category_id": 3, "category_name": "学習・教育型", "product_count": 1},
    ]


def test_list_categories_queries_db_correctly(client):
    _, category_query, chatbot_query = _get(client, CATEGORIES, [])

    category_query.select.assert_called_once_with("category_id, category_name")
    category_query.order.assert_called_once_with("category_id")

    chatbot_query.select.assert_called_once_with(EXPECTED_COUNT_COLUMNS)
    assert chatbot_query.eq.call_args_list == [
        call("is_listed", True),
        call("users.is_withdrawn", False),
    ]
    chatbot_query.order.assert_called_once_with("chatbot_id")
    chatbot_query.range.assert_called_once_with(0, 999)


def test_list_categories_returns_empty_when_no_category(client):
    response, _, _ = _get(client, [], [])

    assert response.status_code == 200
    assert response.get_json() == []


def test_list_categories_counts_across_pages(client):
    first_page = [{"category_id": 1, "users": {"user_id": "x"}}] * 1000
    second_page = [{"category_id": 1, "users": {"user_id": "y"}}] * 5
    response, _, chatbot_query = _get(client, CATEGORIES, first_page, second_page)

    assert chatbot_query.range.call_args_list == [call(0, 999), call(1000, 1999)]
    assert response.get_json()[0]["product_count"] == 1005


@pytest.mark.parametrize("page_size", [0, 999])
def test_list_categories_stops_when_page_is_not_full(client, page_size):
    page = [{"category_id": 2, "users": {"user_id": "z"}}] * page_size
    response, _, chatbot_query = _get(client, CATEGORIES, page)

    chatbot_query.range.assert_called_once_with(0, 999)
    assert response.get_json()[1]["product_count"] == page_size