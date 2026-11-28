"""
RAG の入口（API からはこのファイルの関数だけを呼ぶ）
- ingest_pdf        : 資料の取り込み（抽出 → 分割 → 埋め込み → 保存）
- ingest_pdf_safely : ingest_pdf の失敗しない版（アップロード処理から呼ぶ）
- delete_pdf_chunks : 資料のチャンク削除
- ask               : 質問への回答（検索 → 回答生成）
- chat              : 会話履歴つきの質問応答（履歴の読み込み・要約 → ask → 保存）
"""
import logging
import os
import tempfile

from rag import config, history
from rag.chunker import split_text
from rag.db import get_supabase
from rag.embedder import embed_cost_yen, embed_passages, prepare_chunks
from rag.extractor import create_document_info, read_document
from rag.llm import generate_answer
from rag.retriever import build_context, fit_context, search, to_sources

logger = logging.getLogger(__name__)


# =========================================================
# 取り込み
# =========================================================
def _non_empty_pages(pages):
    """read_document の返り値 [(本文, ページ番号 or None), ...] から空ページを除く"""
    return [(text, page) for text, page in pages if text and text.strip()]


def _build_rows(info_text, pages):
    """保存するチャンク行（埋め込み前）を作る"""
    rows = []

    if info_text and info_text.strip():
        for chunk in prepare_chunks([info_text]):
            rows.append({"page": None, "content": chunk, "is_doc_info": True})

    # ページ番号を保つため、ページごとに分割する
    for text, page in pages:
        for chunk in prepare_chunks(split_text(text)):
            rows.append({"page": page, "content": chunk, "is_doc_info": False})

    return rows


def ingest_pdf(chatbot_id, pdf_id, file_bytes, file_name):
    """
    1つの資料（PDF / TXT / Markdown）をチャンク化して bot_chunk に保存する。
    同じ pdf_id で再実行すると、古いチャンクを消して入れ直す。
    """
    suffix = os.path.splitext(file_name)[1].lower()
    fd, tmp_path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(file_bytes)

        raw_pages = read_document(tmp_path, file_name)
        pages = _non_empty_pages(raw_pages)
        if not pages:
            raise ValueError("資料からテキストを取り出せませんでした")

        try:
            info_text = create_document_info(tmp_path, file_name, raw_pages)
        except Exception as e:  # 文書情報が作れなくても取り込みは続ける
            logger.warning("[ingest] 文書情報の作成をスキップ: %s", e)
            info_text = ""
    finally:
        try:
            os.remove(tmp_path)
        except OSError as e:
            logger.warning("[ingest] 一時ファイルを削除できませんでした: %s (%s)", tmp_path, e)

    # ---- チャンク化 ----
    rows = _build_rows(info_text, pages)
    if not rows:
        raise ValueError("チャンクが作れませんでした")

    # ---- 埋め込み ----
    vectors, tokens = embed_passages([r["content"] for r in rows])

    for i, (r, v) in enumerate(zip(rows, vectors)):
        r["chatbot_id"] = str(chatbot_id)
        r["pdf_id"] = str(pdf_id)
        r["chunk_index"] = i
        r[config.EMBED_COLUMN] = v
        r["embedding_model"] = config.EMBED_MODEL   # どのモデルで作ったか（再取り込みの判定用）

    # ---- 保存 ----
    sb = get_supabase()
    sb.table("bot_chunk").delete().eq("pdf_id", str(pdf_id)).execute()
    try:
        for start in range(0, len(rows), config.INSERT_BATCH_SIZE):
            sb.table("bot_chunk").insert(
                rows[start:start + config.INSERT_BATCH_SIZE]
            ).execute()
    except Exception:
        # 途中まで保存されたチャンクが残ると検索結果が中途半端になるので消しておく
        try:
            delete_pdf_chunks(pdf_id)
        except Exception:
            logger.exception("[ingest] 途中まで保存したチャンクの削除に失敗")
        raise

    return {
        "pdf_id": str(pdf_id),
        "pages": len(pages),
        "chunks": len(rows),
        "embed_tokens": tokens,
        "embed_cost_yen": embed_cost_yen(tokens),
    }


def ingest_pdf_safely(chatbot_id, pdf_id, file_bytes, file_name):
    """
    ingest_pdf を呼び、失敗してもエラーにせずログに残して False を返す。
    PDFのアップロード自体は成功させたいときに使う（あとから再取り込みできる）。
    """
    try:
        ingest_pdf(chatbot_id, pdf_id, file_bytes, file_name)
        return True
    except Exception:
        logger.exception("[ingest] RAG取り込みに失敗しました: %s (pdf_id=%s)", file_name, pdf_id)
        return False


def delete_pdf_chunks(pdf_id):
    get_supabase().table("bot_chunk").delete().eq("pdf_id", str(pdf_id)).execute()


# =========================================================
# 質問応答
# =========================================================
class ConversationNotFound(Exception):
    """指定された会話が存在しない、または本人のものではない"""


def _validate_question(question):
    question = (question or "").strip()
    if not question:
        raise ValueError("質問が空です")
    if len(question) > config.MAX_QUESTION_CHARS:
        raise ValueError(f"質問は{config.MAX_QUESTION_CHARS}文字以内で入力してください")
    return question


def _search_query(question, past):
    """
    検索に使う文。「それはいくら？」のような続きの質問でも資料が見つかるように、
    直前のユーザーの質問もつなげる（今回の質問を先に置き、長すぎる分は後ろが切られる）
    """
    previous = next((m["content"] for m in reversed(past or []) if m["role"] == "user"), "")
    return f"{question}\n{previous}" if previous else question


def ask(chatbot_id, question, history=None, summary=""):
    """
    history : 直近の会話 [{"role": "user"/"assistant", "content": ...}, ...]（古い順）
    summary : それより前の会話の要約

    戻り値は常に同じ形:
    {"answer", "input_tokens", "output_tokens", "cost_yen", "incomplete",
     "provider", "model", "elapsed_sec", "sources"}
    """
    question = _validate_question(question)

    # LLM に実際に渡したチャンクだけを出典として返す
    chunks = fit_context(search(chatbot_id, _search_query(question, history)))

    # 検索結果が0件のときは context が空になり、generate_answer は LLM を呼ばずに返す
    result = generate_answer(
        question, build_context(chunks), history=history, summary=summary
    )
    result["sources"] = to_sources(chunks)
    return result


def chat(chatbot_id, user_id, question, conversation_id=None):
    """
    会話履歴つきで質問に答え、質問と回答を保存する。
    conversation_id を省略すると、新しい会話を始める。
    戻り値は ask() と同じ形に "conversation_id" を加えたもの。
    """
    question = _validate_question(question)

    if conversation_id:
        conversation = history.get_conversation(conversation_id, chatbot_id, user_id)
        if not conversation:
            raise ConversationNotFound()
        summary, past = history.prepare_history(conversation)
    else:
        conversation, summary, past = None, "", []

    result = ask(chatbot_id, question, history=past, summary=summary)

    # 回答できたときだけ保存する（LLM のエラーで空の会話が残らないように）
    if conversation is None:
        conversation = history.create_conversation(chatbot_id, user_id)
    history.save_turn(conversation["conversation_id"], question, result["answer"])

    result["conversation_id"] = str(conversation["conversation_id"])
    return result
