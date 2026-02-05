from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from .pipeline import TranslateOptions, translate_file, translate_many


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="translate",
        description="Traductor Markdown EN→ES usando Google ADK (preserva código).",
    )

    sub = p.add_subparsers(dest="cmd", required=True)

    p_file = sub.add_parser("file", help="Traduce un archivo")
    p_file.add_argument("--in", dest="in_path", required=True)
    p_file.add_argument("--out", dest="out_path", required=True)
    p_file.add_argument("--overwrite", action="store_true")
    p_file.add_argument("--provider", choices=["gemini", "openai", "anthropic", "github", "copilot-sdk"], default=None, help="LLM provider (default: gemini)")
    p_file.add_argument("--model", default="gemini-2.5-flash", help="Model name (default: gemini-2.5-flash)")

    p_batch = sub.add_parser("batch", help="Traduce múltiples archivos en paralelo")
    p_batch.add_argument("--paths", nargs="+", required=True)
    p_batch.add_argument("--root", required=False)
    p_batch.add_argument("--out-dir", required=True)
    p_batch.add_argument("--jobs", type=int, default=4)
    p_batch.add_argument("--overwrite", action="store_true")
    p_batch.add_argument("--fail-fast", action="store_true")
    p_batch.add_argument("--provider", choices=["gemini", "openai", "anthropic", "github", "copilot-sdk"], default=None, help="LLM provider (default: gemini)")
    p_batch.add_argument("--model", default="gemini-2.5-flash", help="Model name (default: gemini-2.5-flash)")

    return p


async def _run(args: argparse.Namespace) -> int:
    if args.cmd == "file":
        options = TranslateOptions(
            overwrite=args.overwrite,
            jobs=1,
            model=args.model,
            provider=args.provider,
        )
        await translate_file(
            Path(args.in_path),
            Path(args.out_path),
            options=options,
        )
        return 0

    if args.cmd == "batch":
        options = TranslateOptions(
            translate_code_comments=args.translate_code_comments,
            model=args.model,
            provider=args.provider,
            overwrite=args.overwrite,
            jobs=args.jobs,
        )
        root = Path(args.root) if args.root else None
        out_dir = Path(args.out_dir)
        inputs = [Path(p) for p in args.paths]

        results = await translate_many(
            inputs,
            root=root,
            out_dir=out_dir,
            options=options,
            continue_on_error=not args.fail_fast,
        )

        ok = sum(1 for v in results.values() if v == "ok")
        err = sum(1 for v in results.values() if v != "ok")
        print(f"Done. ok={ok} error={err}")
        for k, v in results.items():
            if v != "ok":
                print(f"- {k}: {v}")
        return 0 if err == 0 else 2

    return 2


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    return asyncio.run(_run(args))
