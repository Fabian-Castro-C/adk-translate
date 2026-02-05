from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommentLine:
    prefix: str
    payload: str
    suffix: str = ""


def _split_full_line_prefix(line: str, marker: str) -> CommentLine | None:
    stripped = line.lstrip()
    if not stripped.startswith(marker):
        return None
    indent_len = len(line) - len(stripped)
    prefix = line[:indent_len] + marker
    payload = stripped[len(marker) :]
    return CommentLine(prefix=prefix, payload=payload)


def extract_comment_line(line: str, fence_lang: str | None) -> CommentLine | None:
    lang = (fence_lang or "").lower()

    # Conservative: only full-line comments.
    if lang in ("py", "python"):
        return _split_full_line_prefix(line, "#")

    if lang in ("js", "javascript", "ts", "typescript", "go", "java", "c", "cpp", "c++"):
        cl = _split_full_line_prefix(line, "//")
        if cl:
            return cl

        cl = _split_full_line_prefix(line, "/*")
        if cl:
            # Handle closing */ on same line
            payload = cl.payload
            if "*/" in payload:
                before, after = payload.split("*/", 1)
                return CommentLine(prefix=cl.prefix, payload=before, suffix="*/" + after)
            return CommentLine(prefix=cl.prefix, payload=payload)

        # common block interior: leading '*'
        cl = _split_full_line_prefix(line, "*")
        if cl:
            return cl

    # Fallback for unknown language: do nothing
    return None


def replace_comment_payload(line: str, comment: CommentLine, new_payload: str) -> str:
    # Preserve original whitespace around payload.
    # Keep exact prefix & suffix.
    return f"{comment.prefix}{new_payload}{comment.suffix}" + ("\n" if line.endswith("\n") else "")
