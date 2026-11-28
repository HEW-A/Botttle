"""
RAGの設定をまとめる。.env で上書きできる。
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# backend/.env を読む（どこから実行しても同じファイルを読む）
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# ===== 埋め込み（local / openai を切り替え） =====
EMBED_PROVIDER = os.getenv("EMBED_PROVIDER", "local")

LOCAL_EMBED_MODEL = "intfloat/multilingual-e5-small"
LOCAL_EMBED_DEVICE = os.getenv("LOCAL_EMBED_DEVICE", "cpu")   # OllamaとVRAMを取り合わない
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

_EMBED_SETTINGS = {
    # 提供元: (モデル名, 次元数, DBの列名, 検索関数名)
    "local":  (LOCAL_EMBED_MODEL,  384,  "embedding_local",  "match_bot_chunks_local"),
    "openai": (OPENAI_EMBED_MODEL, 1536, "embedding_openai", "match_bot_chunks_openai"),
}

if EMBED_PROVIDER not in _EMBED_SETTINGS:
    raise ValueError(f"EMBED_PROVIDER の値が不正です: {EMBED_PROVIDER}（local / openai）")

EMBED_MODEL, EMBED_DIMENSIONS, EMBED_COLUMN, MATCH_FUNCTION = _EMBED_SETTINGS[EMBED_PROVIDER]

# ===== 回答生成（ollama / openai を切り替え） =====
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-6-luna")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma4:e4b")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

REASONING_EFFORT = os.getenv("RAG_REASONING_EFFORT", "none")
MAX_OUTPUT_TOKENS = int(os.getenv("RAG_MAX_OUTPUT_TOKENS", "700"))

# Ollama が一度に読めるトークン数（CUDAエラー対策で小さめ。GPUに余裕があれば .env で増やす）
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "4096"))

# LLMに送る文字数の予算。Ollama は num_ctx が小さいので、資料・履歴を少なめにする
# （予算を超えると Ollama は古い部分を黙って切り捨て、システムプロンプトが消えることがある）
_IS_OLLAMA = LLM_PROVIDER == "ollama"

# ===== API共通 =====
API_TIMEOUT = 60
API_MAX_RETRIES = 5

# ===== 料金（米ドル／100万トークン）。ローカルは0円 =====
CHAT_INPUT_USD_PER_M = 0.10
CHAT_OUTPUT_USD_PER_M = 0.50
EMBED_USD_PER_M = 0.02
USD_JPY = float(os.getenv("RAG_USD_JPY", "158"))

# ===== 保存 =====
INSERT_BATCH_SIZE = 200            # bot_chunk へ一度に保存する件数

# ===== 検索 =====
SEARCH_CANDIDATES = 40             # DBから取得する候補数
TOP_K = 8                          # LLMに渡すチャンク数の目安
MAX_CONTEXT_CHARS = int(os.getenv(  # LLMに渡す資料の最大文字数
    "RAG_MAX_CONTEXT_CHARS", "2500" if _IS_OLLAMA else "6000"))
MAX_QUESTION_CHARS = 1000          # 質問の最大文字数

# ===== 会話履歴 =====
# 要約されていないメッセージは、そのまま LLM に送る。
# 件数か文字数が上限を超えたら、直近だけ残して古い分を要約に回す。
HISTORY_MAX_MESSAGES = 16          # 要約していないメッセージがこれを超えたら要約する
HISTORY_KEEP_MESSAGES = 6          # 要約したあとも、そのまま送る直近のメッセージ数（3往復）
MAX_HISTORY_CHARS = int(os.getenv(  # そのまま送る履歴の最大文字数（超えたら要約する）
    "RAG_MAX_HISTORY_CHARS", "1500" if _IS_OLLAMA else "4000"))
MAX_MESSAGE_CHARS = 800            # 履歴の1メッセージあたりの最大文字数（長い回答は切り詰める）
MAX_SUMMARY_CHARS = 600 if _IS_OLLAMA else 1000   # 要約の最大文字数
SUMMARY_MAX_OUTPUT_TOKENS = 600    # 要約を作るときの出力上限

DOC_INFO_WORDS = (
    "機種名", "製品名", "端末名", "モデル名", "タイトル", "文書名",
    "ファイル名", "何の資料", "何についての資料", "何の説明書", "概要", "要約",
)