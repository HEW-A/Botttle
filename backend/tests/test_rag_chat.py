"""
RAG チャット（会話履歴・要約・API）のテスト
Supabase はメモリ上の偽物、LLM と検索は差し替えて、ネット接続なしで動かす。
"""
import os

os.environ.setdefault("EMBED_PROVIDER", "local")
os.environ.setdefault("LLM_PROVIDER", "ollama")

import itertools
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from rag import config, history, llm, service
from rag.llm import LLMError

BOT_ID = "11111111-1111-1111-1111-111111111111"
OTHER_BOT_ID = "22222222-2222-2222-2222-222222222222"


# =========================================================
# メモリ上の Supabase
# =========================================================

class FakeQuery:
    def __init__(self, db, table):
        self.db, self.table = db, table
        self.filters, self._order, self._desc, self._limit = [], None, False, None
        self.action, self.payload = "select", None

    def select(self, *_):
        self.action = "select"
        return self

    def insert(self, payload):
        self.action, self.payload = "insert", payload
        return self

    def update(self, payload):
        self.action, self.payload = "update", payload
        return self

    def eq(self, col, val):
        self.filters.append(lambda r: str(r.get(col)) == str(val))
        return self

    def gt(self, col, val):
        self.filters.append(lambda r: r.get(col) > val)
        return self

    def order(self, col, desc=False):
        self._order, self._desc = col, desc
        return self

    def limit(self, n):
        self._limit = n
        return self

    def execute(self):
        rows = self.db.tables.setdefault(self.table, [])
        if self.action == "insert":
            items = self.payload if isinstance(self.payload, list) else [self.payload]
            new = [self.db.fill(self.table, dict(i)) for i in items]
            rows.extend(new)
            return MagicMock(data=new)

        matched = [r for r in rows if all(f(r) for f in self.filters)]
        if self.action == "update":
            for r in matched:
                r.update(self.payload)
            return MagicMock(data=matched)

        if self._order:
            matched = sorted(matched, key=lambda r: r[self._order], reverse=self._desc)
        if self._limit is not None:
            matched = matched[:self._limit]
        return MagicMock(data=[dict(r) for r in matched])


class FakeDB:
    ID_COLUMNS = {"conversations": "conversation_id", "messages": "message_id"}

    def __init__(self):
        self.tables = {}
        self._clock = itertools.count()
        self._base = datetime(2026, 11, 25, tzinfo=timezone.utc)

    def fill(self, table, row):
        """DB の既定値（ID と、呼ぶたびに進む created_at）を入れる"""
        if table in self.ID_COLUMNS:
            row.setdefault(self.ID_COLUMNS[table], str(uuid.uuid4()))
        row.setdefault("created_at", (self._base + timedelta(seconds=next(self._clock))).isoformat())
        return row

    def table(self, name):
        return FakeQuery(self, name)


@pytest.fixture
def db():
    fake = FakeDB()
    with patch.object(history, "get_supabase", return_value=fake):
        yield fake


def _add_turns(db, conversation_id, n):
    for i in range(n):
        history.save_turn(conversation_id, f"質問{i}", f"回答{i}")


def _conversation(db, user_id="u1", chatbot_id=BOT_ID):
    return history.create_conversation(chatbot_id, user_id)


# =========================================================
# history.prepare_history
# =========================================================

def test_short_history_is_sent_as_is(db):
    conv = _conversation(db)
    _add_turns(db, conv["conversation_id"], 3)

    with patch.object(history, "summarize_conversation") as summarize:
        summary, past = history.prepare_history(conv)

    summarize.assert_not_called()
    assert summary == ""
    assert [m["role"] for m in past] == ["user", "assistant"] * 3
    assert past[0]["content"] == "質問0" and past[-1]["content"] == "回答2"


def test_long_history_is_summarized_and_saved(db):
    conv = _conversation(db)
    _add_turns(db, conv["conversation_id"], 9)   # 18件 > HISTORY_MAX_MESSAGES(16)

    with patch.object(history, "summarize_conversation", return_value="・要約A") as summarize:
        summary, past = history.prepare_history(conv)

    # 古い12件を要約し、直近6件はそのまま送る
    old = summarize.call_args.args[1]
    assert summarize.call_args.args[0] == ""
    assert len(old) == 18 - config.HISTORY_KEEP_MESSAGES
    assert old[0]["content"] == "質問0"
    assert summary == "・要約A"
    assert [m["content"] for m in past] == ["質問6", "回答6", "質問7", "回答7", "質問8", "回答8"]

    # 要約と「どこまで要約したか」が保存されている
    saved = db.tables["conversations"][0]
    assert saved["summary"] == "・要約A"
    assert saved["summarized_until"] == db.tables["messages"][11]["created_at"]

    # 次回は要約済みの分を読まない（抜け・重複がない）
    with patch.object(history, "summarize_conversation") as summarize:
        summary, past = history.prepare_history(saved)
    summarize.assert_not_called()
    assert summary == "・要約A"
    assert past[0]["content"] == "質問6"


