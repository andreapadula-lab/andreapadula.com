#!/usr/bin/env python3
"""Build the AI & Financial Services series from Medium-ready Markdown drafts."""

from __future__ import annotations

import argparse
import html
import json
import math
import re
from datetime import date
from pathlib import Path

import markdown


SITE_URL = "https://andreapadula.com"
AUTHOR_ID = f"{SITE_URL}/#person"
AUTHOR_IMAGE_URL = f"{SITE_URL}/andrea-padula.png"

LEGACY_ARTICLES = {
    "the-bank-of-2030": ("The Bank of 2030 Has 10x the Clients and Half the People", "June 2025"),
    "what-i-see-selling-ai-to-european-banks": ("What I See Selling AI to European Banks", "October 2024"),
    "most-ai-products-fail": ("Most AI Products Fail — Not Because of the Tech", "February 2025"),
    "why-banks-keep-buying-ai-they-will-never-use": ("Why Banks Keep Buying AI They’ll Never Use", "March 2025"),
    "the-eu-ai-act-is-a-competitive-advantage": ("The EU AI Act Is a Competitive Advantage", "April 2025"),
    "the-pilot-trap": ("The Pilot Trap", "May 2025"),
}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    default_drafts = root.parent / "medium"
    parser = argparse.ArgumentParser()
    parser.add_argument("--drafts", type=Path, default=default_drafts)
    parser.add_argument("--site", type=Path, default=root)
    parser.add_argument("--manifest", type=Path, default=Path(__file__).with_name("ai-series.json"))
    return parser.parse_args()


def read_draft(path: Path) -> tuple[str, str, str, int]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or not lines[0].startswith("# "):
        raise ValueError(f"Missing H1 in {path}")

    draft_title = lines[0][2:].strip()
    cursor = 1
    while cursor < len(lines) and not lines[cursor].strip():
        cursor += 1

    subtitle = ""
    if cursor < len(lines):
        candidate = lines[cursor].strip()
        if candidate.startswith("*") and candidate.endswith("*") and not candidate.startswith("**"):
            subtitle = candidate[1:-1].strip()
            cursor += 1

    body = "\n".join(lines[cursor:]).strip()
    footer_markers = [
        "\n---\n\n*Originally published",
        "\n---\n\nOriginally published",
    ]
    for marker in footer_markers:
        if marker in body:
            body = body.split(marker, 1)[0].rstrip()
            break

    body_html = markdown.markdown(body, extensions=["sane_lists", "toc"])
    source_match = re.search(r'(<h2 id="sources">Sources</h2>)\s*<ul>(.*?)</ul>', body_html, flags=re.DOTALL)
    if source_match:
        replacement = f'{source_match.group(1)}\n<ul class="source-list">{source_match.group(2)}</ul>'
        body_html = body_html[: source_match.start()] + replacement + body_html[source_match.end() :]
    plain = re.sub(r"https?://\S+", " ", body)
    plain = re.sub(r"[#*_>`\[\]()—–-]", " ", plain)
    word_count = len(re.findall(r"\b[\w’']+\b", plain))
    return draft_title, subtitle, body_html, word_count


def title_key(value: str) -> str:
    value = value.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'")
    value = value.replace('"', "").rstrip(".")
    return re.sub(r"\s+", " ", value).strip().casefold()


def article_lookup(site: Path) -> dict[str, tuple[str, str]]:
    lookup = dict(LEGACY_ARTICLES)
    for manifest_path in sorted((site / "scripts").glob("*-series.json")):
        candidate = json.loads(manifest_path.read_text(encoding="utf-8"))
        published = date.fromisoformat(candidate["published"]).strftime("%B %Y")
        for article in candidate["articles"]:
            slug = article["slug"]
            if slug in lookup:
                raise ValueError(f"Duplicate article slug across manifests: {slug}")
            lookup[slug] = (article["title"], published)
    return lookup


