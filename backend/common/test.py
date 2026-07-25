from flask import Blueprint, jsonify

common_bp = Blueprint("common", __name__)


@common_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "common"})