def test_summary_is_merged_with_previous_summary(db):
    conv = _conversation(db)
    _add_turns(db, conv["conversation_id"], 9)
    with patch.object(history, "summarize_conversation", return_value="・要約A"):
        history.prepare_history(conv)

    conv = db.tables["conversations"][0]
    _add_turns(db, conv["conversation_id"], 6)   # 未要約が 6 + 12 = 18件
    with patch.object(history, "summarize_conversation", return_value="・要約B") as summarize:
        summary, past = history.prepare_history(conv)

    assert summarize.call_args.args[0] == "・要約A"   # 前回の要約と統合する
    assert summary == "・要約B" and len(past) == config.HISTORY_KEEP_MESSAGES


def test_long_messages_trigger_summary(db, monkeypatch):
    monkeypatch.setattr(config, "MAX_HISTORY_CHARS", 1000)
    conv = _conversation(db)
    for i in range(3):
        history.save_turn(conv["conversation_id"], "長い質問" * 100, "長い回答" * 100)

    with patch.object(history, "summarize_conversation", return_value="・要約"):
        _, past = history.prepare_history(conv)

    assert sum(len(m["content"]) for m in past) <= 1000
    assert all(len(m["content"]) <= config.MAX_MESSAGE_CHARS + 1 for m in past)


def test_summary_failure_still_answers(db):
    conv = _conversation(db)
    _add_turns(db, conv["conversation_id"], 9)

    with patch.object(history, "summarize_conversation", side_effect=LLMError("down")):
        summary, past = history.prepare_history(conv)

    assert summary == "" and len(past) == config.HISTORY_KEEP_MESSAGES
    # 保存しないので、次の質問でまた要約を試す
    assert db.tables["conversations"][0].get("summarized_until") is None


def test_get_conversation_only_returns_own(db):
    conv = _conversation(db, user_id="u1")
    cid = conv["conversation_id"]

    assert history.get_conversation(cid, BOT_ID, "u1")
    assert history.get_conversation(cid, BOT_ID, "u2") is None
    assert history.get_conversation(cid, OTHER_BOT_ID, "u1") is None


# =========================================================
# service.chat
# =========================================================

def _answer(text="回答です"):
    return {"answer": text, "input_tokens": 1, "output_tokens": 1, "cost_yen": 0.0,
            "incomplete": False, "provider": "ollama", "model": "m", "elapsed_sec": 0.1}


def test_chat_starts_and_continues_conversation(db):
    with patch.object(service, "search", return_value=[]) as search, \
            patch.object(service, "generate_answer", return_value=_answer("防水です")) as gen:
        first = service.chat(BOT_ID, "u1", "この製品は防水？")
        cid = first["conversation_id"]

        gen.return_value = _answer("1万円です")
        second = service.chat(BOT_ID, "u1", "それはいくら？", cid)

    assert second["conversation_id"] == cid
    # 2回目は1回目のやりとりを履歴として渡す
    assert gen.call_args.kwargs["history"] == [
        {"role": "user", "content": "この製品は防水？"},
        {"role": "assistant", "content": "防水です"},
    ]
    # 検索には直前の質問もつなげる
    assert search.call_args.args[1] == "それはいくら？\nこの製品は防水？"
    assert [m["content"] for m in history.list_messages(cid)] == [
        "この製品は防水？", "防水です", "それはいくら？", "1万円です",
    ]


def test_chat_does_not_create_conversation_when_llm_fails(db):
    with patch.object(service, "search", return_value=[]), \
            patch.object(service, "generate_answer", side_effect=LLMError("down")):
        with pytest.raises(LLMError):
            service.chat(BOT_ID, "u1", "質問")

    assert db.tables.get("conversations", []) == []


def test_chat_rejects_others_conversation(db):
    conv = _conversation(db, user_id="u2")
    with pytest.raises(service.ConversationNotFound):
        service.chat(BOT_ID, "u1", "質問", conv["conversation_id"])


# =========================================================
# llm：履歴と要約の渡し方
# =========================================================

