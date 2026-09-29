"""Build the production /articles/ index from generated metadata."""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLES = ROOT / "articles"
SITE_URL = "https://www.staxtech.in"
ADSENSE_CLIENT = "ca-pub-9005733002223091"


def main() -> None:
    items = []
    for meta in ARTICLES.glob("*.json"):
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if data.get("slug") and data.get("title"):
            items.append(data)

    items.sort(key=lambda item: item.get("published", ""), reverse=True)

    cards = []
    for item in items:
        title = html.escape(item["title"])
        description = html.escape(item.get("description", ""))
        slug = html.escape(item["slug"], quote=True)
        date = html.escape(item.get("published", ""))
        category = html.escape(item.get("category", "Technology"))
        cards.append(
            f'<article class="stx-card">'
            f'<p class="stx-kicker">{category}</p>'
            f'<h2><a href="/articles/{slug}.html">{title}</a></h2>'
            f'<p>{description}</p>'
            f'<p class="stx-meta">{date}</p>'
            f'</article>'
        )

    body = (
        '<div class="stx-grid">' + "".join(cards) + "</div>"
        if cards
        else '<div class="stx-card"><p>No published guides yet. The next eligible technology trend will appear here automatically.</p></div>'
    )

    page = f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StaxTech Technology Guides</title>
<meta name="description" content="Practical technology, software, AI and web development guides from StaxTech.">
<link rel="canonical" href="{SITE_URL}/articles/">
<link rel="stylesheet" href="/assets/article.css">
<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client={ADSENSE_CLIENT}" crossorigin="anonymous"></script>
</head>
<body class="stx-shell">
<header class="stx-nav">
  <div class="stx-nav-inner">
    <a class="stx-brand" href="/">StaxTech</a>
    <nav><a href="/">Home</a><a href="/articles/">Guides</a></nav>
  </div>
</header>
<main class="stx-container">
  <section class="stx-article">
    <p class="stx-kicker">StaxTech Guides</p>
    <h1>Technology Guides</h1>
    <p>Practical guides covering AI, software, web development and student technology.</p>
    {body}
  </section>
</main>
<footer class="stx-footer">© <span data-stx-year></span> StaxTech</footer>
<script src="/assets/article.js" defer></script>
</body>
</html>
"""
    ARTICLES.mkdir(parents=True, exist_ok=True)
    (ARTICLES / "index.html").write_text(page, encoding="utf-8")
    print(f"Built article index with {len(items)} articles.")


if __name__ == "__main__":
    main()
