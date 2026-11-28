#RAG用のテキスト分割処理
import re

CHUNK_MIN = 300      
CHUNK_TARGET = 600   
CHUNK_MAX = 800      
OVERLAP = 100        

NEW_ITEM = re.compile(r"^([・･●○◆◇■□▶►▼※＊*•#\-]|\d+[.．)）\s]|[①-⑳])")

SENTENCE_END = re.compile(r"[。！？!?：:]$")

# 日本語（かな・漢字・全角記号）どうしの折り返しはスペースを入れずにつなぐ
CJK = re.compile(r"[\u3000-\u30ff\u3400-\u9fff\uf900-\ufaff\uff00-\uffef]")


def _join(prev, line):
    if CJK.match(prev[-1]) and CJK.match(line[0]):
        return prev + line
    return prev + " " + line


def join_wrapped_lines(text):
    lines = []

    for line in text.split("\n"):
        line = line.strip()

        if not line:
            lines.append("")
            continue

        prev = lines[-1] if lines else ""

        if prev and not SENTENCE_END.search(prev) and not NEW_ITEM.match(line):
            lines[-1] = _join(prev, line)
        else:
            lines.append(line)

    return "\n".join(lines)


def split_sentences(text):
    text = join_wrapped_lines(text)
    parts = re.split(r"(?<=[。！？!?])|(?<=\.)\s+|\n+", text)
    return [part.strip() for part in parts if part and part.strip()]


def joined_length(parts):
    return sum(len(part) for part in parts) + max(len(parts) - 1, 0)


def take_overlap(parts):
    result = []
    total = 0

    for part in reversed(parts):
        if total + len(part) > OVERLAP:
            break
        result.insert(0, part)
        total += len(part) + 1

    if not result and parts:
        result = [parts[-1][-OVERLAP:]]

    return result


def split_long(unit):
    step = CHUNK_MAX - OVERLAP
    pieces = []

    for start in range(0, len(unit), step):
        pieces.append(unit[start:start + CHUNK_MAX])
        if start + CHUNK_MAX >= len(unit):
            break

    return pieces


def split_text(text):
    units = split_sentences(text)

    chunks = []
    current = []         
    overlap_count = 0   

    def flush():
        nonlocal current, overlap_count

        if len(current) > overlap_count:
            chunks.append("\n".join(current))
            current = take_overlap(current)
            overlap_count = len(current)

    for unit in units:
        if len(unit) > CHUNK_MAX:
            flush()
            chunks.extend(split_long(unit))
            current, overlap_count = [], 0
            continue

        if joined_length(current + [unit]) > CHUNK_MAX:
            flush()

            if joined_length(current + [unit]) > CHUNK_MAX:
                current, overlap_count = [], 0

        current.append(unit)

        if joined_length(current) >= CHUNK_TARGET:
            flush()

    rest = current[overlap_count:]

    if rest:
        rest_text = "\n".join(rest)

        if (
            chunks
            and len(rest_text) < CHUNK_MIN
            and len(chunks[-1]) + 1 + len(rest_text) <= CHUNK_MAX
        ):
            chunks[-1] += "\n" + rest_text
        else:
            chunks.append("\n".join(current))

    return list(dict.fromkeys(chunk.strip() for chunk in chunks if chunk.strip()))