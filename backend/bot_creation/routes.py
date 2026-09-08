import io
import uuid
import re

from flask import Blueprint, request, jsonify
try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        class PdfReader:
            def __init__(self, *args, **kwargs):
                raise RuntimeError("pypdf(またはPyPDF2)がインストールされていません")

from common.supabase_client import supabase
from common.auth_helper import get_current_user

bot_creation_bp = Blueprint("bot_creation", __name__)

# --- 仮の上限設定(あとで変更しやすいよう、定数として一箇所にまとめる) ---
MAX_FILE_SIZE_MB = 20
MAX_PAGE_COUNT = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

BOT_PDF_BUCKET = "bot_pdfs"
DEFAULT_SALE_STATUS = "unlisted"


def _sanitize_extracted_text(text: str) -> str:
    # DB保存前に、PostgreSQLのtext型が扱えない制御文字を除去する。
    # - NULバイト(\\x00): PostgreSQLのtext型は保存できず、insert失敗の原因になる
    # - その他の制御文字(\\x01-\\x08, \\x0b, \\x0c, \\x0e-\\x1f): 表示・処理上問題を起こしうる
    # - タブ(\\t)・改行(\\n)・復帰(\\r)は、通常のテキストとして扱いたいので除去しない
    if not text:
        return text
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)

def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """PDFのバイナリデータから、テキスト部分だけを抜き出す"""
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return _sanitize_extracted_text(text)


def _validate_pdf(file, file_bytes: bytes) -> str | None:
    """PDFの形式・サイズ・ページ数をチェックする。問題があればエラーメッセージ、なければNone"""
    if not file.filename.lower().endswith(".pdf"):
        return "PDFファイルではありません"

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        return f"ファイルサイズが上限({MAX_FILE_SIZE_MB}MB)を超えています"

    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        if len(reader.pages) > MAX_PAGE_COUNT:
            return f"ページ数が上限({MAX_PAGE_COUNT}ページ)を超えています"
    except Exception:
        return "PDFの読み込みに失敗しました(壊れている可能性があります)"

    return None


def _upload_single_pdf(chatbot_id: str, file) -> dict:
    """PDF1件を検証・アップロード・DB登録する。成功情報を返し、失敗時は例外を投げる"""
    file_bytes = file.read()

    error = _validate_pdf(file, file_bytes)
    if error:
        raise ValueError(error)

    unique_name = f"{uuid.uuid4()}_{file.filename}"
    file_path = f"{chatbot_id}/{unique_name}"

    supabase.storage.from_(BOT_PDF_BUCKET).upload(
        file_path,
        file_bytes,
        {"content-type": "application/pdf"},
    )

    extracted_text = _extract_text_from_pdf(file_bytes)

    result = supabase.table("bot_pdf").insert({
        "chatbot_id": chatbot_id,
        "file_path": file_path,
        "file_name": file.filename,
        "extracted_text": extracted_text,
    }).execute()

    return {
        "pdf_id": result.data[0]["pdf_id"],
        "file_name": file.filename,
    }


def _process_pdfs(chatbot_id: str, files) -> tuple[list, list]:
    """複数PDFを1件ずつ処理し、(成功リスト, 失敗リスト)を返す"""
    uploaded = []
    failed = []

    for file in files:
        try:
            uploaded.append(_upload_single_pdf(chatbot_id, file))
        except Exception as e:
            failed.append({"file_name": file.filename, "reason": str(e)})

    return uploaded, failed


@bot_creation_bp.route("", methods=["POST"])
def create_bot_with_pdfs():
    current_user = get_current_user()
    if not current_user:
        return jsonify({"error": "ログインが必要です"}), 401

    creator_id = current_user["id"]
    bot_name = request.form.get("bot_name")
    description = request.form.get("description")
    category_id = request.form.get("category_id")

    if not bot_name:
        return jsonify({"error": "bot_name は必須です"}), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify({"error": "PDFファイルが送られていません"}), 400

    try:
        chatbot_result = supabase.table("chatbot").insert({
            "bot_name": bot_name,
            "description": description,
            "category_id": category_id,
            "creator_id": creator_id,
            "sale_status": DEFAULT_SALE_STATUS,
        }).execute()
    except Exception as e:
        return jsonify({"error": f"チャットボットの登録に失敗しました: {str(e)}"}), 500

    chatbot_id = chatbot_result.data[0]["chatbot_id"]

    uploaded, failed = _process_pdfs(chatbot_id, files)

    return jsonify({
        "message": f"チャットボットを作成し、{len(uploaded)}件のPDFを保存しました",
        "chatbot_id": chatbot_id,
        "uploaded": uploaded,
        "failed": failed,
    }), 201