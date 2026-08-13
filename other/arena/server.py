"""
チャットボットアリーナ - HTTPサーバー(標準ライブラリのみ、追加インストール不要)

起動: python3 server.py
デフォルトで http://localhost:8000 で待ち受け

エンドポイント:
  POST /battles                     質問を投げて2ボットの回答を取得
    body: {"question": str, "bot_a": str, "bot_b": str}

  POST /battles/{battle_id}/vote    投票(ユーザーごとに1回・投票でポイント付与)
    body: {"user_id": str, "choice": "a" | "b" | "tie"}

  GET  /battles/{battle_id}         そのバトルの投票結果・勝者を取得
  GET  /battles                     全バトル一覧
  GET  /leaderboard                 ポイントランキング
"""

import asyncio
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from arena_core import Arena

arena = Arena()

ROUTE_VOTE = re.compile(r"^/battles/([^/]+)/vote$")
ROUTE_BATTLE = re.compile(r"^/battles/([^/]+)$")


class Handler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        # フロントエンドを別オリジン(file://やlive-serverなど)で開いても
        # 叩けるように全オリジン許可。本番では許可オリジンを絞ること。
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _send_json(self, status: int, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        # プリフライトリクエスト対応
        self.send_response(204)
        self._send_cors_headers()
        self.end_headers()

    def _read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length))

    def do_GET(self):
        try:
            if self.path == "/battles":
                self._send_json(200, arena.list_battles())
            elif self.path == "/leaderboard":
                self._send_json(200, arena.leaderboard())
            elif (m := ROUTE_BATTLE.match(self.path)):
                result = arena.get_result(m.group(1))
                self._send_json(200, result)
            else:
                self._send_json(404, {"detail": "not found"})
        except KeyError:
            self._send_json(404, {"detail": "battle not found"})
        except Exception as e:
            self._send_json(500, {"detail": str(e)})

    def do_POST(self):
        try:
            if self.path == "/battles":
                body = self._read_json()
                result = asyncio.run(
                    arena.create_battle(body["question"], body["bot_a"], body["bot_b"])
                )
                self._send_json(200, result)
            elif (m := ROUTE_VOTE.match(self.path)):
                body = self._read_json()
                votes = arena.vote(m.group(1), body["user_id"], body["choice"])
                self._send_json(200, {"ok": True, "votes": votes})
            else:
                self._send_json(404, {"detail": "not found"})
        except KeyError as e:
            self._send_json(404, {"detail": f"not found or missing field: {e}"})
        except ValueError as e:
            self._send_json(400, {"detail": str(e)})
        except Exception as e:
            self._send_json(500, {"detail": str(e)})

    def log_message(self, format, *args):
        pass  # コンソールを静かにする


def main(port: int = 8000):
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"Chatbot Arena server running on http://localhost:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()