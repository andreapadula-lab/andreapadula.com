#!/usr/bin/env python3
"""Build standalone essays from the Medium-ready Markdown source."""

from __future__ import annotations

import argparse
import html
import json
import math
from datetime import date
from pathlib import Path

from build_ai_series import (
    AUTHOR_ID,
    AUTHOR_IMAGE_URL,
    SITE_URL,
    read_draft,
    shared_footer,
    shared_nav,
    title_key,
)


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts", type=Path, default=root.parent / "medium")
    parser.add_argument("--site", type=Path, default=root)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path(__file__).with_name("standalone-articles.json"),
    )
    return parser.parse_args()


def json_ld(article: dict, word_count: int) -> str:
    url = f"{SITE_URL}/{article['slug']}.html"
    image_url = f"{SITE_URL}/assets/articles/{article['slug']}.png"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "@id": f"{url}#article",
                "headline": article["title"],
                "description": article["description"],
                "datePublished": article["published"],
                "dateModified": article["published"],
                "inLanguage": "en",
                "wordCount": word_count,
                "image": {
                    "@type": "ImageObject",
                    "url": image_url,
                    "width": 1200,
                    "height": 630,
                },
                "author": {"@id": AUTHOR_ID},
                "publisher": {"@id": AUTHOR_ID},
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "about": [
                    {"@type": "Thing", "name": topic}
                    for topic in article["schema_about"]
                ],
                "genre": article["editorial_type"],
                "keywords": article["keywords"],
            },
            {
                "@type": "Person",
                "@id": AUTHOR_ID,
                "name": "Andrea Padula",
                "url": f"{SITE_URL}/about.html",
                "image": AUTHOR_IMAGE_URL,
                "jobTitle": "Head of Partnerships & Business Development",
                "worksFor": {
                    "@type": "Organization",
                    "name": "Streetbeat",
                    "url": "https://streetbeat.com",
                },
                "sameAs": [
                    "https://www.linkedin.com/in/andreapadula/",
                    "https://medium.com/@padula.andrea",
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": 1,
                        "name": "Home",
                        "item": f"{SITE_URL}/",
                    },
                    {
                        "@type": "ListItem",
                        "position": 2,
                        "name": "Vision",
                        "item": f"{SITE_URL}/vision.html",
                    },
                    {
                        "@type": "ListItem",
                        "position": 3,
                        "name": article["title"],
                        "item": url,
                    },
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=8)


def render_related(article: dict) -> str:
    rows = []
    for related in article["related"]:
        rows.append(
            f'''            <a class="related-link" href="{html.escape(related['slug'])}.html">
                <span>{html.escape(related['title'])}</span><span aria-hidden="true">→</span>
            </a>'''
        )
    return "\n".join(rows)


def render_article(
    article: dict,
    subtitle: str,
    body_html: str,
    word_count: int,
) -> str:
    title = html.escape(article["title"])
    description = html.escape(article["description"], quote=True)
    published = article["published"]
    visible_date = date.fromisoformat(published).strftime("%B %d, %Y").replace(" 0", " ")
    reading_time = max(1, math.ceil(word_count / 220))
    url = f"{SITE_URL}/{article['slug']}.html"
    image_url = f"{SITE_URL}/assets/articles/{article['slug']}.png"
    tags = "\n".join(
        f'    <meta property="article:tag" content="{html.escape(keyword, quote=True)}">'
        for keyword in article["keywords"]
    )
    related = render_related(article)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Andrea Padula</title>
    <meta name="description" content="{description}">
    <meta name="author" content="Andrea Padula">
    <meta name="keywords" content="{html.escape(', '.join(article['keywords']), quote=True)}">
    <link rel="canonical" href="{url}">
    <meta property="og:site_name" content="Andrea Padula">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{image_url}">
    <meta property="og:image:alt" content="{title} — Andrea Padula">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="{url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{published}">
    <meta property="article:modified_time" content="{published}">
    <meta property="article:author" content="{SITE_URL}/about.html">
    <meta property="article:section" content="{html.escape(article['section'], quote=True)}">
{tags}
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{image_url}">
    <script type="application/ld+json">
{json_ld(article, word_count)}
    </script>
    <link rel="stylesheet" href="assets/site.css">
    <link rel="stylesheet" href="assets/article.css">
</head>
<body class="long-horizon-essay">
<a class="skip-link" href="#main">Skip to content</a>
<div class="progress-bar" id="progressBar"></div>
{shared_nav("writing")}

<main id="main" tabindex="-1">
<header class="article-hero">
    <div class="hero-inner">
        <div class="eyebrow">{html.escape(article['eyebrow'])}</div>
        <h1>{title}</h1>
        <p class="hero-subtitle">{html.escape(subtitle)}</p>
        <div class="article-meta">
            <a href="about.html" rel="author">Andrea Padula</a>
            <time class="meta-dot" datetime="{published}">{visible_date}</time>
            <span class="meta-dot">{reading_time} min read</span>
        </div>
    </div>
</header>

    <div class="article-shell">
        <article class="article-body">
{body_html}
        </article>
        <aside class="article-aside" aria-label="About this essay">
            <div class="aside-card">
                <div class="aside-label">{html.escape(article['aside_label'])}</div>
                <p>{html.escape(article['aside_copy'])}</p>
                <a href="vision.html">Explore the vision →</a>
            </div>
        </aside>
    </div>

    <section class="related-section" aria-labelledby="related-heading">
        <div class="section-kicker" id="related-heading">Continue reading</div>
        <div class="related-links">
{related}
        </div>
    </section>

    <section class="author-box" aria-label="About the author">
        <div class="author-inner">
            <div class="author-copy">
                <h2><a href="about.html">Andrea Padula</a></h2>
                <p>Head of Partnerships &amp; Business Development at Streetbeat. Writing from Milan about AI, technology, choices, and the inner life.</p>
                <p class="disclosure">Andrea leads Partnerships &amp; BD at Streetbeat; views are personal.</p>
            </div>
        </div>
    </section>
</main>

{shared_footer("writing")}
<script src="assets/article.js" defer></script>
<script src="assets/site.js" defer></script>
</body>
</html>
'''


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    for article in manifest["articles"]:
        draft_path = args.drafts / article["draft"]
        draft_title, subtitle, body_html, word_count = read_draft(draft_path)
        if title_key(draft_title) != title_key(article["title"]):
            raise ValueError(
                f"Title mismatch in {draft_path}: {draft_title!r} != {article['title']!r}"
            )
        if not subtitle:
            raise ValueError(f"Missing italic subtitle in {draft_path}")
        if word_count < 1000:
            raise ValueError(f"Draft is unexpectedly short ({word_count} words): {draft_path}")

        output_path = args.site / f"{article['slug']}.html"
        output_path.write_text(
            render_article(article, subtitle, body_html, word_count),
            encoding="utf-8",
        )
        print(f"Built {output_path.name} ({word_count} words)")


if __name__ == "__main__":
    main()
