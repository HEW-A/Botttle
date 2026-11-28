"""
RAG（backend/rag）のテスト
Supabase・埋め込みモデル・LLM はすべて偽物に差し替えるので、ネット接続なしで動く。
"""
import os

os.environ.setdefault("EMBED_PROVIDER", "local")
os.environ.setdefault("LLM_PROVIDER", "ollama")

from unittest.mock import MagicMock, patch

import pymupdf
import pytest

from rag import chunker, config, embedder, llm, retriever, service
from rag.extractor import create_document_info, read_document


# =========================================================
# 偽物
# =========================================================

class _Vectors(list):
    def tolist(self):
        return list(self)


class FakeLocalModel:
    """e5 の代わり。1文字=1トークンとして数え、固定のベクトルを返す"""
    max_seq_length = 512

    def tokenizer(self, text):
        return {"input_ids": list(range(len(text) + 2))}

    def encode(self, texts, **kwargs):
        return _Vectors([[0.1] * config.EMBED_DIMENSIONS for _ in texts])


class FakeSupabase:
    """table().delete()/insert() と rpc() の呼び出しを記録する"""

    def __init__(self, rpc_rows=None, fail_insert_at=None):
        self.inserted = []
        self.deleted = []
        self.rpc_rows = rpc_rows or []
        self.fail_insert_at = fail_insert_at
        self._insert_calls = 0

    def table(self, name):
        sb = self
        query = MagicMock()

        def delete():
            q = MagicMock()
            q.eq.side_effect = lambda col, val: (
                sb.deleted.append((name, col, val)) or MagicMock()
            )
            return q

        def insert(rows):
            sb._insert_calls += 1
            if sb.fail_insert_at == sb._insert_calls:
                raise RuntimeError("insert failed")
            sb.inserted.extend(rows)
            return MagicMock()

        query.delete.side_effect = delete
        query.insert.side_effect = insert
        return query

    def rpc(self, fn, params):
        self.rpc_called = (fn, params)
        res = MagicMock()
        res.execute.return_value.data = [dict(r) for r in self.rpc_rows]
        return res


@pytest.fixture(autouse=True)
def fake_model():
    embedder.set_local_model_for_test(FakeLocalModel())
    yield
    embedder.set_local_model_for_test(None)


def _make_pdf(path, pages):
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text, fontsize=11)
    doc.save(path)
    doc.close()


# =========================================================
# chunker
# =========================================================

def test_split_text_respects_max_and_overlaps():
    text = "\n".join(f"これはテスト用の文章その{i}です。" * 3 for i in range(80))
    chunks = chunker.split_text(text)

    assert len(chunks) > 1
    assert all(len(c) <= chunker.CHUNK_MAX for c in chunks)
    # 隣り合うチャンクは末尾の文を共有する（オーバーラップ）
    assert chunks[0].split("\n")[-1] in chunks[1]


def test_split_text_long_line_is_cut():
    text = "".join(f"{i:04d}" for i in range(500))   # 句読点のない2000文字
    chunks = chunker.split_text(text)
    assert len(chunks) == 3
    assert all(len(c) <= chunker.CHUNK_MAX for c in chunks)
    assert chunks[0][-chunker.OVERLAP:] == chunks[1][:chunker.OVERLAP]
    assert chunks[-1].endswith("0499")


def test_split_text_empty():
    assert chunker.split_text("") == []
    assert chunker.split_text("\n\n  \n") == []


def test_japanese_wrapped_lines_join_without_space():
    assert chunker.split_text("これは折り返された\n行の例です。") == ["これは折り返された行の例です。"]
    assert chunker.split_text("This line is\nwrapped.") == ["This line is wrapped."]


def test_list_items_stay_separate():
    chunks = chunker.split_text("注意事項\n・水に濡らさない\n・分解しない")
    assert chunks == ["注意事項\n・水に濡らさない\n・分解しない"]


# =========================================================
# extractor
# =========================================================

def test_read_document_pdf_returns_int_pages(tmp_path):
    path = tmp_path / "manual.pdf"
    _make_pdf(path, ["Page one body text here.", "Page two body text here."])

    pages = read_document(str(path), "manual.pdf")

    assert [p for _, p in pages] == [1, 2]
    assert "Page one" in pages[0][0]


