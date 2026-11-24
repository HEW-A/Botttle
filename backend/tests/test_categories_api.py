from unittest.mock import MagicMock, call, patch

import pytest

from app import create_app

# routes.py の COUNT_COLUMNS・PAGE_SIZE とは、意図して重複させている。
# 列名や外部キー名のタイポ、分割取得の件数の変更を検知するため、期待値はテスト側に直接書く。
EXPECTED_CATEGORY_COLUMNS = "category_id, category_name"
EXPECTED_COUNT_COLUMNS = "category_id, users!chatbot_creator_id_fkey!inner(user_id)"
LISTED_FILTERS = [call("is_listed", True), call("users.is_withdrawn", False)]
PAGE_SIZE = 1000


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
    """
    select / eq / order / range を何回呼んでも同じモックを返すクエリ。
    execute() は呼ばれるたびに、pages の1ページ目から順に返す。
    """
    query = MagicMock()
    for name in ("select", "eq", "order", "range"):
        getattr(query, name).return_value = query
    query.execute.side_effect = [_db_result(list(page)) for page in pages]
    return query


def _category_rows(*items):
    return [{"category_id": cid, "category_name": name} for cid, name in items]


def _product_rows(*category_ids):
    """カテゴリ件数用の商品の行(users は結合の都合で入っているだけ)"""
    return [{"category_id": cid, "users": {"user_id": "u"}} for cid in category_ids]


def _get(client, categories, *product_pages):
    """
    supabase をモックにしてGETし、(レスポンス, カテゴリのクエリ, 商品のクエリ, db) を返す。
    product_pages には、商品の取得結果をページごとに渡す。
    """
    category_query = _chain(categories)
    product_query = _chain(*product_pages)
    with patch("categories.routes.supabase") as db:
        db.table.side_effect = lambda name: {
            "category": category_query,
            "chatbot": product_query,
        }[name]
        response = client.get("/api/categories")
    return response, category_query, product_query, db


# ============================================================
# 一覧
# ============================================================


def test_list_categories_returns_name_and_product_count(client):
    categories = _category_rows((1, "カスタマーサポート型"), (2, "予約・受付型"))
    response, category_query, _, _ = _get(client, categories, _product_rows(1, 1, 2))

    category_query.select.assert_called_once_with(EXPECTED_CATEGORY_COLUMNS)
    assert response.status_code == 200
    assert response.get_json() == [
        {"category_id": 1, "category_name": "カスタマーサポート型", "product_count": 2},
        {"category_id": 2, "category_name": "予約・受付型", "product_count": 1},
    ]


def test_list_categories_orders_by_category_id(client):
    categories = _category_rows((1, "A"), (2, "B"), (3, "C"))
    response, category_query, _, _ = _get(client, categories, [])

    category_query.order.assert_called_once_with("category_id")
    # DBの並び順をそのまま返す(Python側で並べ替えない)
    assert [item["category_id"] for item in response.get_json()] == [1, 2, 3]


def test_list_categories_returns_zero_for_category_without_products(client):
    categories = _category_rows((1, "A"), (2, "B"), (3, "C"))
    response, _, _, _ = _get(client, categories, _product_rows(2))

    assert [item["product_count"] for item in response.get_json()] == [0, 1, 0]


def test_list_categories_returns_empty_list_when_no_categories(client):
    response, _, _, _ = _get(client, [], _product_rows(1, 2))

    assert response.status_code == 200
    assert response.get_json() == []


def test_list_categories_does_not_require_login(client):
    # Cookie も認証ヘッダーも付けずに呼べる
    response, _, _, _ = _get(client, _category_rows((1, "A")), [])

    assert response.status_code == 200


# ============================================================
# 商品数の数え方
# ============================================================


def test_list_categories_counts_only_listed_products_of_active_users(client):
    _, _, product_query, db = _get(client, _category_rows((1, "A")), _product_rows(1))

    assert [c.args[0] for c in db.table.call_args_list] == ["category", "chatbot"]
    product_query.select.assert_called_once_with(EXPECTED_COUNT_COLUMNS)
    assert product_query.eq.call_args_list == LISTED_FILTERS
    # 分割取得の途中で並びが変わらないよう、主キーで並べる
    product_query.order.assert_called_once_with("chatbot_id")


def test_list_categories_ignores_products_without_category(client):
    categories = _category_rows((1, "A"))
    response, _, _, _ = _get(client, categories, _product_rows(1, None, None))

    assert response.status_code == 200
    assert response.get_json()[0]["product_count"] == 1


def test_list_categories_ignores_unknown_category_ids(client):
    # category テーブルにない category_id の商品は、一覧に出ない
    categories = _category_rows((1, "A"))
    response, _, _, _ = _get(client, categories, _product_rows(1, 99, 99))

    assert response.get_json() == [
        {"category_id": 1, "category_name": "A", "product_count": 1}
    ]


def test_list_categories_fetches_all_pages(client):
    # 1ページ目が満杯なら、次のページも取りに行く
    categories = _category_rows((1, "A"), (2, "B"))
    first_page = _product_rows(*([1] * PAGE_SIZE))
    second_page = _product_rows(1, 1, 2)
    response, _, product_query, _ = _get(client, categories, first_page, second_page)

    assert product_query.range.call_args_list == [
        call(0, PAGE_SIZE - 1),
        call(PAGE_SIZE, PAGE_SIZE * 2 - 1),
    ]
    assert [item["product_count"] for item in response.get_json()] == [PAGE_SIZE + 2, 1]


def test_list_categories_fetches_next_page_when_first_page_is_exactly_full(client):
    # ちょうど満杯のときは、次が空かどうか確かめるまで終わらない
    categories = _category_rows((1, "A"))
    response, _, product_query, _ = _get(
        client, categories, _product_rows(*([1] * PAGE_SIZE)), []
    )

    assert product_query.range.call_count == 2
    assert response.get_json()[0]["product_count"] == PAGE_SIZE


def test_list_categories_stops_after_first_page_when_not_full(client):
    categories = _category_rows((1, "A"))
    _, _, product_query, _ = _get(client, categories, _product_rows(*([1] * (PAGE_SIZE - 1))))

    product_query.range.assert_called_once_with(0, PAGE_SIZE - 1)