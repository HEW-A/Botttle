import io
from unittest.mock import patch, MagicMock

import pytest

from bot_creation.routes import (
    _validate_pdf,
    _extract_text_from_pdf,
    _upload_single_pdf,
    _process_pdfs,
    MAX_FILE_SIZE_MB,
    MAX_PAGE_COUNT,
)


class FakeFile:
    """request.files から渡されるファイルオブジェクトの代わりに使う、テスト用の偽物"""
    def __init__(self, filename, content: bytes = b"dummy content"):
        self.filename = filename
        self._content = content

    def read(self):
        return self._content


# ============================================================
# _validate_pdf のテスト
# ============================================================

def test_rejects_non_pdf_extension():
    file = FakeFile("image.png")
    error = _validate_pdf(file, b"dummy content")
    assert error == "PDFファイルではありません"


def test_rejects_oversized_file():
    file = FakeFile("big.pdf")
    too_big_bytes = b"a" * (MAX_FILE_SIZE_MB * 1024 * 1024 + 1)
    error = _validate_pdf(file, too_big_bytes)
    assert error == f"ファイルサイズが上限({MAX_FILE_SIZE_MB}MB)を超えています"


def test_accepts_valid_pdf_within_page_limit():
    file = FakeFile("valid.pdf")

    # PdfReaderが「5ページのPDF」を返したことにする、偽物を用意する
    fake_reader = MagicMock()
    fake_reader.pages = [MagicMock() for _ in range(5)]

    with patch("bot_creation.routes.PdfReader", return_value=fake_reader):
        error = _validate_pdf(file, b"dummy small pdf content")

    assert error is None


def test_rejects_pdf_over_page_limit():
    file = FakeFile("toolong.pdf")

    # PdfReaderが「上限を超えるページ数」を返したことにする
    fake_reader = MagicMock()
    fake_reader.pages = [MagicMock() for _ in range(MAX_PAGE_COUNT + 1)]

    with patch("bot_creation.routes.PdfReader", return_value=fake_reader):
        error = _validate_pdf(file, b"dummy content")

    assert error == f"ページ数が上限({MAX_PAGE_COUNT}ページ)を超えています"


def test_rejects_broken_pdf():
    file = FakeFile("broken.pdf")

    with patch("bot_creation.routes.PdfReader", side_effect=Exception("cannot read")):
        error = _validate_pdf(file, b"corrupted bytes")

    assert error == "PDFの読み込みに失敗しました(壊れている可能性があります)"


def test_sanitize_removes_null_byte():
    from bot_creation.routes import _sanitize_extracted_text

    result = _sanitize_extracted_text("テキスト\x00不正な文字")
    assert result == "テキスト不正な文字"
    assert "\x00" not in result


def test_sanitize_removes_other_control_characters():
    from bot_creation.routes import _sanitize_extracted_text

    result = _sanitize_extracted_text("あ\x01い\x1fう")
    assert result == "あいう"


def test_sanitize_keeps_tabs_and_newlines():
    from bot_creation.routes import _sanitize_extracted_text

    result = _sanitize_extracted_text("1行目\n2行目\tタブ入り")
    assert result == "1行目\n2行目\tタブ入り"


def test_sanitize_handles_empty_string():
    from bot_creation.routes import _sanitize_extracted_text

    assert _sanitize_extracted_text("") == ""
    assert _sanitize_extracted_text(None) is None


def test_extract_text_from_pdf_removes_null_bytes():
    fake_page = MagicMock()
    fake_page.extract_text.return_value = "テキスト\x00不正な文字を含む"

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page]

    with patch("bot_creation.routes.PdfReader", return_value=fake_reader):
        result = _extract_text_from_pdf(b"dummy pdf bytes")

    assert "\x00" not in result
    assert result == "テキスト不正な文字を含む\n"

# ============================================================
# _extract_text_from_pdf のテスト
# ============================================================

def test_extract_text_from_pdf_joins_all_pages():
    fake_page1 = MagicMock()
    fake_page1.extract_text.return_value = "1ページ目の内容"
    fake_page2 = MagicMock()
    fake_page2.extract_text.return_value = "2ページ目の内容"

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page1, fake_page2]

    with patch("bot_creation.routes.PdfReader", return_value=fake_reader):
        result = _extract_text_from_pdf(b"dummy pdf bytes")

    assert result == "1ページ目の内容\n2ページ目の内容\n"