def test_read_document_txt_has_no_page(tmp_path):
    path = tmp_path / "memo.txt"
    path.write_text("これはテキストファイルの本文です。", encoding="cp932")

    assert read_document(str(path), "memo.txt") == [("これはテキストファイルの本文です。", None)]


def test_read_document_rejects_unknown_extension(tmp_path):
    path = tmp_path / "a.docx"
    path.write_bytes(b"x")
    with pytest.raises(ValueError):
        read_document(str(path), "a.docx")


def test_create_document_info(tmp_path):
    path = tmp_path / "manual.pdf"
    _make_pdf(path, ["Model X100 User Guide"])
    pages = read_document(str(path), "manual.pdf")

    info = create_document_info(str(path), "manual.pdf", pages)

    assert "ファイル名: manual.pdf" in info
    assert "Model X100 User Guide" in info


# =========================================================
# embedder
# =========================================================

def test_prepare_chunks_splits_over_token_limit():
    long_chunk = "\n".join(["あ" * 300] * 3)   # 900文字 > 512トークン
    parts = embedder.prepare_chunks([long_chunk, "", "  "])

    assert len(parts) >= 2
    assert all(embedder._count_local_tokens(p) <= 512 for p in parts)


# =========================================================
# service.ingest_pdf
# =========================================================

def test_ingest_pdf_saves_rows_with_page_numbers(tmp_path):
    path = tmp_path / "manual.pdf"
    _make_pdf(path, ["Page one body text here.", "Page two body text here."])
    sb = FakeSupabase()

    with patch.object(service, "get_supabase", return_value=sb):
        result = service.ingest_pdf("bot-1", "pdf-1", path.read_bytes(), "manual.pdf")

    assert result["pages"] == 2
    assert result["chunks"] == len(sb.inserted)
    assert sb.deleted == [("bot_chunk", "pdf_id", "pdf-1")]

    info_rows = [r for r in sb.inserted if r["is_doc_info"]]
    body_rows = [r for r in sb.inserted if not r["is_doc_info"]]
    assert info_rows and all(r["page"] is None for r in info_rows)
    assert [r["page"] for r in body_rows] == [1, 2]

    for i, r in enumerate(sb.inserted):
        assert r["chunk_index"] == i
        assert r["chatbot_id"] == "bot-1"
        assert len(r[config.EMBED_COLUMN]) == config.EMBED_DIMENSIONS
        assert r["embedding_model"] == config.EMBED_MODEL


def test_ingest_pdf_cleans_up_when_insert_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "INSERT_BATCH_SIZE", 1)
    path = tmp_path / "memo.txt"
    path.write_text("これはテキストファイルの本文です。" * 5, encoding="utf-8")
    sb = FakeSupabase(fail_insert_at=2)

    with patch.object(service, "get_supabase", return_value=sb):
        with pytest.raises(RuntimeError):
            service.ingest_pdf("bot-1", "pdf-1", path.read_bytes(), "memo.txt")

    # 最初の削除 + 失敗後の後片付けの削除
    assert sb.deleted == [("bot_chunk", "pdf_id", "pdf-1")] * 2


def test_ingest_pdf_rejects_bad_pdf():
    with patch.object(service, "get_supabase", return_value=FakeSupabase()):
        with pytest.raises(ValueError):
            service.ingest_pdf("bot-1", "pdf-1", b"not a pdf", "broken.pdf")


# =========================================================
# retriever
# =========================================================

def _row(chunk_id, file_name, content, similarity, page=1, is_doc_info=False):
    return {
        "chunk_id": chunk_id, "pdf_id": "p", "file_name": file_name, "page": page,
        "content": content, "is_doc_info": is_doc_info, "similarity": similarity,
    }


def test_search_prioritizes_doc_info_for_title_questions():
    rows = [
        _row("a", "manual.pdf", "電源の入れ方", 0.90),
        _row("b", "manual.pdf", "文書情報 ファイル名: manual.pdf", 0.80, None, True),
    ]
    sb = FakeSupabase(rpc_rows=rows)
    with patch.object(retriever, "get_supabase", return_value=sb):
        result = retriever.search("bot-1", "この資料の機種名は？")

    assert result[0]["chunk_id"] == "b"
    assert sb.rpc_called[0] == config.MATCH_FUNCTION
    assert sb.rpc_called[1]["p_chatbot_id"] == "bot-1"


