"""
ベクトル検索
質問を埋め込み → Supabase の検索関数（rpc）で候補を取得
→ キーワード一致・文書情報・ファイル指定で並べ替え → LLM に渡す文脈を作る
"""

import re

from rag import config
from rag.db import get_supabase
from rag.embedder import embed_query

MIN_SIMILARITY = 0.0        # 低すぎる候補を捨てたいときに上げる（e5なら0.75前後から調整）
KEYWORD_WEIGHT = 0.01       # キーワード1件一致あたりの加点
KEYWORD_MAX = 20            # キーワード加点の上限（長いチャンクが有利になりすぎないように）
DOC_INFO_BONUS = 1.0        # 「機種名」などの質問で文書情報を最優先にする


def bigrams(text):
    """日本語は単語の区切りがないので、2文字ずつに分ける"""
    text = re.sub(r"\s+", "", text or "")
    return {text[i:i + 2] for i in range(len(text) - 1)}


def _target_files(question, rows):
    """質問に書かれたファイル名（複数可）を見つける"""
    q = question.lower()
    names = {r["file_name"] for r in rows}
    return [name for name in names if name and name.lower() in q]


def search(chatbot_id, question, top_k=None):
    """指定ボットのチャンクを、関連度の高い順に返す"""
    top_k = top_k or config.TOP_K
    query_vec = embed_query(question)

    res = get_supabase().rpc(
        config.MATCH_FUNCTION,
        {
            "p_chatbot_id": str(chatbot_id),
            "query_embedding": query_vec,
            "match_count": config.SEARCH_CANDIDATES,
        },
    ).execute()

    rows = [r for r in (res.data or []) if r["similarity"] >= MIN_SIMILARITY]
    if not rows:
        return []

    # 質問でファイルが指定されていれば、そのファイルに絞る
    targets = _target_files(question, rows)
    if targets:
        rows = [r for r in rows if r["file_name"] in targets]

    # 意味の近さ ＋ キーワード一致 ＋ 文書情報の優先
    q_grams = bigrams(question)
    wants_doc_info = any(word in question for word in config.DOC_INFO_WORDS)

    for r in rows:
        overlap = len(q_grams & bigrams(r["content"]))
        r["score"] = r["similarity"] + KEYWORD_WEIGHT * min(overlap, KEYWORD_MAX)
        if r.get("is_doc_info") and wants_doc_info:
            r["score"] += DOC_INFO_BONUS

    rows.sort(key=lambda r: r["score"], reverse=True)

    # 複数ファイルを比較する質問では、各ファイルの最上位を必ず残す
    guaranteed = []
    if len(targets) > 1:
        for name in targets:
            best = next((r for r in rows if r["file_name"] == name), None)
            if best:
                guaranteed.append(best)

    selected = list({r["chunk_id"]: r for r in guaranteed + rows}.values())
    return selected[:max(top_k, len(guaranteed))]


def _label(chunk):
    """出典の表示名"""
    if chunk.get("is_doc_info"):
        return f"{chunk['file_name']} [文書情報]"
    page = f" p.{chunk['page']}" if chunk.get("page") else ""
    return f"{chunk['file_name']}{page}"


def _block(chunk):
    return f"[資料: {_label(chunk)}]\n{chunk['content']}"


def fit_context(chunks):
    """MAX_CONTEXT_CHARS に収まる分だけ、上位から順にチャンクを選ぶ"""
    selected, total = [], 0
    for c in chunks:
        size = len(_block(c)) + (2 if selected else 0)   # 区切りの "\n\n" 分
        if total + size > config.MAX_CONTEXT_CHARS:
            continue   # 大きすぎるものは飛ばして、次の小さいチャンクを試す
        selected.append(c)
        total += size
    return selected


def build_context(chunks):
    """
    LLM に渡す文脈。出典が分かるように資料名とページを付ける。
    事前に fit_context() で文字数を収めておくこと。
    """
    return "\n\n".join(_block(c) for c in chunks)


def to_sources(chunks):
    """フロントに返す出典一覧（同じ資料・ページは1つにまとめる）"""
    seen, sources = set(), []
    for c in chunks:
        if c.get("is_doc_info"):
            continue  # 文書情報はユーザー向けの出典には出さない
        key = (c["file_name"], c.get("page"))
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "file_name": c["file_name"],
            "page": c.get("page"),
            "similarity": round(c["similarity"], 3),
        })
    return sources