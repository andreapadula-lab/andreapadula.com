#!/usr/bin/env python3
"""Apply the shared site shell to the hand-authored legacy essays.

The article copy and metadata are intentionally left untouched. The script only
adds the shared styles/scripts, navigation landmarks, optimized author portrait,
and compact footer. It is safe to run more than once.
"""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

OLD_NAV = (
    '<nav><div class="container"><a href="/" class="name">Andrea Padula</a>'
    '<a href="/" class="back">Home</a></div></nav>'
)

SHARED_NAV = '''<header class="site-header">
    <nav class="nav-shell" aria-label="Primary navigation">
        <a class="wordmark" href="/" aria-label="Andrea Padula, home">Andrea Padula</a>
        <div class="nav-links">
            <a class="nav-link" href="/">Home</a>
            <a class="nav-link" href="about.html">Journey</a>
            <a class="nav-link" href="writing.html" aria-current="page">Writing</a>
        </div>
        <a class="nav-cta" href="contact.html">Contact</a>
        <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-menu" aria-label="Open navigation"><span></span></button>
        <div class="nav-drawer" id="site-menu" hidden>
            <a class="drawer-link" href="/">Home <span aria-hidden="true">→</span></a>
            <a class="drawer-link" href="about.html">Journey <span aria-hidden="true">→</span></a>
            <a class="drawer-link" href="writing.html" aria-current="page">Writing <span aria-hidden="true">→</span></a>
            <a class="drawer-link" href="contact.html">Contact <span aria-hidden="true">→</span></a>
        </div>
    </nav>
</header>'''

SHARED_FOOTER = '''<footer class="site-footer article-footer">
    <div class="article-footer-inner">
        <p>© 2026 Andrea Padula · AI, technology, choices, and the inner life.</p>
        <nav class="footer-links" aria-label="Footer navigation">
            <a href="about.html">Journey</a>
            <a href="writing.html">Writing</a>
            <a href="speaking.html">Speaking</a>
            <a href="contact.html">Contact</a>
        </nav>
    </div>
</footer>'''


def is_legacy_article(path: Path, text: str) -> bool:
    return (
        '<meta property="og:type" content="article">' in text
        and 'assets/article.css' not in text
        and (OLD_NAV in text or 'assets/legacy-article.css' in text)
    )


def modernize(text: str, path: Path) -> str:
    # Inter is bundled with the site. Keep every essay independent from a
    # third-party font request, including pages modernized by an earlier run.
    text = re.sub(
        r"^[ \t]*@import url\(['\"]https://fonts\.googleapis\.com/[^\n]+\);[ \t]*\n?",
        "",
        text,
        flags=re.MULTILINE,
    )

    if 'assets/legacy-article.css' in text:
        text = text.replace('class="footer-inner"', 'class="article-footer-inner"')
        text, nav_count = re.subn(
            r'<header class="site-header">.*?</header>',
            SHARED_NAV,
            text,
            count=1,
            flags=re.DOTALL,
        )
        if nav_count != 1:
            raise ValueError(f"Expected one shared navigation in {path.name}")
        text, footer_count = re.subn(
            r'<footer class="site-footer article-footer">.*?</footer>',
            SHARED_FOOTER,
            text,
            count=1,
            flags=re.DOTALL,
        )
        if footer_count != 1:
            raise ValueError(f"Expected one shared footer in {path.name}")
        return text

    original = text
    style_close = '    </style>\n</head>'
    if text.count(style_close) != 1:
        raise ValueError(f"Expected one inline style terminator in {path.name}")
    text = text.replace(
        style_close,
        '    </style>\n    <link rel="stylesheet" href="assets/site.css">\n'
        '    <link rel="stylesheet" href="assets/legacy-article.css">\n</head>',
    )

    if text.count('<body>') != 1:
        raise ValueError(f"Expected one body tag in {path.name}")
    text = text.replace(
        '<body>',
        '<body class="legacy-article">\n<a class="skip-link" href="#main">Skip to content</a>',
        1,
    )

    if text.count(OLD_NAV) != 1:
        raise ValueError(f"Expected one legacy nav in {path.name}")
    text = text.replace(OLD_NAV, SHARED_NAV, 1)

    hero_marker = '\n\n<div class="hero-img">'
    if text.count(hero_marker) != 1:
        raise ValueError(f"Expected one hero marker in {path.name}")
    text = text.replace(hero_marker, '\n\n<main id="main" tabindex="-1">\n<div class="hero-img">', 1)

    text = text.replace(
        '<img src="andrea-padula.png" alt="Andrea Padula">',
        '<img src="assets/andrea-padula-192.jpg" alt="Andrea Padula" width="192" height="192" loading="lazy">',
        1,
    )

    text, footer_count = re.subn(
        r'<footer><div class="container"><p>&copy; 2026 Andrea Padula(?:\. All rights reserved\.)?</p></div></footer>',
        f'</main>\n{SHARED_FOOTER}',
        text,
        count=1,
    )
    if footer_count != 1:
        raise ValueError(f"Expected one legacy footer in {path.name}")

    text, script_count = re.subn(
        r'<script>\s*window\.addEventListener\(\'scroll\'.*?</script>',
        '<script src="assets/article.js" defer></script>\n<script src="assets/site.js" defer></script>',
        text,
        count=1,
        flags=re.DOTALL,
    )
    if script_count != 1:
        raise ValueError(f"Expected one progress script in {path.name}")

    if text == original:
        raise ValueError(f"No changes produced for {path.name}")
    return text


def main() -> None:
    changed: list[str] = []
    for path in sorted(ROOT.glob('*.html')):
        source = path.read_text(encoding='utf-8')
        if not is_legacy_article(path, source):
            continue
        updated = modernize(source, path)
        if updated != source:
            path.write_text(updated, encoding='utf-8')
            changed.append(path.name)

    print(f"Modernized {len(changed)} legacy articles")
    for name in changed:
        print(f"- {name}")


if __name__ == '__main__':
    main()
