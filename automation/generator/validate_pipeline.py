"""Validate the generated StaxTech publishing output before commit."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = [
    ROOT / "articles" / "index.html",
    ROOT / "sitemap.xml",
    ROOT / "robots.txt",
    ROOT / "assets" / "article.css",
    ROOT / "assets" / "article.js",
]


def fail(message: str) -> None:
    print(f"VALIDATION ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> int:
    for path in REQUIRED:
        if not path.exists() or path.stat().st_size == 0:
            fail(f"missing or empty file: {path.relative_to(ROOT)}")

    try:
        candidates = json.loads(
            (ROOT / "automation" / "data" / "topic-candidates.json").read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid topic-candidates.json: {exc}")

    articles = list(ROOT.joinpath("articles").glob("*.json"))
    html_articles = [
        p for p in ROOT.joinpath("articles").glob("*.html")
        if p.name != "index.html"
    ]

    if len(articles) != len(html_articles):
        fail("article metadata/html file count does not match")

    # A run with no suitable trend is allowed to publish nothing, but if an
    # article exists it must pass the complete structural checks below.
    for meta_path in articles:
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(f"invalid article metadata {meta_path.name}: {exc}")

        slug = meta.get("slug")
        if not slug:
            fail(f"missing slug in {meta_path.name}")

        page_path = ROOT / "articles" / f"{slug}.html"
        if not page_path.exists():
            fail(f"metadata points to missing page: {page_path.name}")

        page = page_path.read_text(encoding="utf-8")
        required_markers = (
            "<!doctype html>",
            '<meta name="description"',
            '<link rel="canonical"',
            'rel="stylesheet" href="/assets/article.css"',
            "adsbygoogle.js?client=ca-pub-9005733002223091",
            'type="application/ld+json"',
            '<script src="/assets/article.js" defer></script>',
        )
        for marker in required_markers:
            if marker not in page:
                fail(f"{page_path.name} is missing: {marker}")

    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for page_path in html_articles:
        public_url = f"https://www.staxtech.in/articles/{page_path.name}"
        if public_url not in sitemap:
            fail(f"sitemap missing {public_url}")

    print(
        f"Validation passed: {len(articles)} generated article(s), "
        f"{len(candidates.get('topics', []))} shortlisted topic(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
