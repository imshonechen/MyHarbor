from __future__ import annotations

import json
import ipaddress
import re
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import urljoin, urlparse

import httpx

_SIZE_RE = re.compile(r"^(\d+)[xX](\d+)$")
_SVG_SCORE = 1_000_000_000
_MAX_HTML_BYTES = 512 * 1024
_MAX_MANIFEST_BYTES = 256 * 1024
_MAX_ICON_BYTES = 256 * 1024
_MIN_SQUARE_RATIO = 0.85

_ICON_REL_EXTRA_TOKENS = {
    "apple-touch-icon",
    "apple-touch-icon-precomposed",
    "mask-icon",
    "fluid-icon",
}


@dataclass(frozen=True)
class IconCandidate:
    url: str
    score: int
    width: int | None = None
    height: int | None = None


def _is_http_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _should_verify_ssl(url: str) -> bool:
    parsed = urlparse(url)
    hostname = parsed.hostname
    if parsed.scheme != "https" or not hostname:
        return True

    try:
        ip = ipaddress.ip_address(hostname)
    except ValueError:
        return True

    return ip.is_global


def parse_icon_sizes(value: str | None) -> int:
    score, _ = parse_icon_sizes_and_dimensions(value)
    return score


def _is_squareish(width: int, height: int) -> bool:
    if width <= 0 or height <= 0:
        return False
    ratio = min(width, height) / max(width, height)
    return ratio >= _MIN_SQUARE_RATIO


def parse_icon_sizes_and_dimensions(value: str | None) -> tuple[int, tuple[int, int] | None]:
    if not value:
        return 0, None
    raw = value.strip().lower()
    if not raw:
        return 0, None
    if raw == "any":
        return _SVG_SCORE, None

    best_score = 0
    best_dimensions: tuple[int, int] | None = None
    for token in raw.split():
        match = _SIZE_RE.fullmatch(token)
        if not match:
            continue
        width = int(match.group(1))
        height = int(match.group(2))
        if not _is_squareish(width, height):
            continue
        score = width * height
        if score > best_score:
            best_score = score
            best_dimensions = (width, height)
    return best_score, best_dimensions


class _IconHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.icon_links: list[tuple[str, int, tuple[int, int] | None]] = []
        self.manifest_links: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "link":
            return
        attr_map: dict[str, str] = {}
        for key, value in attrs:
            if not key or value is None:
                continue
            attr_map[key.lower()] = value

        href = attr_map.get("href")
        if not href:
            return

        rel_raw = attr_map.get("rel", "")
        rel_tokens = {token for token in re.split(r"\s+", rel_raw.strip().lower()) if token}
        if not rel_tokens:
            return

        if "manifest" in rel_tokens:
            self.manifest_links.append(href)
            return

        if "icon" in rel_tokens or rel_tokens & _ICON_REL_EXTRA_TOKENS:
            score, dimensions = parse_icon_sizes_and_dimensions(attr_map.get("sizes"))
            if score == 0 and href.lower().endswith(".svg"):
                score = _SVG_SCORE
            self.icon_links.append((href, score, dimensions))


def _dedupe_candidates(candidates: Iterable[IconCandidate]) -> list[IconCandidate]:
    best_by_url: dict[str, IconCandidate] = {}
    for item in candidates:
        current = best_by_url.get(item.url)
        if current is None or item.score > current.score:
            best_by_url[item.url] = item
            continue
        if item.score == current.score and current.width is None and item.width is not None:
            best_by_url[item.url] = item
    return list(best_by_url.values())


def extract_icon_candidates_from_html(html: str, page_url: str) -> tuple[list[IconCandidate], list[str]]:
    parser = _IconHtmlParser()
    parser.feed(html)

    icons: list[IconCandidate] = []
    for href, score, dimensions in parser.icon_links:
        url = urljoin(page_url, href)
        if not _is_http_url(url):
            continue
        if score == 0 and url.lower().endswith(".svg"):
            score = _SVG_SCORE
        width, height = dimensions if dimensions else (None, None)
        icons.append(IconCandidate(url=url, score=score, width=width, height=height))

    manifests: list[str] = []
    for href in parser.manifest_links:
        url = urljoin(page_url, href)
        if _is_http_url(url):
            manifests.append(url)

    return _dedupe_candidates(icons), manifests


