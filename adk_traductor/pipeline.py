from __future__ import annotations

import asyncio
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .adk_translate import AdkTranslateConfig, AdkTranslator


class Translator(Protocol):
    async def translate_text(self, text: str) -> str: ...


@dataclass(frozen=True)
class TranslateOptions:
    overwrite: bool = False
    jobs: int = 4
    model: str = "gemini-2.5-flash"
    provider: str | None = None


def _create_translator(options: TranslateOptions) -> Translator:
    """Factory para crear translator - todos usan AdkTranslator ahora."""
    return AdkTranslator(
        AdkTranslateConfig(
            model=options.model,
            provider=options.provider,
        )
    )


async def translate_file(input_path: Path, output_path: Path, *, options: TranslateOptions) -> None:
    if output_path.exists() and not options.overwrite:
        raise FileExistsError(f"Output exists: {output_path}")
    md = input_path.read_text(encoding="utf-8")
    translator = _create_translator(options)
    translated = await translator.translate_text(md)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(translated, encoding="utf-8")


async def translate_many(inputs: list[Path], *, root: Path | None, out_dir: Path, options: TranslateOptions, continue_on_error: bool = True) -> dict[str, str]:
    semaphore = asyncio.Semaphore(max(1, options.jobs))
    results: dict[str, str] = {}
    async def run_one(p: Path) -> None:
        async with semaphore:
            try:
                rel = p if root is None else p.relative_to(root)
                await translate_file(p, out_dir / rel, options=options)
                results[str(p)] = "ok"
            except Exception as e:
                results[str(p)] = f"error: {e}"
                if not continue_on_error:
                    raise
    await asyncio.gather(*[run_one(p) for p in inputs], return_exceptions=continue_on_error)
    return results
