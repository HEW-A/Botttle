"""
チャットボットアリーナ - コアロジック(Web非依存)

Webフレームワークに依存しない部分をここに切り出してる。
ボットAPI呼び出し・DBは別担当が用意する想定なのでダミー実装。
本番では call_bot() を実API呼び出しに、Storage内部をSQL DBに差し替えるだけでOK。
"""

from uuid import uuid4
from datetime import datetime, timezone
from typing import Optional, Literal
import asyncio


async def call_bot(bot_name: str, question: str) -> str:
    """本番では各ボットのAPIを叩く。今はダミーでオウム返し。"""
    await asyncio.sleep(0.05)
    return f"[{bot_name}からのダミー回答] 「{question}」について考えてみました。"


class Arena:
    """バトルの作成・投票・結果集計を管理するクラス。
    本番ではこのクラスの中身をSQL DBアクセスに差し替える想定。"""

    def __init__(self):
        self.battles: dict[str, dict] = {}
        self.user_points: dict[str, int] = {}

    async def create_battle(self, question: str, bot_a: str, bot_b: str) -> dict:
        response_a, response_b = await asyncio.gather(
            call_bot(bot_a, question),
            call_bot(bot_b, question),
        )
        battle_id = str(uuid4())
        self.battles[battle_id] = {
            "question": question,
            "bot_a": bot_a,
            "bot_b": bot_b,
            "response_a": response_a,
            "response_b": response_b,
            "votes": {"a": 0, "b": 0, "tie": 0},
            "voters": set(),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        return {
            "battle_id": battle_id,
            "question": question,
            "response_a": response_a,
            "response_b": response_b,
        }

    def vote(self, battle_id: str, user_id: str, choice: Literal["a", "b", "tie"]) -> dict:
        battle = self.battles.get(battle_id)
        if battle is None:
            raise KeyError("battle not found")
        if user_id in battle["voters"]:
            raise ValueError("already voted")

        battle["votes"][choice] += 1
        battle["voters"].add(user_id)
        self.user_points[user_id] = self.user_points.get(user_id, 0) + 1
        return dict(battle["votes"])

    def get_result(self, battle_id: str) -> dict:
        battle = self.battles.get(battle_id)
        if battle is None:
            raise KeyError("battle not found")

        votes = battle["votes"]
        winner: Optional[str] = None
        if any(votes.values()):
            top_count = max(votes.values())
            top = [k for k, v in votes.items() if v == top_count]
            winner = top[0] if len(top) == 1 else "tie"

        return {
            "battle_id": battle_id,
            "question": battle["question"],
            "votes_a": votes["a"],
            "votes_b": votes["b"],
            "votes_tie": votes["tie"],
            "winner": winner,
            "bot_a": battle["bot_a"],
            "bot_b": battle["bot_b"],
        }

    def leaderboard(self) -> list[dict]:
        ranking = sorted(self.user_points.items(), key=lambda x: x[1], reverse=True)
        return [{"user_id": u, "points": p} for u, p in ranking]

    def list_battles(self) -> list[dict]:
        return [
            {"battle_id": bid, "question": b["question"], "votes": b["votes"]}
            for bid, b in self.battles.items()
        ]
