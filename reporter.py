# reporter.py | Python 3.10+ | Playwright async

import asyncio
from playwright.async_api import async_playwright, TimeoutError as PWTimeout


async def report_facebook_profile(profile_url: str, cookies_path: str = "fb_cookies.json") -> dict:
    """
    Navigates to a Facebook profile and submits a report.

    Args:
        profile_url: Full Facebook profile URL (e.g. https://www.facebook.com/username)
        cookies_path: Path to saved Facebook session cookies (JSON)

    Returns:
        dict with keys: success (bool), message (str)
    """
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )

        # Load saved session
        try:
            await context.add_cookies(_load_cookies(cookies_path))
        except Exception as e:
            await browser.close()
            return {"success": False, "message": f"Cookie load failed: {e}"}

        page = await context.new_page()

        try:
            await page.goto(profile_url, wait_until="networkidle", timeout=30000)

            # Check if logged in
            if "login" in page.url.lower():
                return {"success": False, "message": "Session expired — re-export cookies"}

            # Click the 3-dot "More" button on profile
            # Facebook uses aria-label="More" on the overflow button
            more_btn = page.locator('[aria-label="More"]').first
            await more_btn.wait_for(state="visible", timeout=10000)
            await more_btn.click()

            await page.wait_for_timeout(800)

            # Click "Report profile" or "Report" in the dropdown
            report_option = page.get_by_role("menuitem", name="Report profile").first
            try:
                await report_option.wait_for(state="visible", timeout=5000)
            except PWTimeout:
                # Fallback: look for generic "Report"
                report_option = page.get_by_text("Report").first
                await report_option.wait_for(state="visible", timeout=5000)

            await report_option.click()
            await page.wait_for_timeout(1000)

            # Report dialog — select reason
            # "Pretending to be someone" / "Fake account" / "Something else"
            # We pick "Pretending to be someone" as default — adjust as needed
            reason_map = {
                "fake": "Pretending to be someone",
                "spam": "Spam",
                "harassment": "Bullying or harassment",
                "hate": "Hate speech",
                "other": "Something else",
            }
            chosen_reason = reason_map.get("fake")

            reason_btn = page.get_by_text(chosen_reason, exact=False).first
            try:
                await reason_btn.wait_for(state="visible", timeout=8000)
                await reason_btn.click()
            except PWTimeout:
                # Try clicking first available radio/option in dialog
                first_option = page.locator('div[role="dialog"] label').first
                await first_option.click()

            await page.wait_for_timeout(600)

            # Hit Next/Submit button
            for btn_text in ["Next", "Submit", "Send", "Continue"]:
                btn = page.get_by_role("button", name=btn_text).first
                try:
                    await btn.wait_for(state="visible", timeout=3000)
                    await btn.click()
                    await page.wait_for_timeout(500)
                except PWTimeout:
                    continue

            # Second "Next" if multi-step
            for _ in range(3):
                try:
                    next_btn = page.get_by_role("button", name="Next").first
                    await next_btn.wait_for(state="visible", timeout=2000)
                    await next_btn.click()
                    await page.wait_for_timeout(500)
                except PWTimeout:
                    break

            # Final submit / Done
            for btn_text in ["Submit", "Done", "Send"]:
                try:
                    btn = page.get_by_role("button", name=btn_text).first
                    await btn.wait_for(state="visible", timeout=3000)
                    await btn.click()
                    break
                except PWTimeout:
                    continue

            await page.wait_for_timeout(1500)
            return {"success": True, "message": "Report submitted successfully."}

        except PWTimeout:
            return {"success": False, "message": "Timeout — Facebook DOM may have changed"}
        except Exception as e:
            return {"success": False, "message": str(e)}
        finally:
            await browser.close()


def _load_cookies(path: str) -> list:
    import json
    with open(path, "r") as f:
        return json.load(f)


def run_report(profile_url: str) -> dict:
    return asyncio.run(report_facebook_profile(profile_url))
