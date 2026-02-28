from __future__ import annotations

import bleach

_ALLOWED_TAGS = [
    "a",
    "b",
    "br",
    "em",
    "img",
    "i",
    "small",
    "span",
    "strong",
]

_ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
    "img": ["src", "alt", "title", "width", "height"],
}

_ALLOWED_PROTOCOLS = [
    "http",
    "https",
    "mailto",
]


def sanitize_footer_html(value: str) -> str:
    return bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
    )


def sanitize_copyright_html(value: str) -> str:
    return sanitize_footer_html(value)


def sanitize_icp_number_html(value: str) -> str:
    return sanitize_footer_html(value)
