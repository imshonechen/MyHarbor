from __future__ import annotations

import bleach

_ALLOWED_TAGS = [
    "a",
    "b",
    "br",
    "em",
    "i",
    "small",
    "span",
    "strong",
]

_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}

_ALLOWED_PROTOCOLS = [
    "http",
    "https",
    "mailto",
]


def sanitize_copyright_html(value: str) -> str:
    return bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )

