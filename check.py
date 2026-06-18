from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from pathlib import Path
from typing import List
from bs4 import BeautifulSoup
import time
from notification import send_notification
from sound import victory_sound


OUT_DIR = Path("html_dumps")
OUT_DIR.mkdir(exist_ok=True)

def beautify(html: str) -> str:
    return BeautifulSoup(html, "html.parser").prettify()


RETRY_TIMES = 86400        # how many times to retry after reload
WAIT_30S = 30_000        # 30 seconds
FIND_TIMEOUT = 10_000    # how long to wait to find "空" each attempt


def submit_login(frame):
    # Try common submit controls inside the frame
    candidates = [
        'input[type="submit"]',
        'button[type="submit"]',
        'input[type="image"]',
        'button:has-text("ログイン")',
        'button:has-text("Login")',
    ]
    for sel in candidates:
        loc = frame.locator(sel).first
        if loc.count() > 0:
            loc.click()
            return True

    # Fallback: press Enter while focused on password
    frame.locator("#txtPassword").press("Enter")
    return True

# def find_kara_bage_and_sound(frame):
#     # badge element that visually shows: <span class="badge">空</span>
#     badge = frame.locator("span.badge:has-text('空')").first
#     badge.wait_for(state="visible", timeout=FIND_TIMEOUT)
#     return badge  # found


# def click_in_frame(frame, selector, wait_ms=30000):
#     btn = frame.locator(selector)
#     print(f"Selector clicked: {selector}")
#     btn.wait_for(state="visible", timeout=wait_ms)
#     btn.click()


def click_week(frame, which, timeout_ms=30000):
    assert which in ("next", "previous")

    if which == "next":
        input_id = "btnNextWeek"
        label_sel = 'label[for="btnNextWeek"]'
    else:
        input_id = "btnPreviousWeek"
        label_sel = 'label[for="btnPreviousWeek"]'

    # 1) Prefer clicking the label (usually visible)
    label = frame.locator(label_sel).first
    try:
        if label.count() > 0:
            label.wait_for(state="attached", timeout=timeout_ms)
            # label may still be off-screen; allow forced click
            label.click(force=True, timeout=timeout_ms)
            return
    except Exception:
        pass

    # 2) Fallback: JS click the input even if "collapsed/not visible"
    inp = frame.locator(f"#{input_id}").first
    inp.wait_for(state="attached", timeout=timeout_ms)
    inp.evaluate("el => el.click()")  # bypass visibility restrictions


# def is_badge_found(frame):
#     badge = frame.locator("span.badge:has-text('空')").first
#     return badge.count() > 0

# def should_sound_empty_outside_date(container, date_str) -> bool:
#     js = """
#     (dateStr) => {
#       const blocks = Array.from(document.querySelectorAll('div.blocks'));
#       for (const block of blocks) {
#         const lbl = block.querySelector('span.lbl');
#         const badge = block.querySelector('span.badge');
#         if (!badge) continue;

#         const badgeText = (badge.textContent || '').trim();
#         if (badgeText !== '空') continue;

#         const dateText = (lbl ? (lbl.textContent || '') : '').trim();
#         // Ignore only when badge '空' is inside the block whose date includes dateStr
#         if (dateText.includes(dateStr)) continue;

#         // Otherwise: play sound
#         return true;
#       }
#       return false;
#     }
#     """
#     return container.locator("body").evaluate(js, date_str)

def container_has_blocks(container) -> bool:
    return container.locator("div.blocks").count() > 0


