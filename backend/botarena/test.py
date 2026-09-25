from flask import Blueprint, jsonify
from other.arena.arena_core import Arena

botarena_bp = Blueprint("botarena", __name__)

arena = Arena()


@botarena_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "botarena"})
@botarena_bp.route("/battles")
def get_battles():
    return jsonify(arena.list_battles())