from flask import Blueprint, jsonify

bot_creation_bp = Blueprint("bot_creation", __name__)


@bot_creation_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "bot_creation"})
