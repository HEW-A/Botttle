"""
会話履歴（conversations / messages テーブル）の読み書きと、古い履歴の要約

LLM に送る履歴は「要約 ＋ まだ要約していないメッセージ」。
要約していないメッセージが多くなりすぎたら、直近だけ残して古い分を要約に回す。
こうすると、どのメッセージも「要約」か「そのまま送る履歴」のどちらかに必ず入る。
"""

import logging

from rag import config
from rag.db import get_supabase
from rag.llm import summarize_conversation

logger = logging.getLogger(__name__)

CONVERSATION_COLUMNS = "conversation_id, chatbot_id, user_id, summary, summarized_until, created_at"
MESSAGE_COLUMNS = "message_id, role, content, created_at"


# =========================================================
# 会話
# =========================================================

def create_conversation(chatbot_id, user_id):
    res = get_supabase().table("conversations").insert({
        "chatbot_id": str(chatbot_id),
        "user_id": user_id,
    }).execute()
    return res.data[0]


def get_conversation(conversation_id, chatbot_id, user_id):
    """本人の、そのボットとの会話だけを返す（他人の会話は None）"""
    res = (
        get_supabase().table("conversations")
        .select(CONVERSATION_COLUMNS)
        .eq("conversation_id", str(conversation_id))
        .eq("chatbot_id", str(chatbot_id))
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def list_conversations(chatbot_id, user_id):
    res = (
        get_supabase().table("conversations")
        .select("conversation_id, created_at")
        .eq("chatbot_id", str(chatbot_id))
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


# =========================================================
# メッセージ
# =========================================================

def list_messages(conversation_id):
    """画面表示用：会話の全メッセージを古い順に返す"""
    res = (
        get_supabase().table("messages")
        .select(MESSAGE_COLUMNS)
        .eq("conversation_id", str(conversation_id))
        .order("created_at")
        .execute()
    )
    return res.data or []


def save_turn(conversation_id, question, answer):
    """
    質問と回答を保存する。
    created_at で順番を決めるので、同じ時刻にならないよう1件ずつ保存する。
    """
    table = get_supabase().table("messages")
    table.insert({"conversation_id": str(conversation_id), "role": "user", "content": question}).execute()
    table.insert({"conversation_id": str(conversation_id), "role": "ai", "content": answer}).execute()


def _unsummarized_messages(conversation):
    query = (
        get_supabase().table("messages")
        .select(MESSAGE_COLUMNS)
        .eq("conversation_id", str(conversation["conversation_id"]))
    )
    if conversation.get("summarized_until"):
        query = query.gt("created_at", conversation["summarized_until"])
    return query.order("created_at").execute().data or []


# =========================================================
# LLM に送る形にする
# =========================================================

def _clip(text):
    text = text or ""
    if len(text) <= config.MAX_MESSAGE_CHARS:
        return text
    return text[:config.MAX_MESSAGE_CHARS] + "…"


def _to_llm(messages):
    """DB の role（user / ai）を LLM の role（user / assistant）に変える"""
    return [
        {"role": "assistant" if m["role"] == "ai" else "user", "content": _clip(m["content"])}
        for m in messages
    ]


def _chars(messages):
    return sum(len(_clip(m["content"])) for m in messages)


def _needs_summary(messages):
    return (
        len(messages) > config.HISTORY_MAX_MESSAGES
        or _chars(messages) > config.MAX_HISTORY_CHARS
    )


def _split_for_summary(messages):
    """(要約に回す古い部分, そのまま送る直近部分) に分ける"""
    keep = messages[-config.HISTORY_KEEP_MESSAGES:] if config.HISTORY_KEEP_MESSAGES else []
    # 直近部分も文字数の予算に収まるまで、古いほうから要約に回す
    while keep and _chars(keep) > config.MAX_HISTORY_CHARS:
        keep = keep[1:]
    old = messages[:len(messages) - len(keep)]
    return old, keep


def prepare_history(conversation):
    """
    LLM に送る (要約, 直近の履歴) を返す。
    履歴が長くなっていれば、古い分を要約して conversations に保存する。
    """
    summary = conversation.get("summary") or ""
    messages = _unsummarized_messages(conversation)

    if not _needs_summary(messages):
        return summary, _to_llm(messages)

    old, keep = _split_for_summary(messages)
    try:
        new_summary = summarize_conversation(summary, _to_llm(old))
        (
            get_supabase().table("conversations")
            .update({"summary": new_summary, "summarized_until": old[-1]["created_at"]})
            .eq("conversation_id", str(conversation["conversation_id"]))
            .execute()
        )
        summary = new_summary
    except Exception:
        # 要約できなくても回答は続ける（今回は直近だけ送り、次の質問でまた要約を試す）
        logger.exception("[history] 会話の要約に失敗しました")

    return summary, _to_llm(keep)
