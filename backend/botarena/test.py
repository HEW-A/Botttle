from flask import Blueprint, jsonify, request
from arena_core import Arena

botarena_bp = Blueprint("botarena", __name__)

arena = Arena()


@botarena_bp.route("/health")
def health():
    return jsonify({"status": "ok", "domain": "botarena"})


@botarena_bp.route("/battles")
def get_battles():
    return jsonify(arena.list_battles())


@botarena_bp.route("/battles", methods=["POST"])
async def create_battle():
    data = request.get_json()
    question = data.get("question")
    bot_a = data.get("bot_a")
    bot_b = data.get("bot_b")

    if not question or not bot_a or not bot_b:
        return jsonify({
            "error": "question, bot_a, bot_b は必須です"
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
    data = request.get_json()
    user_id = data.get("user_id")
    choice = data.get("choice")

    if not user_id or choice not in ("a", "b", "tie"):
        return jsonify({
            "error": "user_id と choice は必須です"
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