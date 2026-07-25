from flask import Blueprint, jsonify

botarena_bp = Blueprint("botarena", __name__)


@botarena_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "botarena"})
