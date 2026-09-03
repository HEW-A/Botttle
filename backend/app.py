import os

from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
from common.supabase_client import supabase

from auth.routes import auth_bp
from bot_creation.test import bot_creation_bp
from botarena.test import botarena_bp
from users.test import users_bp
from common.test import common_bp

# backend/.env ファイルを読み込み、以降の os.getenv() で値を使えるようにする
load_dotenv()


def create_app():
    app = Flask(__name__)

    # 開発中は指定URLのNuxtからのアクセスのみ許可
    # Cookieでセッションを扱うため、Cookie付きリクエストを許可する
    CORS(app, origins=["http://localhost:3000"], supports_credentials=True)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(bot_creation_bp, url_prefix="/api/bots")
    app.register_blueprint(botarena_bp, url_prefix="/api/botarena")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(common_bp, url_prefix="/api/common")

    # 未処理の例外がdebugモードのインタラクティブデバッガー(CORSヘッダーが付かない)に
    # 渡ってしまうのを防ぎ、常にCORSヘッダー付きのJSONエラーを返すようにする
    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        if isinstance(e, HTTPException):
            return e
        app.logger.exception("Unexpected error")
        return jsonify({"error": "サーバー内部でエラーが発生しました"}), 500

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    # GET /api/botttles へのリクエストを受け取り、Supabaseのテストデータを返すAPI
    @app.get("/api/botttles")
    def get_botttles():
        # botttles テーブルをSupabaseから取得する
        response = supabase.table("botttles").select("*").execute()
        # Supabaseの取得結果をNuxtが受け取れるJSON形式にして返す
        return jsonify(response.data)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
