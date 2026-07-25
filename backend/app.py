from flask import Flask
from flask_cors import CORS

from auth.test import auth_bp
from bot_creation.test import bot_creation_bp
from botarena.test import botarena_bp
from users.test import users_bp
from common.test import common_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(bot_creation_bp, url_prefix="/api/bots")
    app.register_blueprint(botarena_bp, url_prefix="/api/botarena")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(common_bp, url_prefix="/api/common")

    @app.route("/api/health")
    def health():
        return {"status": "ok"}

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=5000)