def test_generate_answer_sends_history_and_summary(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "ollama")
    ok = MagicMock(status_code=200)
    ok.json.return_value = {"message": {"content": "はい"}, "done_reason": "stop"}
    past = [{"role": "user", "content": "前の質問"}, {"role": "assistant", "content": "前の回答"}]

    with patch.object(llm.requests, "post", return_value=ok) as post:
        llm.generate_answer("今の質問", "資料本文", history=past, summary="・要約")

    messages = post.call_args.kwargs["json"]["messages"]
    assert [m["role"] for m in messages] == ["system", "user", "assistant", "user"]
    assert messages[1]["content"] == "前の質問"
    assert "<これまでの会話の要約>\n・要約" in messages[-1]["content"]
    assert "資料本文" in messages[-1]["content"] and "今の質問" in messages[-1]["content"]


def test_summarize_conversation(monkeypatch):
    monkeypatch.setattr(llm, "LLM_PROVIDER", "ollama")
    ok = MagicMock(status_code=200)
    ok.json.return_value = {"message": {"content": "・防水について質問" + "あ" * 5000}}

    with patch.object(llm.requests, "post", return_value=ok) as post:
        summary = llm.summarize_conversation(
            "・前の要約", [{"role": "user", "content": "防水？"}, {"role": "assistant", "content": "はい"}]
        )

    sent = post.call_args.kwargs["json"]["messages"][-1]["content"]
    assert "・前の要約" in sent and "ユーザー: 防水？" in sent and "アシスタント: はい" in sent
    assert len(summary) == config.MAX_SUMMARY_CHARS


# =========================================================
# API
# =========================================================

@pytest.fixture
def client():
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app.test_client()


def _login(user_id="u1"):
    user = {"user_id": user_id} if user_id else None
    return patch("bot_chat.routes.get_current_user", return_value=user)


def _owner_db(creator_id="owner", purchased=False):
    """chatbot と purchases の検索結果を返す偽の supabase"""
    sb = MagicMock()

    def table(name):
        q = MagicMock()
        chain = q.select.return_value.eq.return_value
        if name == "chatbot":
            chain.limit.return_value.execute.return_value.data = (
                [{"creator_id": creator_id}] if creator_id else []
            )
        else:
            chain.eq.return_value.limit.return_value.execute.return_value.data = (
                [{"purchase_id": "p"}] if purchased else []
            )
        return q

    sb.table.side_effect = table
    return patch("bot_chat.routes.supabase", sb)


def test_ask_requires_login(client):
    with _login(None):
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={"question": "q"})
    assert res.status_code == 401


def test_ask_rejects_invalid_id(client):
    with _login():
        res = client.post("/api/bots/not-a-uuid/ask", json={"question": "q"})
    assert res.status_code == 400


def test_ask_unknown_bot(client):
    with _login(), _owner_db(creator_id=None):
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={"question": "q"})
    assert res.status_code == 404


def test_ask_requires_purchase(client):
    with _login("u1"), _owner_db(creator_id="owner", purchased=False):
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={"question": "q"})
    assert res.status_code == 403


def test_ask_requires_question(client):
    with _login("owner"), _owner_db():
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={})
    assert res.status_code == 400


@pytest.mark.parametrize("user_id, purchased", [("owner", False), ("buyer", True)])
def test_ask_success_for_owner_and_buyer(client, user_id, purchased):
    result = dict(_answer("はい"), sources=[{"file_name": "a.pdf", "page": 1, "similarity": 0.9}],
                  conversation_id="c1")
    with _login(user_id), _owner_db(purchased=purchased), \
            patch("bot_chat.routes.chat", return_value=result) as chat:
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={"question": "防水？"})

    assert res.status_code == 200
    assert res.get_json() == {
        "answer": "はい", "sources": result["sources"], "conversation_id": "c1", "incomplete": False,
    }
    assert chat.call_args.args == (BOT_ID, user_id, "防水？", None)


def test_ask_returns_503_when_llm_fails(client):
    with _login("owner"), _owner_db(), \
            patch("bot_chat.routes.chat", side_effect=LLMError("down")):
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={"question": "q"})
    assert res.status_code == 503


def test_ask_unknown_conversation(client):
    cid = str(uuid.uuid4())
    with _login("owner"), _owner_db(), \
            patch("bot_chat.routes.chat", side_effect=service.ConversationNotFound()):
        res = client.post(f"/api/bots/{BOT_ID}/ask", json={"question": "q", "conversation_id": cid})
    assert res.status_code == 404


