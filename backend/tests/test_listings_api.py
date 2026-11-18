import io
from unittest.mock import MagicMock, patch

import pytest
from werkzeug.datastructures import FileStorage

from app import create_app
from listings.routes import _find_owned_bot, _read_thumbnail, _upload_thumbnail


CHATBOT_ID = "59e511a0-efcf-4aa8-98cf-d6fa5786e52b"
USER = {"user_id": "seller01", "username": "seller"}
BOT = {
    "chatbot_id": CHATBOT_ID,
    "bot_name": "作成済みBot",
    "creator_id": "seller01",
    "price": None,
    "description": "作成時の説明",
    "category_id": None,
    "thumbnail_url": None,
    "is_listed": False,
}
CATEGORIES = [{"category_id": 1, "category_name": "学習・教育型"}]


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _login(user=USER):
    return patch("listings.routes.get_current_user", return_value=user)


def _valid_form(**overrides):
    values = {
        "bot_name": "出品Bot",
        "category_id": "1",
        "price": "3000",
        "description": "商品の説明です",
    }
    values.update(overrides)
    return values


def _db_result(rows):
    result = MagicMock()
    result.data = rows
    return result


def _set_update_result(db, rows):
    execute = (
        db.table.return_value.update.return_value.eq.return_value.eq.return_value.execute
    )
    execute.return_value = _db_result(rows)
    return execute


def test_find_owned_bot_filters_by_chatbot_and_creator():
    with patch("listings.routes.supabase") as db:
        first_eq = db.table.return_value.select.return_value.eq
        second_eq = first_eq.return_value.eq
        limit = second_eq.return_value.limit
        limit.return_value.execute.return_value = _db_result([BOT])

        result = _find_owned_bot(CHATBOT_ID, "seller01")

        db.table.assert_called_once_with("chatbot")
        first_eq.assert_called_once_with("chatbot_id", CHATBOT_ID)
        second_eq.assert_called_once_with("creator_id", "seller01")
        limit.assert_called_once_with(1)

    assert result == BOT


def test_get_listing_requires_login(client):
    with _login(None), patch("listings.routes._find_owned_bot") as find:
        response = client.get(f"/api/listings/{CHATBOT_ID}")
        find.assert_not_called()

    assert response.status_code == 401


def test_get_listing_rejects_invalid_id(client):
    with _login(), patch("listings.routes._find_owned_bot") as find:
        response = client.get("/api/listings/not-a-uuid")
        find.assert_not_called()

    assert response.status_code == 400


def test_get_listing_returns_404_for_non_owner(client):
    with _login(), patch("listings.routes._find_owned_bot", return_value=None):
        response = client.get(f"/api/listings/{CHATBOT_ID}")

    assert response.status_code == 404


def test_get_listing_returns_owned_bot_and_categories(client):
    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT) as find,
        patch("listings.routes._list_categories", return_value=CATEGORIES),
    ):
        response = client.get(f"/api/listings/{CHATBOT_ID.upper()}")
        find.assert_called_once_with(CHATBOT_ID, "seller01")

    assert response.status_code == 200
    assert response.get_json() == {"chatbot": BOT, "categories": CATEGORIES}


def test_publish_requires_login(client):
    with _login(None), patch("listings.routes._find_owned_bot") as find:
        response = client.put(f"/api/listings/{CHATBOT_ID}", data=_valid_form())
        find.assert_not_called()

    assert response.status_code == 401


def test_publish_rejects_invalid_id(client):
    with _login(), patch("listings.routes._find_owned_bot") as find:
        response = client.put("/api/listings/not-a-uuid", data=_valid_form())
        find.assert_not_called()

    assert response.status_code == 400


def test_publish_returns_404_for_non_owner(client):
    with _login(), patch("listings.routes._find_owned_bot", return_value=None):
        response = client.put(f"/api/listings/{CHATBOT_ID}", data=_valid_form())

    assert response.status_code == 404


@pytest.mark.parametrize(
    ("overrides", "message"),
    [
        ({"bot_name": ""}, "商品名"),
        ({"bot_name": "a" * 41}, "40文字"),
        ({"description": ""}, "説明文"),
        ({"description": "a" * 5001}, "5000文字"),
        ({"price": ""}, "販売価格"),
        ({"price": "0"}, "販売価格"),
        ({"price": "1.5"}, "販売価格"),
        ({"price": "03"}, "販売価格"),
        ({"category_id": ""}, "カテゴリ"),
        ({"category_id": "abc"}, "カテゴリ"),
    ],
)
def test_publish_validates_form(client, overrides, message):
    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists") as category_exists,
    ):
        response = client.put(
            f"/api/listings/{CHATBOT_ID}", data=_valid_form(**overrides)
        )
        category_exists.assert_not_called()

    assert response.status_code == 400
    assert message in response.get_json()["error"]


def test_publish_rejects_unknown_category(client):
    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists", return_value=False),
    ):
        response = client.put(f"/api/listings/{CHATBOT_ID}", data=_valid_form())

    assert response.status_code == 400
    assert response.get_json()["error"] == "指定されたカテゴリが見つかりません"