def test_extract_text_from_pdf_skips_pages_with_no_text():
    fake_page1 = MagicMock()
    fake_page1.extract_text.return_value = None  # 画像だけのページなど
    fake_page2 = MagicMock()
    fake_page2.extract_text.return_value = "テキストあり"

    fake_reader = MagicMock()
    fake_reader.pages = [fake_page1, fake_page2]

    with patch("bot_creation.routes.PdfReader", return_value=fake_reader):
        result = _extract_text_from_pdf(b"dummy pdf bytes")

    assert result == "テキストあり\n"


# ============================================================
# _upload_single_pdf のテスト
# ============================================================

def test_upload_single_pdf_success():
    file = FakeFile("manual.pdf")

    with patch("bot_creation.routes._validate_pdf", return_value=None), \
         patch("bot_creation.routes._extract_text_from_pdf", return_value="抽出されたテキスト"), \
         patch("bot_creation.routes.supabase") as mock_supabase:

        mock_supabase.storage.from_.return_value.upload.return_value = None

        mock_insert_result = MagicMock()
        mock_insert_result.data = [{"pdf_id": "pdf-uuid-123"}]
        mock_supabase.table.return_value.insert.return_value.execute.return_value = mock_insert_result

        result = _upload_single_pdf("chatbot-uuid-1", file)

    assert result == {"pdf_id": "pdf-uuid-123", "file_name": "manual.pdf"}


def test_upload_single_pdf_raises_when_validation_fails():
    file = FakeFile("image.png")

    with patch("bot_creation.routes._validate_pdf", return_value="PDFファイルではありません"):
        with pytest.raises(ValueError, match="PDFファイルではありません"):
            _upload_single_pdf("chatbot-uuid-1", file)


def test_upload_single_pdf_raises_when_storage_upload_fails():
    file = FakeFile("manual.pdf")

    with patch("bot_creation.routes._validate_pdf", return_value=None), \
         patch("bot_creation.routes.supabase") as mock_supabase:

        mock_supabase.storage.from_.return_value.upload.side_effect = Exception("storage error")

        with pytest.raises(Exception, match="storage error"):
            _upload_single_pdf("chatbot-uuid-1", file)


# ============================================================
# _process_pdfs のテスト
# ============================================================

def test_process_pdfs_separates_success_and_failure():
    file_ok = FakeFile("ok.pdf")
    file_ng = FakeFile("bad.pdf")

    def fake_upload(chatbot_id, file):
        if file.filename == "ok.pdf":
            return {"pdf_id": "pdf-1", "file_name": "ok.pdf"}
        raise ValueError("PDFファイルではありません")

    with patch("bot_creation.routes._upload_single_pdf", side_effect=fake_upload):
        uploaded, failed = _process_pdfs("chatbot-uuid-1", [file_ok, file_ng])

    assert uploaded == [{"pdf_id": "pdf-1", "file_name": "ok.pdf"}]
    assert failed == [{"file_name": "bad.pdf", "reason": "PDFファイルではありません"}]


def test_process_pdfs_all_success():
    files = [FakeFile("a.pdf"), FakeFile("b.pdf")]

    def fake_upload(chatbot_id, file):
        return {"pdf_id": f"pdf-{file.filename}", "file_name": file.filename}

    with patch("bot_creation.routes._upload_single_pdf", side_effect=fake_upload):
        uploaded, failed = _process_pdfs("chatbot-uuid-1", files)

    assert len(uploaded) == 2
    assert failed == []


def test_process_pdfs_all_failure():
    files = [FakeFile("a.png"), FakeFile("b.png")]

    def fake_upload(chatbot_id, file):
        raise ValueError("PDFファイルではありません")

    with patch("bot_creation.routes._upload_single_pdf", side_effect=fake_upload):
        uploaded, failed = _process_pdfs("chatbot-uuid-1", files)

    assert uploaded == []
    assert len(failed) == 2