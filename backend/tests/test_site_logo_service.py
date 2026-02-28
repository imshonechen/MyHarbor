from app.services.site_logo_service import (
    extract_icon_candidates_from_html,
    extract_icon_candidates_from_manifest,
    parse_icon_sizes,
    select_best_icon_url,
)


def test_parse_icon_sizes_prefers_largest_area() -> None:
    assert parse_icon_sizes("16x16 32x32") == 32 * 32


def test_parse_icon_sizes_ignores_non_square_sizes() -> None:
    assert parse_icon_sizes("512x256 180x180") == 180 * 180


def test_extract_icon_candidates_from_html_picks_largest() -> None:
    html = """
    <html>
      <head>
        <link rel="icon" sizes="16x16" href="/icon-16.png" />
        <link rel="icon" sizes="32x32" href="/icon-32.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
      </head>
    </html>
    """

    candidates, manifests = extract_icon_candidates_from_html(html, "https://example.com/")
    assert manifests == []
    assert select_best_icon_url(candidates) == "https://example.com/apple-touch-icon.png"


def test_extract_icon_candidates_from_html_ignores_rectangular_sizes() -> None:
    html = """
    <html>
      <head>
        <link rel="icon" sizes="512x256" href="/rect.png" />
        <link rel="icon" sizes="180x180" href="/square.png" />
      </head>
    </html>
    """

    candidates, manifests = extract_icon_candidates_from_html(html, "https://example.com/")
    assert manifests == []
    assert select_best_icon_url(candidates) == "https://example.com/square.png"


def test_extract_icon_candidates_from_manifest_picks_largest() -> None:
    manifest = {
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192"},
            {"src": "/icon-512.png", "sizes": "512x512"},
        ]
    }

    candidates = extract_icon_candidates_from_manifest(manifest, "https://example.com/manifest.json")
    assert select_best_icon_url(candidates) == "https://example.com/icon-512.png"


def test_extract_icon_candidates_ignores_non_http_urls() -> None:
    html = """
    <link rel="icon" sizes="512x512" href="javascript:alert(1)" />
    <link rel="icon" sizes="512x512" href="data:image/png;base64,AAAA" />
    """

    candidates, manifests = extract_icon_candidates_from_html(html, "https://example.com/")
    assert manifests == []
    assert candidates == []
