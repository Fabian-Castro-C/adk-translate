from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .adk_translate import AdkTranslateConfig, AdkTranslator
from .copilot_translate import CopilotTranslateConfig, CopilotTranslator
from .md.comments import extract_comment_line, replace_comment_payload
from .md.protect import protect_markdown_inline, unprotect
from .md.segmenter import Segment, join_segments, split_markdown


class Translator(Protocol):
    """Protocol for translator implementations."""
    async def translate_text(self, text: str) -> str: ...
    async def translate_many_texts(self, texts: list[str], *, jobs: int) -> list[str]: ...


@dataclass(frozen=True)
class TranslateOptions:
    translate_code_comments: bool = False
    overwrite: bool = False
    jobs: int = 4
    model: str = "gemini-2.5-flash"
    provider: str | None = None


async def _translate_text_segment(translator: Translator, text: str) -> str:
    protected = protect_markdown_inline(text)
    translated = await translator.translate_text(protected.text)
    return unprotect(translated, protected.mapping)


async def _translate_code_fence_comments(
    translator: Translator, segment: Segment
) -> Segment:
    lines = segment.text.splitlines(keepends=True)
    if len(lines) < 2:
        return segment

    out_lines = [lines[0]]  # opening fence
    fence_lang = segment.fence_lang

    for line in lines[1:-1]:
        comment = extract_comment_line(line, fence_lang)
        if not comment:
            out_lines.append(line)
            continue

        payload = comment.payload
        if not payload.strip():
            out_lines.append(line)
            continue

        translated_payload = await translator.translate_text(payload)
        out_lines.append(replace_comment_payload(line, comment, translated_payload))

    out_lines.append(lines[-1])  # closing fence

    return Segment(
        kind=segment.kind,
        text="".join(out_lines),
        fence_marker=segment.fence_marker,
        fence_lang=segment.fence_lang,
    )


async def translate_markdown(
    md: str,
    *,
    options: TranslateOptions,
    translator: Translator | None = None,
) -> str:
    if translator is None:
        translator = _create_translator(options)

    segments = split_markdown(md)
    out: list[Segment] = []

    for seg in segments:
        if seg.kind in ("frontmatter",):
            out.append(seg)
            continue

        if seg.kind == "code_fence":
            if options.translate_code_comments:
                out.append(await _translate_code_fence_comments(translator, seg))
            else:
                out.append(seg)
            continue

        if seg.kind == "text":
            out.append(Segment(kind="text", text=await _translate_text_segment(translator, seg.text)))
            continue

        out.append(seg)

    return join_segments(out)


async def translate_file(
    input_path: Path,
    output_path: Path,
    *,
    options: TranslateOptions,
) -> None:
    if output_path.exists() and not options.overwrite:
        raise FileExistsError(f"Output exists: {output_path}")

    md = input_path.read_text(encoding="utf-8")
    translated = await translate_markdown(md, options=options)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(translated, encoding="utf-8")


async def translate_many(
    inputs: list[Path],
    *,
    root: Path | None,
    out_dir: Path,
    options: TranslateOptions,
    continue_on_error: bool = True,
) -> dict[str, str]:
    semaphore = asyncio.Semaphore(max(1, options.jobs))
    results: dict[str, str] = {}

    async def run_one(p: Path) -> None:
        async with semaphore:
            try:
                rel = p
                if root is not None:
                    rel = p.relative_to(root)
                out_path = out_dir / rel
                await translate_file(p, out_path, options=options)
                results[str(p)] = "ok"
            except Exception as e:
                results[str(p)] = f"error: {e}"
                if not continue_on_error:
                    raise

    await asyncio.gather(*(run_one(p) for p in inputs))
    return results
