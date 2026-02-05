from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


SegmentKind = Literal["frontmatter", "text", "code_fence"]


@dataclass(frozen=True)
class Segment:
    kind: SegmentKind
    text: str
    fence_marker: str | None = None
    fence_lang: str | None = None


def split_markdown(md: str) -> list[Segment]:
    lines = md.splitlines(keepends=True)
    segments: list[Segment] = []

    i = 0

    # YAML frontmatter (very common in docs): preserve by default
    if lines and lines[0].strip() == "---":
        fm = [lines[0]]
        i = 1
        while i < len(lines):
            fm.append(lines[i])
            if lines[i].strip() in ("---", "..."):
                i += 1
                break
            i += 1
        segments.append(Segment(kind="frontmatter", text="".join(fm)))

    def flush_text(buf: list[str]) -> None:
        if buf:
            segments.append(Segment(kind="text", text="".join(buf)))
            buf.clear()

    text_buf: list[str] = []

    while i < len(lines):
        line = lines[i]

        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            flush_text(text_buf)

            fence_marker = stripped[:3]
            fence_lang = stripped[3:].strip() or None

            fence_lines = [line]
            i += 1
            while i < len(lines):
                fence_lines.append(lines[i])
                if lines[i].lstrip().startswith(fence_marker):
                    i += 1
                    break
                i += 1

            segments.append(
                Segment(
                    kind="code_fence",
                    text="".join(fence_lines),
                    fence_marker=fence_marker,
                    fence_lang=fence_lang,
                )
            )
            continue

        text_buf.append(line)
        i += 1

    flush_text(text_buf)
    return segments


def join_segments(segments: list[Segment]) -> str:
    return "".join(s.text for s in segments)
