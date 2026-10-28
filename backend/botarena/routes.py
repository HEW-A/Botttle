from flask import Blueprint, jsonify, request
from common.auth_helper import get_current_user
from .arena_core import Arena

botarena_bp = Blueprint("botarena", __name__)

arena = Arena()


def _normalize(value):
    # 文字列なら前後の空白を除く(空白だけが違う同一ボットのすり抜け防止)
    return value.strip() if isinstance(value, str) else value


@botarena_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "botarena"})


@botarena_bp.route("/battles")
def get_battles():
    return jsonify(arena.list_battles())


@botarena_bp.route("/battles", methods=["POST"])
async def create_battle():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "ログインが必要です"}), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    question = data.get("question")
    bot_a = _normalize(data.get("bot_a"))
    bot_b = _normalize(data.get("bot_b"))

    if not question or not bot_a or not bot_b:
        return jsonify({
            "error": "question, bot_a, bot_b は必須です"
        }), 400

    if bot_a == bot_b:
        return jsonify({
            "error": "bot_a と bot_b は別のボットを指定してください"
        }), 400

    try:
        battle = await arena.create_battle(
            question,
            bot_a,
            bot_b
        )
        return jsonify(battle)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@botarena_bp.route("/battles/<battle_id>", methods=["GET"])
def get_battle(battle_id):
    try:
        battle = arena.get_result(battle_id)
        return jsonify(battle)

    except KeyError:
        return jsonify({"error": "Battle not found"}), 404


@botarena_bp.route("/battles/<battle_id>/vote", methods=["POST"])
def vote(battle_id):
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "ログインが必要です"}), 401

    # 投票者はログイン中のユーザー。リクエストの中身の user_id は使わない
    user_id = current_user["user_id"]

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        data = {}
    choice = data.get("choice")

    if choice not in ("a", "b", "tie"):
        return jsonify({
            "error": "choice は a, b, tie のいずれかを指定してください"
        }), 400

    try:
        votes = arena.vote(
            battle_id,
            user_id,
            choice
        )
        return jsonify(votes)

    except KeyError:
        return jsonify({"error": "Battle not found"}), 404

    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@botarena_bp.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    return jsonify(arena.leaderboard())


@botarena_bp.route("/bot-leaderboard", methods=["GET"])
def get_bot_leaderboard():
    return jsonify(arena.bot_leaderboard())
