from __future__ import annotations

import re
from dataclasses import dataclass


_PLACEHOLDER_FMT = "<<ADK_P{n}>>"


@dataclass(frozen=True)
class ProtectedText:
    text: str
    mapping: dict[str, str]


_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")

# Markdown links/images: keep URL part intact
_MD_LINK_URL_RE = re.compile(r"\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")

# Autolinks like <https://...>
_AUTO_LINK_RE = re.compile(r"<https?://[^>]+>")

# Bare URLs
_BARE_URL_RE = re.compile(r"https?://[^\s)\]]+")


def protect_markdown_inline(text: str) -> ProtectedText:
    mapping: dict[str, str] = {}
    counter = 0

    def make_placeholder(value: str) -> str:
        nonlocal counter
        key = _PLACEHOLDER_FMT.format(n=counter)
        counter += 1
        mapping[key] = value
        return key

    # Order matters: protect inline code first, then urls
    def sub_all(pattern: re.Pattern[str], s: str) -> str:
        return pattern.sub(lambda m: make_placeholder(m.group(0)), s)

    protected = text
    protected = sub_all(_INLINE_CODE_RE, protected)

    # Protect just URL portion in markdown links: we replace the URL inside (...)
    def link_url_sub(m: re.Match[str]) -> str:
        url = m.group(1)
        ph = make_placeholder(url)
        return m.group(0).replace(url, ph)

    protected = _MD_LINK_URL_RE.sub(link_url_sub, protected)

    protected = sub_all(_AUTO_LINK_RE, protected)
    protected = sub_all(_BARE_URL_RE, protected)

    return ProtectedText(text=protected, mapping=mapping)


def unprotect(text: str, mapping: dict[str, str]) -> str:
    # Restore in reverse insertion order to avoid accidental partial matches
    for key in sorted(mapping.keys(), key=len, reverse=True):
        text = text.replace(key, mapping[key])
    return text