def json_ld_article(article: dict, word_count: int, published: str, series: dict) -> str:
    url = f"{SITE_URL}/{article['slug']}.html"
    article_image = f"{SITE_URL}/assets/articles/{article['slug']}.png"
    series_url = f"{SITE_URL}/{series['slug']}.html"
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BlogPosting",
                "@id": f"{url}#article",
                "headline": article["title"],
                "description": article["description"],
                "datePublished": published,
                "dateModified": published,
                "inLanguage": "en",
                "wordCount": word_count,
                "image": {"@type": "ImageObject", "url": article_image, "width": 1200, "height": 630},
                "author": {"@id": AUTHOR_ID},
                "publisher": {"@id": AUTHOR_ID},
                "mainEntityOfPage": {"@type": "WebPage", "@id": url},
                "isPartOf": {"@type": "CollectionPage", "@id": series_url},
                "about": [{"@type": "Thing", "name": item} for item in series["schema_about"]],
                "keywords": article["keywords"],
            },
            {
                "@type": "Person",
                "@id": AUTHOR_ID,
                "name": "Andrea Padula",
                "url": f"{SITE_URL}/about.html",
                "image": AUTHOR_IMAGE_URL,
                "jobTitle": "Head of Partnerships & Business Development",
                "worksFor": {"@type": "Organization", "name": "Streetbeat", "url": "https://streetbeat.com"},
                "sameAs": [
                    "https://www.linkedin.com/in/andreapadula/",
                    "https://medium.com/@padula.andrea",
                ],
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{SITE_URL}/"},
                    {"@type": "ListItem", "position": 2, "name": series["short_label"], "item": series_url},
                    {"@type": "ListItem", "position": 3, "name": article["title"], "item": url},
                ],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=8)


def render_related(article: dict, lookup: dict[str, tuple[str, str]]) -> str:
    rows = []
    for slug in article["related"]:
        title, _ = lookup[slug]
        rows.append(
            f'''            <a class="related-link" href="{html.escape(slug)}.html">
                <span>{html.escape(title)}</span><span aria-hidden="true">→</span>
            </a>'''
        )
    return "\n".join(rows)


def render_article(
    article: dict,
    index: int,
    total: int,
    subtitle: str,
    body_html: str,
    word_count: int,
    published: str,
    lookup: dict[str, tuple[str, str]],
    series: dict,
) -> str:
    title = html.escape(article["title"])
    description = html.escape(article["description"], quote=True)
    url = f"{SITE_URL}/{article['slug']}.html"
    article_image = f"{SITE_URL}/assets/articles/{article['slug']}.png"
    reading_time = max(1, math.ceil(word_count / 220))
    tags = "\n".join(
        f'    <meta property="article:tag" content="{html.escape(keyword, quote=True)}">'
        for keyword in article["keywords"]
    )
    ld_json = json_ld_article(article, word_count, published, series)
    related = render_related(article, lookup)
    visible_date = date.fromisoformat(published).strftime("%B %d, %Y").replace(" 0", " ")

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
    <meta property="og:image" content="{article_image}">
    <meta property="og:image:alt" content="{title} — Andrea Padula">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="{url}">
    <meta property="og:type" content="article">
    <meta property="article:published_time" content="{published}">
    <meta property="article:modified_time" content="{published}">
    <meta property="article:author" content="{SITE_URL}/about.html">
    <meta property="article:section" content="{html.escape(series['section'], quote=True)}">
{tags}
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{article_image}">
    <script type="application/ld+json">
{ld_json}
    </script>
    <link rel="stylesheet" href="assets/article.css">
</head>
<body class="{html.escape(series.get('body_class', ''), quote=True)}">
<div class="progress-bar" id="progressBar"></div>
<nav class="site-nav" aria-label="Primary navigation">
    <div class="nav-inner">
        <a class="brand" href="/">Andrea Padula</a>
        <div class="nav-links">
            <a href="{html.escape(series['slug'])}.html">{html.escape(series['short_label'])}</a>
            <a href="about.html">About</a>
            <a href="https://www.linkedin.com/in/andreapadula/" rel="me">LinkedIn</a>
        </div>
    </div>
</nav>

<header class="article-hero">
    <div class="hero-inner">
        <div class="eyebrow">{html.escape(series['short_label'])} · Essay {index:02d}/{total:02d}</div>
        <h1>{title}</h1>
        <p class="hero-subtitle">{html.escape(subtitle)}</p>
        <div class="article-meta">
            <a href="about.html" rel="author">Andrea Padula</a>
            <time class="meta-dot" datetime="{published}">{visible_date}</time>
            <span class="meta-dot">{reading_time} min read</span>
        </div>
    </div>
</header>

<main>
    <div class="article-shell">
        <article class="article-body">
{body_html}
        </article>
        <aside class="article-aside" aria-label="About this series">
            <div class="aside-card">
                <div class="aside-label">The series</div>
                <p>{html.escape(series['aside_copy'])}</p>
                <a href="{html.escape(series['slug'])}.html">Explore all ten →</a>
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
            <a href="about.html"><img src="andrea-padula.png" alt="Andrea Padula" width="66" height="66"></a>
            <div class="author-copy">
                <h2><a href="about.html">Andrea Padula</a></h2>
                <p>Head of Partnerships &amp; Business Development at Streetbeat. Writing from Milan about AI, financial services, and the bridge between European banking and Silicon Valley technology.</p>
                <p class="disclosure">Andrea leads Partnerships &amp; BD at Streetbeat; views are personal.</p>
            </div>
        </div>
    </section>
