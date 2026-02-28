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
    if not value:
        return 0
    raw = value.strip().lower()
    if not raw:
        return 0
    if raw == "any":
        return _SVG_SCORE
    best = 0
    for token in raw.split():
        match = _SIZE_RE.fullmatch(token)
        if not match:
            continue
        width = int(match.group(1))
        height = int(match.group(2))
        best = max(best, width * height)
    return best


class _IconHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.icon_links: list[tuple[str, int]] = []
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
            score = parse_icon_sizes(attr_map.get("sizes"))
            if score == 0 and href.lower().endswith(".svg"):
                score = _SVG_SCORE
            self.icon_links.append((href, score))


def _dedupe_candidates(candidates: Iterable[IconCandidate]) -> list[IconCandidate]:
    best_score_by_url: dict[str, int] = {}
    for item in candidates:
        current = best_score_by_url.get(item.url)
        if current is None or item.score > current:
            best_score_by_url[item.url] = item.score
    return [IconCandidate(url=url, score=score) for url, score in best_score_by_url.items()]


def extract_icon_candidates_from_html(html: str, page_url: str) -> tuple[list[IconCandidate], list[str]]:
    parser = _IconHtmlParser()
    parser.feed(html)

    icons: list[IconCandidate] = []
    for href, score in parser.icon_links:
        url = urljoin(page_url, href)
        if not _is_http_url(url):
            continue
        if score == 0 and url.lower().endswith(".svg"):
            score = _SVG_SCORE
        icons.append(IconCandidate(url=url, score=score))

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
        score = parse_icon_sizes(sizes)
        if score == 0 and url.lower().endswith(".svg"):
            score = _SVG_SCORE
        results.append(IconCandidate(url=url, score=score))

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


def _favicon_exists(client: httpx.Client, favicon_url: str) -> bool:
    try:
        with client.stream("GET", favicon_url) as response:
            if response.status_code != 200:
                return False
            content_type = response.headers.get("content-type", "")
            return _looks_like_image(content_type, str(response.url))
    except httpx.RequestError:
        return False


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

        best = select_best_icon_url(candidates)
        if best:
            return best

        favicon_url = urljoin(_origin(site_url) + "/", "favicon.ico")
        if _favicon_exists(client, favicon_url):
            return favicon_url

    return None