def test_publish_rejects_invalid_thumbnail(client):
    data = _valid_form()
    data["thumbnail"] = (io.BytesIO(b"not an image"), "fake.png")

    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists", return_value=True),
    ):
        response = client.put(
            f"/api/listings/{CHATBOT_ID}",
            data=data,
            content_type="multipart/form-data",
        )

    assert response.status_code == 400
    assert "JPEG、PNG、WebP" in response.get_json()["error"]


def test_publish_without_thumbnail_updates_owned_bot(client):
    saved = {**BOT, **_valid_form(), "category_id": 1, "price": 3000, "is_listed": True}

    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists", return_value=True),
        patch("listings.routes.supabase") as db,
    ):
        _set_update_result(db, [saved])
        response = client.put(f"/api/listings/{CHATBOT_ID}", data=_valid_form())

        update_values = db.table.return_value.update.call_args.args[0]
        assert update_values["bot_name"] == "出品Bot"
        assert update_values["price"] == 3000
        assert update_values["category_id"] == 1
        assert update_values["is_listed"] is True
        assert "thumbnail_url" not in update_values
        assert "update_at" in update_values
        db.table.return_value.update.return_value.eq.assert_called_once_with(
            "chatbot_id", CHATBOT_ID
        )
        db.table.return_value.update.return_value.eq.return_value.eq.assert_called_once_with(
            "creator_id", "seller01"
        )

    assert response.status_code == 200


def test_publish_with_thumbnail_stores_public_url(client):
    saved = {**BOT, "thumbnail_url": "https://example.test/image.png", "is_listed": True}
    thumbnail = (io.BytesIO(b"\x89PNG\r\n\x1a\ncontent"), "image.png")
    data = {**_valid_form(), "thumbnail": thumbnail}

    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists", return_value=True),
        patch(
            "listings.routes._upload_thumbnail",
            return_value=("path/image.png", "https://example.test/image.png"),
        ),
        patch("listings.routes.supabase") as db,
    ):
        _set_update_result(db, [saved])
        response = client.put(
            f"/api/listings/{CHATBOT_ID}",
            data=data,
            content_type="multipart/form-data",
        )

        update_values = db.table.return_value.update.call_args.args[0]
        assert update_values["thumbnail_url"] == "https://example.test/image.png"

    assert response.status_code == 200


def test_publish_returns_500_when_thumbnail_upload_fails(client):
    thumbnail = (io.BytesIO(b"\x89PNG\r\n\x1a\ncontent"), "image.png")
    data = {**_valid_form(), "thumbnail": thumbnail}

    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists", return_value=True),
        patch(
            "listings.routes._upload_thumbnail",
            side_effect=Exception("storage error"),
        ),
    ):
        response = client.put(
            f"/api/listings/{CHATBOT_ID}",
            data=data,
            content_type="multipart/form-data",
        )

    assert response.status_code == 500
    assert response.get_json() == {"error": "サムネイル画像の保存に失敗しました"}


def test_publish_removes_uploaded_thumbnail_when_db_update_fails(client):
    thumbnail = (io.BytesIO(b"\x89PNG\r\n\x1a\ncontent"), "image.png")
    data = {**_valid_form(), "thumbnail": thumbnail}

    with (
        _login(),
        patch("listings.routes._find_owned_bot", return_value=BOT),
        patch("listings.routes._category_exists", return_value=True),
        patch(
            "listings.routes._upload_thumbnail",
            return_value=("path/image.png", "https://example.test/image.png"),
        ),
        patch("listings.routes.supabase") as db,
    ):
        execute = _set_update_result(db, [])
        execute.side_effect = Exception("db error")

        response = client.put(
            f"/api/listings/{CHATBOT_ID}",
            data=data,
            content_type="multipart/form-data",
        )

        db.storage.from_.return_value.remove.assert_called_once_with(["path/image.png"])

    assert response.status_code == 500


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b"\x89PNG\r\n\x1a\ncontent", ("image/png", "png")),
        (b"\xff\xd8\xffcontent", ("image/jpeg", "jpg")),
        (b"RIFF1234WEBPcontent", ("image/webp", "webp")),
    ],
)
def test_read_thumbnail_detects_file_content(content, expected):
    file = FileStorage(stream=io.BytesIO(content), filename="image.bin")
    thumbnail = _read_thumbnail(file)

    assert thumbnail[1:] == expected


def test_upload_thumbnail_uses_bot_folder_and_public_url():
    with (
        patch("listings.routes.supabase") as db,
        patch("listings.routes.uuid.uuid4", return_value="image-uuid"),
    ):
        bucket = db.storage.from_.return_value
        bucket.get_public_url.return_value = "https://example.test/image.png"

        path, url = _upload_thumbnail(
            CHATBOT_ID, (b"image", "image/png", "png")
        )

        assert path == f"{CHATBOT_ID}/image-uuid.png"
        db.storage.from_.assert_any_call("chatbot_thumbnails")
        bucket.upload.assert_called_once_with(
            path, b"image", {"content-type": "image/png"}
        )
        bucket.get_public_url.assert_called_once_with(path)

    assert url == "https://example.test/image.png"
