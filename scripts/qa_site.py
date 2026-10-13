#!/usr/bin/env python3
"""Responsive browser QA for the primary site journeys and both article systems."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urljoin

from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:4173/"
SCREENSHOT_DIR = Path("/tmp/andrea-site-qa")

PAGES = [
    "",
    "writing.html",
    "about.html",
    "speaking.html",
    "ai-financial-services.html",
    "one-brain-many-minds.html",
    "trust-is-not-a-model-score.html",
    "deep-work-is-the-new-competitive-advantage.html",
]

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 1000},
    "laptop": {"width": 1024, "height": 900},
    "tablet": {"width": 768, "height": 1024},
    "mobile": {"width": 390, "height": 844},
    "narrow": {"width": 320, "height": 720},
}


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def label(path: str) -> str:
    return path.removesuffix(".html") or "home"


def main() -> None:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    console_errors: list[str] = []
    page_errors: list[str] = []
    failed_requests: list[str] = []
    checked = 0

    with sync_playwright() as playwright:
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
                expect(page.locator("h1").count() == 1, f"{prefix}: expected one H1")
                expect(page.locator(".site-header .wordmark").count() == 1, f"{prefix}: shared navigation missing")
                expect(page.locator("a[href='writing.html']").count() >= 1, f"{prefix}: Writing navigation missing")
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
                checked += 1

                if (
                    (viewport_name == "desktop" and path in {"", "writing.html", "one-brain-many-minds.html"})
                    or (viewport_name == "mobile" and path in {"", "writing.html", "about.html", "speaking.html", "trust-is-not-a-model-score.html", "deep-work-is-the-new-competitive-advantage.html"})
                ):
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
    print(f"QA passed: {checked} page/viewport combinations")
    print(f"Screenshots: {SCREENSHOT_DIR}")


if __name__ == "__main__":
    main()