def test_search_filters_by_file_name_in_question():
    rows = [
        _row("a", "a.pdf", "内容A", 0.9),
        _row("b", "b.pdf", "内容B", 0.5),
    ]
    with patch.object(retriever, "get_supabase", return_value=FakeSupabase(rpc_rows=rows)):
        result = retriever.search("bot-1", "b.pdf について教えて")

    assert [r["chunk_id"] for r in result] == ["b"]


def test_fit_context_skips_too_long_chunk(monkeypatch):
    monkeypatch.setattr(config, "MAX_CONTEXT_CHARS", 100)
    chunks = [_row("a", "a.pdf", "x" * 200, 0.9), _row("b", "a.pdf", "短い", 0.8)]

    assert [c["chunk_id"] for c in retriever.fit_context(chunks)] == ["b"]


def test_to_sources_hides_doc_info_and_dedupes():
    chunks = [
        _row("a", "a.pdf", "x", 0.9, 1),
        _row("b", "a.pdf", "y", 0.8, 1),
        _row("c", "a.pdf", "z", 0.7, None, True),
    ]
    assert retriever.to_sources(chunks) == [{"file_name": "a.pdf", "page": 1, "similarity": 0.9}]


# =========================================================
# service.ask
# =========================================================

def test_ask_without_results_returns_full_shape():
    with patch.object(service, "search", return_value=[]):
        result = service.ask("bot-1", "質問です")

    assert result["answer"] == llm.NO_CONTEXT_ANSWER
    assert result["sources"] == []
    assert "input_tokens" in result and "model" in result


def test_ask_sources_match_context(monkeypatch):
    monkeypatch.setattr(config, "MAX_CONTEXT_CHARS", 60)
    chunks = [_row("a", "a.pdf", "電源ボタンを長押し", 0.9, 3), _row("b", "b.pdf", "x" * 200, 0.8, 5)]
    fake_answer = {"answer": "はい", "input_tokens": 1, "output_tokens": 1}

    with patch.object(service, "search", return_value=chunks), \
            patch.object(service, "generate_answer", return_value=fake_answer) as gen:
        result = service.ask("bot-1", "電源は？")

    context = gen.call_args[0][1]
    assert "a.pdf p.3" in context and "b.pdf" not in context
    assert result["sources"] == [{"file_name": "a.pdf", "page": 3, "similarity": 0.9}]


def test_ask_rejects_empty_and_too_long():
    with pytest.raises(ValueError):
        service.ask("bot-1", "   ")
    with pytest.raises(ValueError):
        service.ask("bot-1", "あ" * (config.MAX_QUESTION_CHARS + 1))


# =========================================================
# llm（Ollama）
# =========================================================

def _response(status, data=None):
    res = MagicMock(status_code=status, text="error")
    res.json.return_value = data or {}
    return res


def test_ollama_retries_once_on_500(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "ollama")
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    ok = _response(200, {"message": {"content": "はい。"}, "prompt_eval_count": 10,
                         "eval_count": 3, "done_reason": "stop"})

    with patch.object(llm.requests, "post", side_effect=[_response(500), ok]) as post:
        result = llm.generate_answer("質問", "資料")

    assert post.call_count == 2
    assert result["answer"] == "はい。"
    assert result["input_tokens"] == 10 and result["incomplete"] is False


def test_ollama_connection_error(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "ollama")
    with patch.object(llm.requests, "post", side_effect=llm.requests.ConnectionError()):
        with pytest.raises(llm.LLMError):
            llm.generate_answer("質問", "資料")


def test_openai_omits_reasoning_when_empty(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(llm, "REASONING_EFFORT", "")
    client = MagicMock()
    client.responses.create.return_value = MagicMock(
        output_text="はい", status="completed",
        usage=MagicMock(input_tokens=100, output_tokens=10),
    )
    with patch.object(llm, "get_client", return_value=client):
        result = llm.generate_answer("質問", "資料")

    assert "reasoning" not in client.responses.create.call_args.kwargs
    assert result["answer"] == "はい" and result["cost_yen"] > 0
