from flask import Blueprint, jsonify

users_bp = Blueprint("users", __name__)


@users_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "users"})
