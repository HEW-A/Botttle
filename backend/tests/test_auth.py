import os
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app
import auth.routes as auth_routes


@pytest.fixture
def client(monkeypatch):
    fake_supabase = MagicMock()
    monkeypatch.setattr(auth_routes, "supabase", fake_supabase)

    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        client.fake_supabase = fake_supabase
        yield client


def _no_existing_user(fake_supabase):
    fake_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = SimpleNamespace(data=[])


def test_signup_without_email_generates_dummy_auth_email(client):
    fake_supabase = client.fake_supabase
    _no_existing_user(fake_supabase)
    fake_supabase.auth.sign_up.return_value = SimpleNamespace(
        user=SimpleNamespace(id="uid-123"),
        session=None,
    )

    res = client.post("/api/auth/signup", json={
        "user_id": "taro123",
        "username": "太郎",
        "password": "password123",
    })

    assert res.status_code == 201, res.get_json()

    called_args = fake_supabase.auth.sign_up.call_args[0][0]
    assert called_args["email"] == "taro123@users.botttle.internal"

    insert_call = fake_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["auth_email"] == "taro123@users.botttle.internal"
    assert insert_call["user_mailaddless"] is None


def test_signup_with_email_uses_it_as_auth_email(client):
    fake_supabase = client.fake_supabase
    _no_existing_user(fake_supabase)
    fake_supabase.auth.sign_up.return_value = SimpleNamespace(
        user=SimpleNamespace(id="uid-456"),
        session=None,
    )

    res = client.post("/api/auth/signup", json={
        "user_id": "hanako456",
        "username": "花子",
        "password": "password123",
        "email": "hanako@example.com",
    })

    assert res.status_code == 201, res.get_json()

    called_args = fake_supabase.auth.sign_up.call_args[0][0]
    assert called_args["email"] == "hanako@example.com"

    insert_call = fake_supabase.table.return_value.insert.call_args[0][0]
    assert insert_call["auth_email"] == "hanako@example.com"
    assert insert_call["user_mailaddless"] == "hanako@example.com"


def test_signup_rejects_short_password(client):
    fake_supabase = client.fake_supabase
    _no_existing_user(fake_supabase)

    res = client.post("/api/auth/signup", json={
        "user_id": "taro123",
        "username": "太郎",
        "password": "short1",
    })

    assert res.status_code == 400
    assert fake_supabase.auth.sign_up.call_count == 0


def test_signup_db_error_still_returns_cors_header(client):
    """usersテーブル未整備などでDB例外が起きても、CORSヘッダー付きのJSONエラーになること"""
    fake_supabase = client.fake_supabase
    fake_supabase.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.side_effect = Exception("relation \"users\" does not exist")

    res = client.post(
        "/api/auth/signup",
        json={"user_id": "taro123", "username": "太郎", "password": "password123"},
        headers={"Origin": "http://localhost:3000"},
    )

    assert res.status_code == 500
    assert res.get_json()["error"]
    assert res.headers.get("Access-Control-Allow-Origin") == "http://localhost:3000"