def test_get_messages(client, db):
    conv = _conversation(db, user_id="owner")
    _add_turns(db, conv["conversation_id"], 1)

    with _login("owner"), _owner_db():
        ok = client.get(f"/api/bots/{BOT_ID}/conversations/{conv['conversation_id']}/messages")
        listed = client.get(f"/api/bots/{BOT_ID}/conversations")

    assert [m["content"] for m in ok.get_json()["messages"]] == ["質問0", "回答0"]
    assert listed.get_json()["conversations"][0]["conversation_id"] == conv["conversation_id"]

    with _login("buyer"), _owner_db(purchased=True):
        other = client.get(f"/api/bots/{BOT_ID}/conversations/{conv['conversation_id']}/messages")
    assert other.status_code == 404   # 他人の会話は見えない


# =========================================================
# PDFアップロード時の取り込み・再取り込み
# =========================================================

def test_ingest_pdf_safely_never_raises():
    with patch.object(service, "ingest_pdf", side_effect=RuntimeError("Ollamaに接続できません")):
        assert service.ingest_pdf_safely("b", "p", b"x", "a.pdf") is False
    with patch.object(service, "ingest_pdf", return_value={}):
        assert service.ingest_pdf_safely("b", "p", b"x", "a.pdf") is True


def test_upload_calls_rag_ingest_without_changing_response():
    from bot_creation import routes as bc

    file = MagicMock(filename="manual.pdf")
    file.read.return_value = b"%PDF"
    with patch.object(bc, "_validate_pdf", return_value=None), \
            patch.object(bc, "_extract_text_from_pdf", return_value="本文"), \
            patch.object(bc, "supabase") as sb, \
            patch.object(bc, "ingest_pdf_safely", return_value=False) as ingest:
        sb.table.return_value.insert.return_value.execute.return_value.data = [{"pdf_id": "pdf-1"}]
        result = bc._upload_single_pdf("bot-1", file)

    ingest.assert_called_once_with("bot-1", "pdf-1", b"%PDF", "manual.pdf")
    # 取り込みに失敗してもアップロードは成功し、レスポンスの形も変わらない
    assert result == {"pdf_id": "pdf-1", "file_name": "manual.pdf"}


def _reindex_db(creator_id="owner", pdfs=(), download_error=False):
    sb = MagicMock()

    def table(name):
        q = MagicMock()
        if name == "chatbot":
            q.select.return_value.eq.return_value.limit.return_value.execute.return_value.data = (
                [{"creator_id": creator_id}] if creator_id else []
            )
        else:
            q.select.return_value.eq.return_value.execute.return_value.data = list(pdfs)
        return q

    sb.table.side_effect = table
    if download_error:
        sb.storage.from_.return_value.download.side_effect = RuntimeError("not found")
    else:
        sb.storage.from_.return_value.download.return_value = b"%PDF"
    return patch("bot_chat.routes.supabase", sb)


def test_reindex_only_for_creator(client):
    with _login("buyer"), _reindex_db(creator_id="owner"):
        res = client.post(f"/api/bots/{BOT_ID}/reindex")
    assert res.status_code == 403

    with _login(None):
        assert client.post(f"/api/bots/{BOT_ID}/reindex").status_code == 401


def test_reindex_ingests_all_pdfs(client):
    pdfs = [
        {"pdf_id": "p1", "file_path": f"{BOT_ID}/a.pdf", "file_name": "説明書.pdf"},
        {"pdf_id": "p2", "file_path": f"{BOT_ID}/b.pdf", "file_name": "保証書.pdf"},
    ]
    with _login("owner"), _reindex_db(pdfs=pdfs), \
            patch("bot_chat.routes.ingest_pdf_safely", side_effect=[True, False]) as ingest:
        res = client.post(f"/api/bots/{BOT_ID}/reindex")

    assert res.status_code == 200
    assert [r["indexed"] for r in res.get_json()["results"]] == [True, False]
    assert ingest.call_args_list[0].args == (BOT_ID, "p1", b"%PDF", "説明書.pdf")
    assert "1/2件" in res.get_json()["message"]


def test_reindex_reports_download_failure(client):
    pdfs = [{"pdf_id": "p1", "file_path": "x", "file_name": "a.pdf"}]
    with _login("owner"), _reindex_db(pdfs=pdfs, download_error=True), \
            patch("bot_chat.routes.ingest_pdf_safely") as ingest:
        res = client.post(f"/api/bots/{BOT_ID}/reindex")

    assert res.get_json()["results"][0]["indexed"] is False
    ingest.assert_not_called()
