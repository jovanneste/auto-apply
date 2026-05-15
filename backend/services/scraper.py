import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Page

from backend.config import SCREENSHOTS_DIR
from backend.services.ats_detector import detect_ats_from_url, detect_ats_from_page
from backend.services.form_extractor import extract_fields, find_next_button, find_apply_button, fill_placeholders
from backend.utils.streaming import sse_event


async def scrape_job(
    url: str,
    queue: asyncio.Queue,
    continue_event: asyncio.Event,
) -> Optional[tuple]:
    """
    Navigate to a job application URL, extract all form fields across all pages.

    Returns (fields_data, screenshot_path, ats_type, job_title, organization) or None on fatal error.
    """

    async def emit(event_type: str, **kwargs):
        await queue.put(sse_event(event_type, **kwargs))

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            ats_type = detect_ats_from_url(url)
            await emit("status", message=f"Detected ATS: {ats_type}")

            await emit("status", message="Loading page...")
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Refine ATS detection from page content
            content = await page.content()
            ats_type = await detect_ats_from_page(url, content)
            await emit("status", message=f"ATS confirmed: {ats_type}")

            # Check for login wall
            if await _is_login_wall(page):
                await emit("needs_action", action="login",
                           message="A login page was detected. Please log in in the browser window, then click Continue.")
                browser_vis = await pw.chromium.launch(headless=False)
                context_vis = await browser_vis.new_context()
                page = await context_vis.new_page()
                await page.goto(url, wait_until="networkidle", timeout=30000)
                await emit("status", message="Waiting for you to log in and click Continue...")
                await continue_event.wait()
                continue_event.clear()
                await emit("status", message="Resumed. Continuing...")

            # Try to find and click "Apply Now" button
            apply_btn = await find_apply_button(page)
            if apply_btn:
                await emit("status", message="Clicking 'Apply Now'...")
                await apply_btn.click()
                await page.wait_for_load_state("networkidle", timeout=15000)

            # Extract job title and organization from page metadata
            job_title = await _extract_job_title(page)
            organization = await _extract_organization(page)
            await emit("status", message=f"Job: {job_title} at {organization}")

            # Multi-step extraction loop
            all_fields: list[dict] = []
            page_num = 1
            first_screenshot_path: Optional[str] = None

            while True:
                await emit("status", message=f"Extracting fields from page {page_num}...")

                # Check for CAPTCHA
                if await _has_captcha(page):
                    await emit("needs_action", action="captcha",
                               message="A CAPTCHA was detected. Please solve it in the browser window, then click Continue.")
                    await continue_event.wait()
                    continue_event.clear()
                    await emit("status", message="CAPTCHA resolved. Continuing...")

                fields = await _extract_with_fallback(page, page_num)
                await emit("status", message=f"Found {len(fields)} fields on page {page_num}")
                all_fields.extend(fields)

                # Screenshot of first page
                if page_num == 1:
                    screenshot_path = str(SCREENSHOTS_DIR / f"job_screenshot.png")
                    await page.screenshot(path=screenshot_path, full_page=True)
                    first_screenshot_path = screenshot_path

                # Look for next button
                next_btn = await find_next_button(page)
                if not next_btn:
                    await emit("status", message="Reached last form page.")
                    break

                # Fill placeholders to pass client-side validation
                await fill_placeholders(page, fields)

                await emit("status", message=f"Navigating to page {page_num + 1}...")
                await next_btn.click()

                try:
                    await page.wait_for_load_state("networkidle", timeout=10000)
                except Exception:
                    await asyncio.sleep(1)

                await asyncio.sleep(0.5)
                page_num += 1

                if page_num > 10:
                    await emit("status", message="Reached page limit (10). Stopping.")
                    break

            return all_fields, first_screenshot_path, ats_type, job_title, organization

        except Exception as e:
            await emit("error", message=f"Scraping failed: {str(e)}")
            return None
        finally:
            await browser.close()


async def _extract_with_fallback(page: Page, page_num: int) -> list[dict]:
    """Try standard DOM extraction, fall back to accessibility snapshot."""
    fields = await extract_fields(page, page_num)
    if fields:
        return fields

    # Wait a bit and retry
    await asyncio.sleep(3)
    fields = await extract_fields(page, page_num)
    if fields:
        return fields

    # Fallback: use accessibility snapshot
    snapshot = await page.accessibility.snapshot()
    if snapshot:
        fields = _fields_from_accessibility(snapshot, page_num)

    return fields


def _fields_from_accessibility(node: dict, page_num: int, depth: int = 0) -> list[dict]:
    """Recursively extract editable nodes from Playwright accessibility snapshot."""
    fields = []
    role = node.get("role", "")
    if role in ("textbox", "combobox", "listbox", "spinbutton", "searchbox"):
        fields.append({
            "page_number": page_num,
            "field_type": "textarea" if role == "textbox" else "select",
            "field_label": node.get("name", ""),
            "field_name": node.get("name", ""),
            "field_placeholder": None,
            "is_required": node.get("required", False),
            "options_json": None,
            "display_order": depth,
        })
    for child in node.get("children", []):
        fields.extend(_fields_from_accessibility(child, page_num, depth + 1))
    return fields


async def _is_login_wall(page: Page) -> bool:
    url = page.url.lower()
    if any(p in url for p in ["/login", "/signin", "/auth", "/sign-in"]):
        return True
    pwd = page.locator("input[type=password]")
    if await pwd.count() > 0 and await pwd.first.is_visible():
        return True
    return False


async def _has_captcha(page: Page) -> bool:
    for selector in ["iframe[src*='recaptcha']", "iframe[src*='hcaptcha']", ".g-recaptcha", "[data-sitekey]"]:
        el = page.locator(selector)
        if await el.count() > 0:
            return True
    return False


async def _extract_job_title(page: Page) -> str:
    for selector in ["h1", "[class*='job-title']", "[class*='position-title']", "title"]:
        el = page.locator(selector).first
        try:
            if await el.count() > 0:
                text = await el.inner_text()
                if text and len(text) < 200:
                    return text.strip()
        except Exception:
            continue
    return "Unknown Position"


async def _extract_organization(page: Page) -> str:
    for selector in ["[class*='company']", "[class*='employer']", "[class*='organization']"]:
        el = page.locator(selector).first
        try:
            if await el.count() > 0:
                text = await el.inner_text()
                if text and len(text) < 100:
                    return text.strip()
        except Exception:
            continue
    # Fall back to domain name
    from urllib.parse import urlparse
    return urlparse(page.url).netloc.replace("www.", "").split(".")[0].title()
