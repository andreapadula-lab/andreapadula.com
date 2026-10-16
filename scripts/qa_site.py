#!/usr/bin/env python3
"""Responsive browser QA for the primary site journeys and both article systems."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin, urlparse
from xml.etree import ElementTree

from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:4173/"
SCREENSHOT_DIR = Path("/tmp/andrea-site-qa")
ROOT = Path(__file__).resolve().parents[1]

PAGES = [
    "",
    "writing.html",
    "about.html",
    "vision.html",
    "speaking.html",
    "contact.html",
    "five-ambitions-worth-a-lifetime.html",
    "ai-financial-services.html",
    "one-brain-many-minds.html",
    "trust-is-not-a-model-score.html",
    "deep-work-is-the-new-competitive-advantage.html",
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "laptop": {"width": 1024, "height": 900},
    "breakpoint": {"width": 861, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
    "narrow": {"width": 320, "height": 720},
}


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def label(path: str) -> str:
    return path.removesuffix(".html") or "home"


def sitemap_paths() -> list[str]:
    locations = [
        element.text.strip()
        for url in ElementTree.parse(ROOT / "sitemap.xml").findall("{*}url")
        for element in url.findall("{*}loc")
        if element.text and element.text.strip()
    ]
    expect(locations, "sitemap.xml contains no URLs")

    paths: list[str] = []
    for location in locations:
        parsed = urlparse(location)
        expect(parsed.scheme == "https", f"Sitemap URL must use HTTPS: {location}")
        expect(parsed.netloc in {"andreapadula.com", "www.andreapadula.com"}, f"Unexpected sitemap host: {location}")
        expect(not parsed.query and not parsed.fragment, f"Sitemap URL must not contain query or fragment: {location}")
        paths.append(parsed.path.lstrip("/") or "")

    expect(len(paths) == len(set(paths)), "sitemap.xml contains duplicate URLs")
    return paths


def verify_portrait_policy(paths: list[str]) -> None:
    """Andrea's portrait belongs only on About; article artwork is unaffected."""
    for route in paths:
        path = ROOT / (route or "index.html")
        source = path.read_text(encoding="utf-8")
        main = source.split("<main", 1)[-1].split("</main>", 1)[0]
        has_portrait = 'src="assets/andrea-padula' in main or 'src="andrea-padula' in main
        if route == "about.html":
            expect(has_portrait, "about: portrait missing from main content")
        else:
            expect(not has_portrait, f"{label(route)}: portrait must remain exclusive to About")


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    console_errors: list[str] = []
    page_errors: list[str] = []
    failed_requests: list[str] = []
    checked = 0

    with sync_playwright() as playwright:
        request = playwright.request.new_context(base_url=BASE_URL)
        sitemap_routes = sitemap_paths()
        verify_portrait_policy(sitemap_routes)
        for path in sitemap_routes:
            response = request.get(path or "/")
            expect(response.status == 200, f"sitemap/{label(path)}: expected HTTP 200, got {response.status}")
        request.dispose()

        browser = playwright.chromium.launch(headless=True)

        for viewport_name, viewport in VIEWPORTS.items():
            context = browser.new_context(viewport=viewport, device_scale_factor=1)
            page = context.new_page()
            page.on(
                "console",
                lambda message, vp=viewport_name: console_errors.append(f"{vp}: {message.text}")
                if message.type == "error"
                else None,
            )
            page.on("pageerror", lambda error, vp=viewport_name: page_errors.append(f"{vp}: {error}"))
            page.on(
                "requestfailed",
                lambda request, vp=viewport_name: failed_requests.append(f"{vp}: {request.url}"),
            )

            for path in PAGES:
                response = page.goto(urljoin(BASE_URL, path), wait_until="networkidle")
                page_name = label(path)
                prefix = f"{viewport_name}/{page_name}"
                expect(response is not None and response.status == 200, f"{prefix}: expected HTTP 200")
                expect(page.locator("main").count() == 1, f"{prefix}: expected one main landmark")
                expect(page.locator("main").get_attribute("tabindex") == "-1", f"{prefix}: main must receive skip-link focus")
                expect(page.locator("h1").count() == 1, f"{prefix}: expected one H1")
                expect(page.locator(".site-header .wordmark").count() == 1, f"{prefix}: shared navigation missing")
                expect(page.locator("a[href='writing.html']").count() >= 1, f"{prefix}: Writing navigation missing")
                expect(
                    page.locator(".nav-links > a").all_inner_texts() == ["Home", "About", "Writing", "Speaking"],
                    f"{prefix}: primary navigation order is incorrect",
                )
                expect(
                    page.locator(".nav-cta[href='contact.html']").count() == 1,
                    f"{prefix}: Contact CTA is missing or does not use contact.html",
                )
                if viewport["width"] > 860:
                    contact_box = page.locator(".nav-cta[href='contact.html']").bounding_box()
                    expect(
                        contact_box is not None and contact_box["height"] >= 44,
                        f"{prefix}: desktop Contact target is smaller than 44px",
                    )
                expect(
                    [text.replace("→", "").strip() for text in page.locator("#site-menu > a").all_inner_texts()]
                    == ["Home", "About", "Writing", "Speaking", "Contact"],
                    f"{prefix}: mobile navigation order is incorrect",
                )
                expect(page.locator("footer a[href='speaking.html']").count() >= 1, f"{prefix}: Speaking footer link missing")
                expect(page.locator(".site-header a[href='speaking.html']").count() >= 1, f"{prefix}: Speaking primary link missing")
                expect(page.locator(".site-header a[href='vision.html']").count() == 0, f"{prefix}: Vision must remain secondary")
                expect(
                    page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1"),
                    f"{prefix}: horizontal overflow",
                )
                expect(
                    page.locator("img:not([alt])").count() == 0,
                    f"{prefix}: image without alt attribute",
                )
                expect(
                    page.evaluate("Array.from(document.images).filter(img => img.loading !== 'lazy').every(img => img.complete && img.naturalWidth > 0)"),
                    f"{prefix}: broken eager image",
                )
                for script in page.locator("script[type='application/ld+json']").all_text_contents():
                    json.loads(script)

                if path == "":
                    expect(page.locator("main img[src*='andrea-padula']").count() == 0, f"{prefix}: portrait should not appear on the home page")
                    expect(page.locator(".ed-domain-card").count() == 3, f"{prefix}: home must present three clear domains")
                    expect(page.locator(".ed-operating-card").count() == 1, f"{prefix}: home operating context missing")
                if path == "speaking.html":
                    expect(page.locator("main img").count() == 0, f"{prefix}: portrait should not appear on Speaking")
                if path == "speaking.html":
                    expect("One Brain" not in page.locator("main").inner_text(), f"{prefix}: series concept is still a primary speaking theme")
                if path == "about.html":
                    portrait = page.locator(".ed-portrait img")
                    expect(portrait.count() == 1, f"{prefix}: about portrait missing")
                    portrait_width = portrait.bounding_box()["width"]
                    width_limit = 320 if viewport["width"] > 760 else 210
                    expect(portrait_width <= width_limit, f"{prefix}: about portrait is too large ({portrait_width}px)")
                if path == "writing.html":
                    latest_top = page.locator("#start-here").bounding_box()["y"]
                    series_top = page.locator(".ed-series").bounding_box()["y"]
                    expect(latest_top < series_top, f"{prefix}: writing should lead with essays, not series")
                    expect(page.locator(".ed-theme-card").count() == 3, f"{prefix}: Writing must use three themes")
                    expect(page.locator(".ed-archive-list > li").count() == 39, f"{prefix}: full archive must retain 39 essays")
                    expect(not page.locator(".ed-archive-disclosure").evaluate("node => node.open"), f"{prefix}: full archive should start collapsed")
                if path == "vision.html":
                    expect(
                        page.locator(".nav-links a[href='vision.html']").count() == 0,
                        f"{prefix}: Vision must not be a primary navigation section",
                    )
                    expect(
                        page.locator(".ed-vision-list > li").count() == 5,
                        f"{prefix}: Vision must present five ambitions",
                    )
                    expect(
                        page.locator(".ed-vision-list li > p").evaluate_all(
                            """elements => elements.every(element => {
                                const rect = element.getBoundingClientRect();
                                return rect.width > 0 && rect.left >= -1 && rect.right <= window.innerWidth + 1;
                            })"""
                        ),
                        f"{prefix}: ambition descriptions are clipped",
                    )
                    expect(
                        page.locator("a[href='five-ambitions-worth-a-lifetime.html']").count() >= 2,
                        f"{prefix}: Vision must lead to the founding essay",
                    )
                    cover = page.locator(".ed-manifesto-cover img")
                    cover.scroll_into_view_if_needed()
                    expect(
                        cover.evaluate(
                            "img => img.decode().then(() => img.naturalWidth === 1200 && img.naturalHeight === 630)"
                        ),
                        f"{prefix}: manifesto cover did not load at its declared size",
                    )
                if path == "ai-financial-services.html":
                    expect(
                        page.locator(".eyebrow").inner_text().casefold().startswith("analysis ·"),
                        f"{prefix}: AI series must use the Analysis editorial type",
                    )
                if path in {"one-brain-many-minds.html", "trust-is-not-a-model-score.html"}:
                    expect(
                        page.locator(".eyebrow").inner_text().casefold().startswith("reflection ·"),
                        f"{prefix}: One Brain series must use the Reflection editorial type",
                    )
                if path == "five-ambitions-worth-a-lifetime.html":
                    expect(
                        page.locator(".eyebrow").inner_text().casefold().startswith("manifesto ·"),
                        f"{prefix}: standalone essay must use the Manifesto editorial type",
                    )
                    expect(
                        page.locator(".article-body h2").count() >= 10,
                        f"{prefix}: manifesto structure is incomplete",
                    )
                    expect(
                        page.locator(".nav-links a[href='writing.html'][aria-current='page']").count() == 1,
                        f"{prefix}: manifesto must belong to Writing in primary navigation",
                    )
                checked += 1

                if (
                    (viewport_name == "desktop" and path in {"", "writing.html", "about.html", "vision.html", "speaking.html", "contact.html", "one-brain-many-minds.html", "five-ambitions-worth-a-lifetime.html"})
                    or (viewport_name == "breakpoint" and path in {"", "vision.html"})
                    or (viewport_name == "tablet" and path == "vision.html")
                    or (viewport_name == "mobile" and path in {"", "writing.html", "about.html", "vision.html", "speaking.html", "contact.html", "trust-is-not-a-model-score.html", "deep-work-is-the-new-competitive-advantage.html", "five-ambitions-worth-a-lifetime.html"})
                ):
                    page.evaluate(
                        "() => { document.documentElement.style.scrollBehavior = 'auto'; if (document.activeElement instanceof HTMLElement) document.activeElement.blur(); document.querySelector('.skip-link')?.blur(); window.scrollTo(0, 0); }"
                    )
                    page.wait_for_function("window.scrollY === 0")
                    page.screenshot(
                        path=str(SCREENSHOT_DIR / f"{viewport_name}-{page_name}.png"),
                        full_page=True,
                    )

            page.goto(BASE_URL, wait_until="networkidle")
            if viewport["width"] <= 860:
                toggle = page.locator(".nav-toggle")
                drawer = page.locator("#site-menu")
                expect(toggle.is_visible(), f"{viewport_name}: mobile nav toggle should be visible")
                expect(not drawer.is_visible(), f"{viewport_name}: mobile nav drawer should start closed")
                toggle.click()
                expect(toggle.get_attribute("aria-expanded") == "true", f"{viewport_name}: nav did not expand")
                expect(drawer.is_visible(), f"{viewport_name}: nav drawer is not visible after opening")
                page.keyboard.press("Escape")
                expect(toggle.get_attribute("aria-expanded") == "false", f"{viewport_name}: Escape did not close nav")
                expect(not drawer.is_visible(), f"{viewport_name}: nav drawer remained visible")
            else:
                expect(page.locator(".nav-links").is_visible(), f"{viewport_name}: desktop navigation is hidden")

            context.close()

        browser.close()

    ignored_console_fragments = ("favicon.ico",)
    filtered_console = [
        error for error in console_errors if not any(fragment in error for fragment in ignored_console_fragments)
    ]
    filtered_failures = [
        failure for failure in failed_requests if not any(fragment in failure for fragment in ignored_console_fragments)
    ]
    expect(not filtered_console, f"Browser console errors: {filtered_console}")
    expect(not page_errors, f"Page errors: {page_errors}")
    expect(not filtered_failures, f"Failed requests: {filtered_failures}")
    print(f"QA passed: {checked} page/viewport combinations and {len(sitemap_routes)} sitemap URLs")
    print(f"Screenshots: {SCREENSHOT_DIR}")


if __name__ == "__main__":
    main()
