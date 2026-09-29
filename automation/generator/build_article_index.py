"""
Build a lightweight /articles/ index from generated article metadata.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARTICLES = ROOT / "articles"
SITE_URL = "https://www.staxtech.in"


def main() -> None:
    items = []

    for meta in ARTICLES.glob("*.json"):
        try:
            data = json.loads(meta.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        items.append(data)

    items.sort(key=lambda x: x.get("published", ""), reverse=True)

    cards = []

    for item in items:
        title = html.escape(item.get("title", "StaxTech Article"))
        description = html.escape(item.get("description", ""))
        url = html.escape(
            "/" + item.get("url", "").split("/articles/")[-1],
            quote=True
        )
        date = html.escape(item.get("published", ""))

        cards.append(
            f'<article class="stx-card"><h2><a href="{url}">{title}</a></h2>'
            f'<p>{description}</p><small>{date}</small></article>'
        )

    body = "\n".join(cards) or "<p>New technology guides are coming soon.</p>"

    page = f"""<!doctype html>
<html lang="en-IN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>StaxTech Technology Guides</title>
<meta name="description" content="Practical technology, software, AI and web development guides from StaxTech.">
<link rel="canonical" href="{SITE_URL}/articles/">\n<link rel="stylesheet" href="/assets/article.css">\n<script async src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-9005733002223091" crossorigin="anonymous"></script>
</head>
<body>
<main>
<h1>StaxTech Technology Guides</h1>
<p>Practical guides covering AI, software, web development and student technology.</p>
{body}
</main>
</body>
</html>
"""

    ARTICLES.mkdir(parents=True, exist_ok=True)
    (ARTICLES / "index.html").write_text(page, encoding="utf-8")
    print(f"Built article index with {len(items)} articles.")


if __name__ == "__main__":
    main()
