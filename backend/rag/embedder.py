"""
埋め込み（ベクトル化）

.env の EMBED_PROVIDER で切り替える
- local  : multilingual-e5-small（無料・384次元）
- openai : text-embedding-3-small（有料・1536次元）

どちらも同じ形で返すので、呼び出し側は切り替えを意識しなくてよい。
"""

import threading

from rag.config import (
    API_MAX_RETRIES,
    API_TIMEOUT,
    EMBED_DIMENSIONS,
    EMBED_MODEL,
    EMBED_PROVIDER,
    EMBED_USD_PER_M,
    LOCAL_EMBED_DEVICE,
    MAX_QUESTION_CHARS,
    USD_JPY,
)

MAX_PASSAGE_CHARS = 6000   # OpenAIの入力上限（約8,000トークン）を超えないための保険

_client = None
_local_model = None
_lock = threading.Lock()


# =========================================================
# OpenAIクライアント（llm.py からも使う）
# =========================================================

def get_client():
    """OpenAIクライアントは1回だけ作る（OPENAI_API_KEY は .env から読む）"""
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(max_retries=API_MAX_RETRIES, timeout=API_TIMEOUT)
    return _client


def set_client_for_test(client):
    global _client
    _client = client


# =========================================================
# ローカルモデル（e5）
# =========================================================

def get_local_model():
    """e5モデルを1回だけ読み込む（同時アクセスでも安全）"""
    global _local_model
    if _local_model is None:
        with _lock:
            if _local_model is None:
                from sentence_transformers import SentenceTransformer
                _local_model = SentenceTransformer(EMBED_MODEL, device=LOCAL_EMBED_DEVICE)
    return _local_model


def set_local_model_for_test(model):
    global _local_model
    _local_model = model


def _count_local_tokens(text):
    return len(get_local_model().tokenizer("passage: " + text)["input_ids"])


def _fit_local_limit(chunk):
    """e5の上限（512トークン）を超えるチャンクを分け直す"""
    if _count_local_tokens(chunk) <= get_local_model().max_seq_length:
        return [chunk]

    middle = len(chunk) // 2
    cut = chunk.rfind("\n", 0, middle)
    if cut <= 0:
        cut = chunk.rfind("。", 0, middle) + 1
    if cut <= 0:
        cut = middle

    result = []
    for part in (chunk[:cut].strip(), chunk[cut:].strip()):
        if part:
            result.extend(_fit_local_limit(part))
    return result


# =========================================================
# 共通の入口
# =========================================================

def prepare_chunks(chunks):
    """
    埋め込み前にチャンクを整える。
    ローカルは512トークン上限があるので分け直す。OpenAIはそのまま。
    """
    chunks = [c for c in chunks if c and c.strip()]
    if EMBED_PROVIDER != "local":
        return chunks

    result = []
    for chunk in chunks:
        result.extend(_fit_local_limit(chunk))
    return result


def _embed(texts, is_query):
    """(ベクトルのリスト, 使ったトークン数) を返す"""
    if EMBED_PROVIDER == "local":
        prefix = "query: " if is_query else "passage: "
        model = get_local_model()
        vectors = model.encode(
            [prefix + t for t in texts],
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        tokens = 0   # ローカルは費用がかからないので数えない

    else:
        from openai import RateLimitError
        try:
            response = get_client().embeddings.create(
                model=EMBED_MODEL,
                input=texts,
                dimensions=EMBED_DIMENSIONS,
            )
        except RateLimitError as error:
            if "credits" in str(error) or "insufficient_quota" in str(error):
                raise RuntimeError(
                    "OpenAIのクレジット残高がありません。"
                    "EMBED_PROVIDER=local に切り替えるか、請求設定を確認してください。"
                ) from error
            raise

        data = sorted(response.data, key=lambda item: item.index)
        vectors = [item.embedding for item in data]
        tokens = response.usage.total_tokens

    if any(len(v) != EMBED_DIMENSIONS for v in vectors):
        raise RuntimeError("埋め込みの次元数が設定と一致しません")

    return vectors, tokens


def embed_passages(texts, batch_size=100):
    """
    資料のチャンクをベクトルにする。
    戻り値: (ベクトルのリスト, 使ったトークン数)
    ※ 事前に prepare_chunks() を通しておくこと
    """
    if any(not t or not t.strip() for t in texts):
        raise ValueError("空のチャンクが含まれています")

    texts = [t[:MAX_PASSAGE_CHARS] for t in texts]
    vectors, tokens = [], 0

    for start in range(0, len(texts), batch_size):
        v, t = _embed(texts[start:start + batch_size], is_query=False)
        vectors.extend(v)
        tokens += t

    return vectors, tokens


def embed_query(text):
    """質問をベクトルにする"""
    text = (text or "").strip()[:MAX_QUESTION_CHARS]
    if not text:
        raise ValueError("質問が空です")

    vectors, _ = _embed([text], is_query=True)
    return vectors[0]


def embed_cost_yen(tokens):
    """埋め込みにかかった費用（円）。ローカルは0"""
    if EMBED_PROVIDER == "local":
        return 0.0
    return round(tokens * EMBED_USD_PER_M / 1_000_000 * USD_JPY, 4)


def warm_up():
    """Flask起動時に呼ぶと、最初の質問が速くなる（ローカルのみ効果あり）"""
    if EMBED_PROVIDER == "local":
        get_local_model()