def extract_icon_candidates_from_manifest(manifest: object, manifest_url: str) -> list[IconCandidate]:
    if not isinstance(manifest, dict):
        return []

    icons = manifest.get("icons")
    if not isinstance(icons, list):
        return []

    results: list[IconCandidate] = []
    for item in icons:
        if not isinstance(item, dict):
            continue
        src = item.get("src")
        if not isinstance(src, str) or not src.strip():
            continue

        url = urljoin(manifest_url, src)
        if not _is_http_url(url):
            continue

        sizes = item.get("sizes") if isinstance(item.get("sizes"), str) else None
        score, dimensions = parse_icon_sizes_and_dimensions(sizes)
        if score == 0 and url.lower().endswith(".svg"):
            score = _SVG_SCORE
        width, height = dimensions if dimensions else (None, None)
        results.append(IconCandidate(url=url, score=score, width=width, height=height))

    return _dedupe_candidates(results)


def select_best_icon_url(candidates: Iterable[IconCandidate]) -> str | None:
    deduped = _dedupe_candidates(candidates)
    if not deduped:
        return None
    deduped.sort(key=lambda item: (-item.score, item.url))
    return deduped[0].url


def _read_limited_bytes(response: httpx.Response, limit: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    for chunk in response.iter_bytes():
        if not chunk:
            continue
        chunks.append(chunk)
        total += len(chunk)
        if total >= limit:
            break
    return b"".join(chunks)


def _decode_response_bytes(response: httpx.Response, raw: bytes) -> str:
    encoding = response.encoding or "utf-8"
    try:
        return raw.decode(encoding, errors="ignore")
    except LookupError:
        return raw.decode("utf-8", errors="ignore")


def _looks_like_html(content_type: str, url: str) -> bool:
    ct = (content_type or "").lower()
    if not ct:
        return True
    if "text/html" in ct or "application/xhtml+xml" in ct:
        return True
    if ct.startswith("text/") and url.lower().endswith(("/", ".html", ".htm")):
        return True
    return False


def _looks_like_image(content_type: str, url: str) -> bool:
    ct = (content_type or "").lower()
    if ct.startswith("image/"):
        return True
    if "icon" in ct or "svg" in ct:
        return True
    if not ct or "octet-stream" in ct:
        lowered = url.lower()
        return lowered.endswith((".ico", ".png", ".jpg", ".jpeg", ".svg", ".webp"))
    return False


def _extract_png_dimensions(raw: bytes) -> tuple[int, int] | None:
    if len(raw) < 24:
        return None
    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    if raw[12:16] != b"IHDR":
        return None
    width = int.from_bytes(raw[16:20], "big")
    height = int.from_bytes(raw[20:24], "big")
    if width <= 0 or height <= 0:
        return None
    return width, height


def _extract_ico_dimensions(raw: bytes) -> tuple[int, int] | None:
    if len(raw) < 6:
        return None
    reserved = int.from_bytes(raw[0:2], "little")
    icon_type = int.from_bytes(raw[2:4], "little")
    count = int.from_bytes(raw[4:6], "little")
    if reserved != 0 or icon_type != 1 or count <= 0:
        return None

    best: tuple[int, int] | None = None
    best_area = 0
    offset = 6
    for _ in range(min(count, 16)):
        if len(raw) < offset + 16:
            break
        width = raw[offset] or 256
        height = raw[offset + 1] or 256
        area = width * height
        if area > best_area:
            best_area = area
            best = (width, height)
        offset += 16
    return best


_SVG_VIEWBOX_RE = re.compile(
    r"""\bviewBox\s*=\s*["']\s*[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?[,\s]+[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?[,\s]+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)[,\s]+([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*["']""",
    re.IGNORECASE,
)
_SVG_DIM_RE = re.compile(r"""\b(width|height)\s*=\s*["']\s*([^"']+)\s*["']""", re.IGNORECASE)
_SVG_TAG_RE = re.compile(r"""<svg\b[^>]*>""", re.IGNORECASE)


def _parse_svg_length(value: str) -> float | None:
    raw = value.strip().lower()
    if not raw or raw.endswith("%"):
        return None
    match = re.match(r"^([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)([a-z]*)$", raw)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _extract_svg_dimensions(svg: str) -> tuple[int, int] | None:
    svg_tag_match = _SVG_TAG_RE.search(svg[:8192])
    svg_tag = svg_tag_match.group(0) if svg_tag_match else ""

    width_value: float | None = None
    height_value: float | None = None

    for key, value in _SVG_DIM_RE.findall(svg_tag):
        length = _parse_svg_length(value)
        if length is None or length <= 0:
            continue
        if key.lower() == "width" and width_value is None:
            width_value = length
        if key.lower() == "height" and height_value is None:
            height_value = length

    if width_value is None or height_value is None:
        viewbox = _SVG_VIEWBOX_RE.search(svg_tag)
        if viewbox:
            try:
                vb_width = float(viewbox.group(1))
                vb_height = float(viewbox.group(2))
            except ValueError:
                vb_width = 0
                vb_height = 0
            if vb_width > 0 and vb_height > 0:
                width_value = width_value or vb_width
                height_value = height_value or vb_height

    if width_value is None or height_value is None:
        return None

    width_int = int(round(width_value))
    height_int = int(round(height_value))
    if width_int <= 0 or height_int <= 0:
        return None
    return width_int, height_int


def _fetch_icon_dimensions(client: httpx.Client, icon_url: str) -> tuple[int, int] | None:
    try:
        with client.stream("GET", icon_url) as response:
            if response.status_code >= 400:
                return None
            content_type = response.headers.get("content-type", "")
            raw = _read_limited_bytes(response, _MAX_ICON_BYTES)
            url_str = str(response.url)
    except httpx.RequestError:
        return None

    lowered_url = url_str.lower()
    ct = (content_type or "").lower()
    if not _looks_like_image(content_type, url_str) and not lowered_url.endswith((".svg", ".png", ".ico")):
        return None

    if "svg" in ct or lowered_url.endswith(".svg"):
        text = raw.decode("utf-8", errors="ignore")
        return _extract_svg_dimensions(text)

    if "png" in ct or lowered_url.endswith(".png"):
        return _extract_png_dimensions(raw)

    if "icon" in ct or lowered_url.endswith(".ico"):
        return _extract_ico_dimensions(raw)

    return None


def _fetch_html(client: httpx.Client, page_url: str) -> str | None:
    try:
        with client.stream("GET", page_url) as response:
            if response.status_code >= 400:
                return None
            content_type = response.headers.get("content-type", "")
            if not _looks_like_html(content_type, str(response.url)):
                return None
            raw = _read_limited_bytes(response, _MAX_HTML_BYTES)
            return _decode_response_bytes(response, raw)
    except httpx.RequestError:
        return None


def _fetch_manifest(client: httpx.Client, manifest_url: str) -> object | None:
    try:
        with client.stream("GET", manifest_url) as response:
            if response.status_code >= 400:
                return None
            raw = _read_limited_bytes(response, _MAX_MANIFEST_BYTES)
            text = _decode_response_bytes(response, raw)
    except httpx.RequestError:
        return None

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def _favicon_is_squareish(client: httpx.Client, favicon_url: str) -> bool:
    dims = _fetch_icon_dimensions(client, favicon_url)
    if dims is None:
        return False
    return _is_squareish(dims[0], dims[1])


def fetch_site_logo_url(site_url: str, timeout_seconds: float = 5.0) -> str | None:
    timeout = httpx.Timeout(timeout_seconds, connect=timeout_seconds)
    headers = {"User-Agent": "MyHarbor (+https://github.com/imshonechen/MyHarbor)"}
    verify_ssl = _should_verify_ssl(site_url)

    with httpx.Client(timeout=timeout, follow_redirects=True, headers=headers, verify=verify_ssl) as client:
        html = _fetch_html(client, site_url)
        candidates: list[IconCandidate] = []

        if html:
            icon_candidates, manifest_urls = extract_icon_candidates_from_html(html, site_url)
            candidates.extend(icon_candidates)

            for manifest_url in manifest_urls[:2]:
                manifest = _fetch_manifest(client, manifest_url)
                candidates.extend(extract_icon_candidates_from_manifest(manifest, manifest_url))

        deduped = _dedupe_candidates(candidates)
        deduped.sort(key=lambda item: (-item.score, item.url))
        checked = 0
        for candidate in deduped:
            if candidate.width is not None and candidate.height is not None:
                if _is_squareish(candidate.width, candidate.height):
                    return candidate.url
                continue

            if checked >= 10:
                continue
            checked += 1
            dims = _fetch_icon_dimensions(client, candidate.url)
            if dims and _is_squareish(dims[0], dims[1]):
                return candidate.url

        favicon_url = urljoin(_origin(site_url) + "/", "favicon.ico")
        if _favicon_is_squareish(client, favicon_url):
            return favicon_url

    return None
