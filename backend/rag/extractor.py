
#資料の読み込みと、文書情報チャンクの作成
# read_document() は [(本文, ページ番号 or None), ...] を返す

import os
import re

import pymupdf


def _open_pdf(path):
    """PDFを開く。ファイルを掴んだままにしないよう、先にバイト列として読み込んでから渡す。"""
    with open(path, "rb") as f:
        pdf_bytes = f.read()
    return pymupdf.open(stream=pdf_bytes, filetype="pdf")



# =========================================================
# テキストのクリーニング
# =========================================================

def clean_text(text):

    if not text:
        return ""

    text = text.replace("\x00", "")

    text = re.sub(
        r"[\ue000-\uf8ff]",
        "",
        text
    )

    text = re.sub(
        r"[ \t\u3000]+",
        " ",
        text
    )

    text = "\n".join(
        line.strip()
        for line in text.splitlines()
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# =========================================================
# タイトル候補の判定
# =========================================================

def is_title_like(text):


    if not text:
        return False

    if len(text) < 2 or len(text) > 60:
        return False

    if re.fullmatch(
        r"[\d\s\-–—/.]+",
        text
    ):
        return False

    if re.search(
        r"[.…・]{4,}",
        text
    ):
        return False

    return True


# =========================================================
# TXT / Markdown読み込み
# =========================================================

def read_text_file(path):


    for encoding in (
        "utf-8-sig",
        "cp932"
    ):
        try:
            with open(
                path,
                encoding=encoding
            ) as file:

                return clean_text(
                    file.read()
                )

        except UnicodeDecodeError:
            continue

    raise ValueError(
        "文字コードを判別できません"
    )


# =========================================================
# 資料の読み込み
# =========================================================

def read_document(
    path,
    filename
):


    extension = os.path.splitext(
        filename
    )[1].lower()

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    if extension == ".pdf":

        try:
            with _open_pdf(path) as document:

                if document.needs_pass:
                    raise ValueError(
                        "パスワード付きPDFは使用できません"
                    )

                pages = []

                for page_number, page in enumerate(
                    document,
                    start=1
                ):
                    text = page.get_text(
                        sort=True
                    )

                    text = clean_text(
                        text
                    )

                    # (本文, ページ番号) の形で返す。ページ番号は1始まりの int
                    pages.append(
                        (
                            text,
                            page_number
                        )
                    )

        except ValueError:
            raise

        except Exception as error:
            raise ValueError(
                f"PDFを読み込めませんでした: {error}"
            ) from error

        if not pages:
            raise ValueError(
                "PDFにページがありません"
            )

        page_count = len(
            pages
        )

        total_chars = sum(
            len(text)
            for text, _ in pages
        )

        non_empty_pages = sum(
            1
            for text, _ in pages
            if len(text) >= 20
        )

        if total_chars == 0:
            raise ValueError(
                "PDFから文字を読み取れませんでした。"
                "画像だけのPDFの可能性があります。"
            )

        if (
            page_count >= 3
            and total_chars < 100
        ):
            raise ValueError(
                "PDFから十分な文字を読み取れませんでした。"
                "スキャン画像PDFの可能性があります。"
            )

        if page_count >= 5:

            readable_ratio = (
                non_empty_pages
                / page_count
            )

            if readable_ratio < 0.2:
                raise ValueError(
                    "文字を読み取れるページが少なすぎます。"
                    "スキャン画像PDFの可能性があります。"
                )

        return pages

    # -----------------------------------------------------
    # TXT / Markdown
    # -----------------------------------------------------

    if extension in (
        ".txt",
        ".md"
    ):
        text = read_text_file(
            path
        )

        if len(text) < 10:
            raise ValueError(
                "ファイルに十分な文字がありません"
            )

        # TXT / Markdown にはページがないので None
        return [
            (
                text,
                None
            )
        ]

    # -----------------------------------------------------
    # 未対応ファイル
    # -----------------------------------------------------

    raise ValueError(
        f"対応していないファイル形式です: {extension}"
    )


# =========================================================
# PDFタイトル候補
# =========================================================

def extract_pdf_title_candidates(
    path,
    max_pages=5,
    max_results=20
):

    candidates = []

    try:
        with pymupdf.open(
            path
        ) as document:

            if document.needs_pass:
                return []

            page_count = min(
                len(document),
                max_pages
            )

            for page_number in range(
                page_count
            ):
                page = document[
                    page_number
                ]

                page_dict = page.get_text(
                    "dict"
                )

                for block in page_dict.get(
                    "blocks",
                    []
                ):
                    if "lines" not in block:
                        continue

                    for line in block.get(
                        "lines",
                        []
                    ):
                        for span in line.get(
                            "spans",
                            []
                        ):
                            text = clean_text(
                                span.get(
                                    "text",
                                    ""
                                )
                            )

                            text = re.sub(
                                r"\s+",
                                " ",
                                text
                            ).strip()

                            if not is_title_like(
                                text
                            ):
                                continue

                            size = float(
                                span.get(
                                    "size",
                                    0
                                )
                            )

                            candidates.append(
                                (
                                    size,
                                    page_number,
                                    text
                                )
                            )

    except Exception:
        return []

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[1]
        )
    )

    results = []
    seen = set()

    for (
        size,
        page_number,
        text
    ) in candidates:

        key = text.lower()

        if key in seen:
            continue

        seen.add(
            key
        )

        results.append(
            text
        )

        if (
            len(results)
            >= max_results
        ):
            break

    return results


# =========================================================
# 文書冒頭の作成
# =========================================================

def extract_document_beginning(
    pages,
    max_pages=5,
    max_chars=2500
):

    beginning_parts = []

    for text, _page in pages[
        :max_pages
    ]:
        cleaned = clean_text(
            text
        )

        cleaned = re.sub(
            r"\s+",
            " ",
            cleaned
        ).strip()

        if not cleaned:
            continue

        beginning_parts.append(
            cleaned
        )

    beginning = "\n".join(
        beginning_parts
    )

    return beginning[
        :max_chars
    ]


# =========================================================
# 文書情報チャンク作成
# =========================================================

def create_document_info(
    path,
    filename,
    pages
):

    extension = os.path.splitext(
        filename
    )[1].lower()

    metadata_title = ""
    title_candidates = []

    # -----------------------------------------------------
    # PDF固有の情報
    # -----------------------------------------------------

    if extension == ".pdf":

        try:
            with _open_pdf(path) as document:

                if not document.needs_pass:

                    metadata = (
                        document.metadata
                        or {}
                    )

                    metadata_title = (
                        clean_text(
                            metadata.get(
                                "title"
                            )
                            or ""
                        )
                    )

        except Exception:
            metadata_title = ""

        title_candidates = (
            extract_pdf_title_candidates(
                path
            )
        )

    # -----------------------------------------------------
    # 文書冒頭
    # -----------------------------------------------------

    beginning = (
        extract_document_beginning(
            pages
        )
    )

    # -----------------------------------------------------
    # 文書情報作成
    # -----------------------------------------------------

    info_lines = [
        "文書情報",
        f"ファイル名: {filename}",
        f"ファイル形式: {extension}",
    ]

    if metadata_title:
        info_lines.append(
            f"文書タイトル: {metadata_title}"
        )

    if title_candidates:
        info_lines.append(
            "タイトル候補:"
        )

        info_lines.extend(
            title_candidates
        )

    if beginning:
        info_lines.append(
            "文書の冒頭:"
        )

        info_lines.append(
            beginning
        )

    return clean_text(
        "\n".join(
            info_lines
        )
    )