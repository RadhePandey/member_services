from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


class ITClaimDashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)

        self.heading = page.locator(
            "//*[normalize-space(text())='IT Equipment Claims']"
        ).first
        self.add_claim_link = page.locator(
            "//*[@id='app']//*[self::a or self::button][contains(normalize-space(.), 'Add Claim')]"
        ).first
        self.claim_rejected_popup = page.locator(
            "//h2[@id='swal2-title' and normalize-space(.)='Claim Rejected']"
        ).first
        self.popup_ok_button = self.claim_rejected_popup.locator(
            "xpath=ancestor::div[contains(@class, 'swal2-popup')]"
        ).get_by_role("button", name="OK")

    def is_loaded(self):
        self.heading.wait_for(state="visible", timeout=30000)
        return self.heading.is_visible()

    def open_add_claim(self):
        self.log_step("Click Add Claim")
        self.add_claim_link.click()

    def open_claim_for_member(self, member_name: str):
        self.log_step(f"Open latest submitted claim for member: {member_name}")
        self.dismiss_blocking_notification()
        claim_rows = self.page.locator("xpath=//*[@id='app']//tr").filter(
            has_text=member_name
        ).filter(has_text="Submitted")
        claim_row = claim_rows.first
        claim_row.wait_for(state="visible", timeout=30000)
        status_cell = claim_row.locator(
            "xpath=.//span[normalize-space(.)='Submitted']/ancestor::td[1]"
        )
        assert status_cell.inner_text().strip() == "Submitted", (
            f"Expected claim status Submitted, found: {status_cell.inner_text().strip()}"
        )
        status_cell.hover()
        open_button = status_cell.get_by_role("button", name="Open")
        open_button.wait_for(state="visible", timeout=10000)
        open_button.click(force=True)
        self.page.wait_for_timeout(1000)
        self.log_step(f"Claim detail URL after opening: {self.page.url}")

    def open_latest_claim_assigned_to_me(
        self, member_name: str, expected_status: str
    ):
        status_description = (
            f" with status {expected_status}" if expected_status else ""
        )
        self.log_step(
            f"Open the latest claim for {member_name} in Assigned to Me"
            f"{status_description}"
        )
        self.dismiss_blocking_notification()
        all_rows = self.page.locator("//*[@id='app']//tbody/tr")
        claim_rows = all_rows.filter(
            has_text=member_name
        ).filter(has_text=expected_status)
        if claim_rows.count() == 0:
            self.log_step(
                f"Member text is not shown; open the top Assigned to Me "
                f"claim with status {expected_status}"
            )
            claim_rows = all_rows.filter(has_text=expected_status)
        claim_row = claim_rows.first
        claim_row.wait_for(state="visible", timeout=30000)
        status_cell = claim_row.locator(
            f"xpath=.//span[normalize-space(.)='{expected_status}']/ancestor::td[1]"
        )
        status_text = status_cell.locator(
            f"xpath=.//span[normalize-space(.)='{expected_status}']"
        ).inner_text().strip()
        assert status_text == expected_status, (
            f"Expected claim status {expected_status}, found: {status_text}"
        )
        claim_row.hover(force=True)
        open_button = status_cell.get_by_role("button", name="Open").first
        open_button.wait_for(state="visible", timeout=10000)
        open_button.click(force=True)
        self.page.wait_for_timeout(1000)
        self.log_step(f"Claim detail URL after opening: {self.page.url}")

    def open_first_claim_assigned_to_me(self, expected_status: str = None):
        """Compatibility wrapper for callers that do not have member criteria."""
        self.log_step(f"Open the first claim in Assigned to Me with status {expected_status}")
        self.dismiss_blocking_notification()
        claim_rows = self.page.locator("//*[@id='app']//tbody/tr")
        if expected_status:
            claim_rows = claim_rows.filter(has_text=expected_status)
        claim_row = claim_rows.last if expected_status else claim_rows.first
        claim_row.wait_for(state="visible", timeout=30000)
        claim_row.hover(force=True)
        open_button = claim_row.get_by_role("button", name="Open").first
        open_button.wait_for(state="visible", timeout=10000)
        open_button.click(force=True)
        self.page.wait_for_timeout(1000)
        self.log_step(f"Claim detail URL after opening: {self.page.url}")

    def dismiss_blocking_notification(self):
        if self.claim_rejected_popup.is_visible():
            self.log_step("Dismiss the Claim Rejected notification")
            try:
                self.popup_ok_button.click(force=True, timeout=5000)
            except PlaywrightTimeoutError:
                # The alert can auto-close while the dashboard refreshes.
                if self.claim_rejected_popup.is_visible():
                    raise
            if self.claim_rejected_popup.is_visible():
                self.claim_rejected_popup.wait_for(state="hidden", timeout=10000)
