"""
RAG チャット API（url_prefix: /api/bots）

POST /api/bots/<chatbot_id>/ask
    {"question": "...", "conversation_id": "..."(省略すると新しい会話)}
    → {"answer", "sources", "conversation_id", "incomplete"}
GET  /api/bots/<chatbot_id>/conversations
    → 自分とこのボットの会話一覧（新しい順）
GET  /api/bots/<chatbot_id>/conversations/<conversation_id>/messages
    → 会話のメッセージ（古い順）
POST /api/bots/<chatbot_id>/reindex
    → 保存済みPDFをすべてRAGに取り込み直す（作成者のみ。RAG導入前のボットや、取り込み失敗時に使う）

使えるのは、ボットの作成者と購入者だけ（reindex は作成者だけ）。
"""
import uuid

from flask import Blueprint, current_app, jsonify, request

from bot_creation.routes import BOT_PDF_BUCKET
from common.auth_helper import get_current_user
from common.supabase_client import supabase
from rag import history
from rag.llm import LLMError
from rag.service import ConversationNotFound, chat, ingest_pdf_safely

bot_chat_bp = Blueprint("bot_chat", __name__)

INVALID_ID_ERROR = "IDの形式が正しくありません"


def _normalize_id(value):
    if not isinstance(value, str):
        return None
    try:
        return str(uuid.UUID(value))
    except ValueError:
        return None


def _can_use_bot(chatbot_id, user_id):
    """(ボットが存在するか, 使ってよいか) を返す。作成者と購入者だけが使える"""
    bot = (
        supabase.table("chatbot")
        .select("creator_id")
        .eq("chatbot_id", chatbot_id)
        .limit(1)
        .execute()
    )
    if not bot.data:
        return False, False
    if bot.data[0]["creator_id"] == user_id:
        return True, True

    # purchases.is_deleted は表示用のフラグなので、購入済みかどうかには関係しない
    purchased = (
        supabase.table("purchases")
        .select("purchase_id")
        .eq("buyer_id", user_id)
        .eq("chatbot_id", chatbot_id)
        .limit(1)
        .execute()
    )
    return True, bool(purchased.data)


def _check_access(raw_chatbot_id):
    """(ユーザー, chatbot_id, エラーレスポンス) を返す。問題なければエラーは None"""
    user = get_current_user()
    if not user:
        return None, None, (jsonify({"error": "ログインが必要です"}), 401)

    chatbot_id = _normalize_id(raw_chatbot_id)
    if chatbot_id is None:
        return None, None, (jsonify({"error": INVALID_ID_ERROR}), 400)

    exists, allowed = _can_use_bot(chatbot_id, user["user_id"])
    if not exists:
        return None, None, (jsonify({"error": "チャットボットが見つかりません"}), 404)
    if not allowed:
        return None, None, (jsonify({"error": "購入したチャットボットだけ利用できます"}), 403)

    return user, chatbot_id, None


@bot_chat_bp.post("/<chatbot_id>/ask")
def ask_bot(chatbot_id):
    user, chatbot_id, error = _check_access(chatbot_id)
    if error:
        return error

    body = request.get_json(silent=True) or {}
    question = body.get("question")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "question は必須です"}), 400

    conversation_id = body.get("conversation_id")
    if conversation_id is not None:
        conversation_id = _normalize_id(conversation_id)
        if conversation_id is None:
            return jsonify({"error": INVALID_ID_ERROR}), 400

    try:
        result = chat(chatbot_id, user["user_id"], question, conversation_id)
    except ConversationNotFound:
        return jsonify({"error": "会話が見つかりません"}), 404
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except LLMError as e:
        current_app.logger.warning("RAG回答の生成に失敗: %s", e)
        return jsonify({"error": "回答を生成できませんでした。時間をおいてもう一度お試しください"}), 503

    current_app.logger.info(
        "RAG回答 bot=%s provider=%s model=%s tokens=%s/%s cost=%s円 %s秒",
        chatbot_id, result.get("provider"), result.get("model"),
        result.get("input_tokens"), result.get("output_tokens"),
        result.get("cost_yen"), result.get("elapsed_sec"),
    )

    # トークン数や費用は利用者には見せず、ログにだけ残す
    return jsonify({
        "answer": result["answer"],
        "sources": result["sources"],
        "conversation_id": result["conversation_id"],
        "incomplete": result.get("incomplete", False),
    })


@bot_chat_bp.get("/<chatbot_id>/conversations")
def get_conversations(chatbot_id):
    user, chatbot_id, error = _check_access(chatbot_id)
    if error:
        return error

    return jsonify({"conversations": history.list_conversations(chatbot_id, user["user_id"])})


@bot_chat_bp.get("/<chatbot_id>/conversations/<conversation_id>/messages")
def get_messages(chatbot_id, conversation_id):
    user, chatbot_id, error = _check_access(chatbot_id)
    if error:
        return error

    conversation_id = _normalize_id(conversation_id)
    if conversation_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    if not history.get_conversation(conversation_id, chatbot_id, user["user_id"]):
        return jsonify({"error": "会話が見つかりません"}), 404

    return jsonify({
        "conversation_id": conversation_id,
        "messages": history.list_messages(conversation_id),
    })


@bot_chat_bp.post("/<chatbot_id>/reindex")
def reindex_bot(chatbot_id):
    user = get_current_user()
    if not user:
        return jsonify({"error": "ログインが必要です"}), 401

    chatbot_id = _normalize_id(chatbot_id)
    if chatbot_id is None:
        return jsonify({"error": INVALID_ID_ERROR}), 400

    bot = (
        supabase.table("chatbot")
        .select("creator_id")
        .eq("chatbot_id", chatbot_id)
        .limit(1)
        .execute()
    )
    if not bot.data:
        return jsonify({"error": "チャットボットが見つかりません"}), 404
    if bot.data[0]["creator_id"] != user["user_id"]:
        return jsonify({"error": "作成者だけが実行できます"}), 403

    pdfs = (
        supabase.table("bot_pdf")
        .select("pdf_id, file_path, file_name")
        .eq("chatbot_id", chatbot_id)
        .execute()
    ).data or []

    results = []
    for pdf in pdfs:
        try:
            file_bytes = supabase.storage.from_(BOT_PDF_BUCKET).download(pdf["file_path"])
        except Exception:
            current_app.logger.exception("PDFのダウンロードに失敗: %s", pdf["file_path"])
            indexed = False
        else:
            indexed = ingest_pdf_safely(chatbot_id, pdf["pdf_id"], file_bytes, pdf["file_name"])
        results.append({"pdf_id": pdf["pdf_id"], "file_name": pdf["file_name"], "indexed": indexed})

    return jsonify({
        "message": f"{sum(r['indexed'] for r in results)}/{len(results)}件のPDFを取り込みました",
        "results": results,
    })