def run_check(start_url: str, username: str, password: str, ignored_dates: List[str]):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()

        page.goto(start_url, wait_until="domcontentloaded")

        # If the login entry is a link/button on the first page, click it here (optional).
        # Example: click a link containing ログイン if present:
        for i in range(min(page.locator("a[href]").count(), 50)):
            a = page.locator("a[href]").nth(i)
            txt = (a.inner_text() or "").strip()
            if "ログイン" in txt:
                a.click()
                break

        # --- Key part: wait for the iframe that actually contains the login form ---
        try:
            page.locator("#scroll iframe").first.wait_for(state="attached", timeout=30000)
        except PWTimeout:
            # Debug if iframe isn't attached where expected
            print("No #scroll iframe attached yet.")
            print("iframe count (anywhere):", page.locator("iframe").count())
            raise

        frame = page.frame_locator("#scroll iframe").first

        # Wait for the known input IDs *inside the iframe*
        frame.locator("#txtKyoushuuseiNO").wait_for(state="visible", timeout=30000)
        frame.locator("#txtPassword").wait_for(state="visible", timeout=30000)

        # Fill credentials
        frame.locator("#txtKyoushuuseiNO").fill(username)
        frame.locator("#txtPassword").fill(password)

        # Submit
        # submit_login(frame)

        # Click the authentication button inside the iframe
        frame.locator("#btnAuthentication").wait_for(state="visible", timeout=30000)
        frame.locator("#btnAuthentication").click()

        # Wait for post-login navigation/content
        page.wait_for_load_state("domcontentloaded")
        page.wait_for_timeout(1500)

        # Re-locate iframe AFTER login (important)
        page.locator("#scroll iframe").first.wait_for(state="attached", timeout=30000)
        frame = page.frame_locator("#scroll iframe").first

        menu_btn = frame.locator("#btnMenu_Kyoushuuyoyaku")

        # Debug: confirm it exists in the iframe
        print("menu_btn count =", menu_btn.count())

        menu_btn.wait_for(state="visible", timeout=30000)

        # Helpful for cases where element is present but not in viewport
        menu_btn.scroll_into_view_if_needed()

        # Click
        menu_btn.click()
        print("Clicked btnMenu_Kyoushuuyoyaku")
        # 1) Click menu button inside iframe

        page.wait_for_timeout(500)

        for attempt in range(1, RETRY_TIMES + 1):
            print(f"[attempt {attempt}] Looking for '空'...")

            # frame.locator("#txtKyoushuuseiNO").wait_for(state="attached", timeout=30000)
            # (If #txtKyoushuuseiNO is not present after login, remove that line.)
            # Always re-acquire the frame (DOM can change after navigation/clicks)
            page_frame = page.frame_locator("#scroll iframe").first

            # 1) Find badge and (optionally) play sound
            try:
                # badge = find_kara_bage_and_sound(frame)
                # print("Found '空' badge -> playing victory sound")
                # victory_sound()  # your Linux sound function
                if container_has_blocks(page_frame):
                    blocks = page_frame.locator("body").first.evaluate("""
                    () => Array.from(document.querySelectorAll('div.blocks')).map(b => ({
                        date: (b.querySelector('span.lbl')?.textContent || '').trim(),
                        badge: (b.querySelector('span.badge')?.textContent || '').trim()
                    }))
                    """)
                    print("Blocks on main (page_frame):", blocks)
                    print(f"Checking for '空' (ignoring {ignored_dates})...")

                    # sound = False
                    # if container_has_blocks(page_frame):
                    #     sound = should_sound_empty_outside_date(page_frame, ignore_dates)
                    # else:
                    #     # If blocks aren’t in main document, you’d need to also check iframe;
                    #     # but in your code page_frame is already the iframe, so this else is usually unnecessary.
                    #     sound = False
                    for item in blocks:
                        if item.get("badge") == "空" and item.get("date") not in ignored_dates:
                            send_notification(item.get('date'))
                            victory_sound()

                print(f"Waiting {WAIT_30S/1000:.0f}s, reloading, then retrying...")
                time.sleep(WAIT_30S / 1000)
            except PWTimeout:
                print("Did not find '空' within timeout. Stopping retries.")
                break

            # 2) Click btnTop then btnMenu_Kyoushuuyoyaku
            # (These clicks are done regardless of found/not found)
            week_btn = "next" if attempt % 2 == 1 else "previous"
            click_week(page_frame, week_btn)
            print(f"Clicked {week_btn}; waiting 30s...")
            page.wait_for_timeout(30_000)

            # Small wait; better if you can wait for a specific post-click selector
            page.wait_for_timeout(1500)

            # # Re-acquire frame after top navigation (often safer)
            # page_frame = page.frame_locator("#scroll iframe").first
            # click_in_frame(page_frame, "#btnMenu_Kyoushuuyoyaku")

            # Wait for menu page to load/render again
            # Replace this with a more specific wait if you can (recommended).
            # page.wait_for_timeout(1500)

        # Dump iframe HTML (where you clicked the menu)
        # FrameLocator -> extract DOM via evaluate()
        # iframe_html_saved = frame.locator("html").evaluate("el => el.outerHTML")

        context.close()
        browser.close()