</main>

<footer class="site-footer">
    <p>© 2026 Andrea Padula · <a href="{html.escape(series['slug'])}.html">{html.escape(series['short_label'])}</a> · <a href="mailto:andreapadula@streetbeat.com">Contact</a></p>
</footer>
<script src="assets/article.js" defer></script>
</body>
</html>
'''


def json_ld_series(manifest: dict, series: dict) -> str:
    series_url = f"{SITE_URL}/{series['slug']}.html"
    items = [
        {
            "@type": "ListItem",
            "position": index,
            "name": article["title"],
            "url": f"{SITE_URL}/{article['slug']}.html",
        }
        for index, article in enumerate(manifest["articles"], start=1)
    ]
    graph = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": series_url,
                "url": series_url,
                "name": series["title"],
                "description": series["description"],
                "inLanguage": "en",
                "datePublished": manifest["published"],
                "dateModified": manifest["published"],
                "author": {"@id": AUTHOR_ID},
                "mainEntity": {"@type": "ItemList", "numberOfItems": len(items), "itemListElement": items},
            },
            {
                "@type": "Person",
                "@id": AUTHOR_ID,
                "name": "Andrea Padula",
                "url": f"{SITE_URL}/about.html",
                "image": AUTHOR_IMAGE_URL,
                "jobTitle": "Head of Partnerships & Business Development",
                "sameAs": ["https://www.linkedin.com/in/andreapadula/", "https://medium.com/@padula.andrea"],
            },
        ],
    }
    return json.dumps(graph, ensure_ascii=False, indent=8)


def render_series(manifest: dict, drafts: dict[str, dict], series: dict) -> str:
    cards_by_slug = {}
    cards_h2_by_slug = {}
    for index, article in enumerate(manifest["articles"], start=1):
        draft = drafts[article["slug"]]
        reading_time = max(1, math.ceil(draft["word_count"] / 220))
        card = (
            f'''        <a class="series-card" href="{html.escape(article['slug'])}.html">
            <div class="card-number">ESSAY {index:02d}</div>
            <h3>{html.escape(article['title'])}</h3>
            <p>{html.escape(article['description'])}</p>
            <div class="card-meta">{reading_time} min read · Primary sources</div>
            <span class="card-arrow" aria-hidden="true">→</span>
        </a>'''
        )
        cards_by_slug[article["slug"]] = card
        cards_h2_by_slug[article["slug"]] = card.replace("<h3>", "<h2>").replace("</h3>", "</h2>")

    chapters = series.get("chapters", [])
    if chapters:
        rendered_chapters = []
        seen = []
        for chapter_index, chapter in enumerate(chapters, start=1):
            for slug in chapter["slugs"]:
                if slug not in cards_by_slug:
                    raise ValueError(f"Unknown chapter article slug: {slug}")
                if slug in seen:
                    raise ValueError(f"Article appears in more than one chapter: {slug}")
                seen.append(slug)
            chapter_cards = "\n".join(cards_by_slug[slug] for slug in chapter["slugs"])
            rendered_chapters.append(
                f'''    <section class="series-chapter" aria-labelledby="chapter-{chapter_index}">
        <div class="chapter-heading">
            <h2 id="chapter-{chapter_index}">{html.escape(chapter['title'])}</h2>
            <p>{html.escape(chapter['description'])}</p>
        </div>
        <div class="series-grid">
{chapter_cards}
        </div>
    </section>'''
            )
        missing = sorted(set(cards_by_slug) - set(seen))
        if missing:
            raise ValueError(f"Chapter configuration does not cover every article: {missing}")
        collection_html = "\n".join(rendered_chapters)
    else:
        collection_html = f'''    <section class="series-grid" aria-label="Ten essays">
{chr(10).join(cards_h2_by_slug[article['slug']] for article in manifest['articles'])}
    </section>'''

    intro_rows = []
    for index, paragraph in enumerate(series["intro"]):
        copy = html.escape(paragraph)
        if index == series.get("intro_emphasis"):
            copy = f"<strong>{copy}</strong>"
        intro_rows.append(f"            <p>{copy}</p>")
    intro_html = "\n".join(intro_rows)
    ld_json = json_ld_series(manifest, series)
    description = series["description"]
    series_url = f"{SITE_URL}/{series['slug']}.html"

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{html.escape(series['title'])} — Andrea Padula</title>
    <meta name="description" content="{html.escape(description, quote=True)}">
    <meta name="author" content="Andrea Padula">
    <meta name="keywords" content="{html.escape(', '.join(series['keywords']), quote=True)}">
    <link rel="canonical" href="{series_url}">
    <meta property="og:site_name" content="Andrea Padula">
    <meta property="og:title" content="{html.escape(series['title'], quote=True)}">
    <meta property="og:description" content="{html.escape(description, quote=True)}">
    <meta property="og:image" content="{SITE_URL}/assets/articles/{html.escape(series['slug'])}.png">
    <meta property="og:image:alt" content="{html.escape(series['title'], quote=True)} — a ten-essay series by Andrea Padula">
    <meta property="og:image:width" content="1200">
    <meta property="og:image:height" content="630">
    <meta property="og:url" content="{series_url}">
    <meta property="og:type" content="website">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{html.escape(series['title'], quote=True)}">
    <meta name="twitter:description" content="{html.escape(description, quote=True)}">
    <meta name="twitter:image" content="{SITE_URL}/assets/articles/{html.escape(series['slug'])}.png">
    <script type="application/ld+json">
{ld_json}
    </script>
    <link rel="stylesheet" href="assets/article.css">
</head>
<body class="{html.escape(series.get('body_class', ''), quote=True)}">
<nav class="site-nav" aria-label="Primary navigation">
    <div class="nav-inner">
        <a class="brand" href="/">Andrea Padula</a>
        <div class="nav-links">
            <a href="/">Home</a>
            <a href="about.html">About</a>
            <a href="https://medium.com/@padula.andrea" rel="me">Medium</a>
        </div>
    </div>
</nav>

<header class="series-hero">
    <div class="hero-inner">
        <div class="eyebrow">{html.escape(series['hero_label'])}</div>
        <h1>{html.escape(series['title'])}</h1>
        <p class="hero-subtitle">{html.escape(series['hero_subtitle'])}</p>
    </div>
</header>

<main>
    <section class="series-intro" aria-label="About the series">
        <div class="series-copy">
{intro_html}
        </div>
        <aside class="series-note">
            <div class="label">Editorial standard</div>
            <p>{html.escape(series['editorial_standard'])}</p>
        </aside>
    </section>

{collection_html}

    <section class="series-cta">
        <div class="series-cta-inner">
            <h2>{html.escape(series['cta_title'])}</h2>
            <p>{html.escape(series['cta_copy'])}</p>
            <a class="button" href="mailto:andreapadula@streetbeat.com">Start a conversation</a>
        </div>
    </section>
</main>

<footer class="site-footer">
    <p>© 2026 Andrea Padula · <a href="about.html">About</a> · <a href="https://www.linkedin.com/in/andreapadula/">LinkedIn</a> · <a href="https://medium.com/@padula.andrea">Medium</a></p>
</footer>
</body>
</html>
'''


