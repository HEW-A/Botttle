import os
import sys

import pytest

# backend ディレクトリをインポートパスに追加（app.py / 各ドメインを import 可能にする）
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


def test_health_returns_ok(client):
    """GET /api/health が 200 を返し、status が "ok" であること"""
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.get_json()["status"] == "ok"


@pytest.mark.parametrize(
    "path,domain",
    [
        ("/api/auth/health", "auth"),
        ("/api/bots/health", "bot_creation"),
        ("/api/botarena/health", "botarena"),
        ("/api/users/health", "users"),
        ("/api/common/health", "common"),
    ],
)
def test_domain_health_returns_ok(client, path, domain):
    """各ドメインの /health エンドポイントが 200 を返し、domain が一致すること"""
    res = client.get(path)
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert body["domain"] == domain
