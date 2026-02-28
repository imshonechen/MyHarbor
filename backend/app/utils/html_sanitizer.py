from __future__ import annotations

import bleach

try:
    from bleach.css_sanitizer import CSSSanitizer
except ImportError:  # pragma: no cover
    CSSSanitizer = None

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
    "img": ["src", "alt", "title", "width", "height", "display", "style"],
}

_ALLOWED_PROTOCOLS = [
    "http",
    "https",
    "mailto",
]

_CSS_SANITIZER = CSSSanitizer(allowed_css_properties=["display"]) if CSSSanitizer else None


def sanitize_footer_html(value: str) -> str:
    return bleach.clean(
        value,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=_ALLOWED_PROTOCOLS,
        strip=True,
        css_sanitizer=_CSS_SANITIZER,
    )


def sanitize_copyright_html(value: str) -> str:
    return sanitize_footer_html(value)


def sanitize_icp_number_html(value: str) -> str:
    return sanitize_footer_html(value)