def main() -> None:
    args = parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    series = manifest["series"]
    published = manifest["published"]
    lookup = article_lookup(args.site)
    parsed: dict[str, dict] = {}

    for article in manifest["articles"]:
        draft_path = args.drafts / f"{article['slug']}.md"
        if not draft_path.exists():
            raise FileNotFoundError(f"Missing draft: {draft_path}")
        draft_title, subtitle, body_html, word_count = read_draft(draft_path)
        if title_key(draft_title) != title_key(article["title"]):
            raise ValueError(f"Title mismatch in {draft_path}: {draft_title!r} != {article['title']!r}")
        if not subtitle:
            raise ValueError(f"Missing italic subtitle in {draft_path}")
        if word_count < 1000:
            raise ValueError(f"Draft is unexpectedly short ({word_count} words): {draft_path}")
        parsed[article["slug"]] = {
            "subtitle": subtitle,
            "body_html": body_html,
            "word_count": word_count,
        }

    for index, article in enumerate(manifest["articles"], start=1):
        draft = parsed[article["slug"]]
        page = render_article(
            article,
            index,
            len(manifest["articles"]),
            draft["subtitle"],
            draft["body_html"],
            draft["word_count"],
            published,
            lookup,
            series,
        )
        (args.site / f"{article['slug']}.html").write_text(page, encoding="utf-8")

    series_slug = series["slug"]
    (args.site / f"{series_slug}.html").write_text(render_series(manifest, parsed, series), encoding="utf-8")
    print(f"Built {len(manifest['articles'])} articles and {series_slug}.html")


if __name__ == "__main__":
    main()
