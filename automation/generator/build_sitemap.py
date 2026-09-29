"""
Build sitemap.xml from site pages and generated articles.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SITE_URL = "https://www.staxtech.in"
OUTPUT = ROOT / "sitemap.xml"


def public_url(relative: Path) -> str:
    return SITE_URL.rstrip("/") + "/" + str(relative).replace("\\", "/")


def collect() -> list[str]:
    urls = set()

    for path in ROOT.glob("*.html"):
        urls.add(public_url(path.relative_to(ROOT)))

    articles = ROOT / "articles"
    if articles.exists():
        for path in articles.glob("*.html"):
            urls.add(public_url(path.relative_to(ROOT)))

    return sorted(urls)


def main() -> None:
    urls = collect()
    today = datetime.now(timezone.utc).date().isoformat()

    entries = []
    for url in urls:
        entries.append(
            "  <url>\n"
            f"    <loc>{html.escape(url, quote=True)}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            "  </url>"
        )

    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(entries)
        + '\n</urlset>\n'
    )

    OUTPUT.write_text(sitemap, encoding="utf-8")
    print(f"Generated sitemap with {len(urls)} URLs.")


if __name__ == "__main__":
    main()
