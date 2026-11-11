import re

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

    def open_latest_claim_assigned_to_me(
        self, member_name: str, expected_status: str
    ):
        """Open the member's claim with the given status and return its
        claim number. A member can only have one open claim at a time, so
        member + status identifies a single claim."""
        self.log_step(
            f"Open the latest claim for {member_name} in Assigned to Me"
            f" with status {expected_status}"
        )
        claim_rows = self._claim_rows(expected_status).filter(has_text=member_name)
        return self._open_claim_row(
            claim_rows,
            expected_status,
            f"No claim for {member_name} with status {expected_status} "
            f"in Assigned to Me",
        )

    def open_claim_by_number(self, claim_number: str, expected_status: str):
        """Open the claim with the given claim number (e.g. 000000002966)."""
        self.log_step(
            f"Open claim number {claim_number} in Assigned to Me"
            f" with status {expected_status}"
        )
        claim_rows = self._claim_rows(expected_status).filter(has_text=claim_number)
        return self._open_claim_row(
            claim_rows,
            expected_status,
            f"Claim number {claim_number} with status {expected_status} "
            f"is not in Assigned to Me",
        )

    def _claim_rows(self, expected_status: str):
        self.dismiss_blocking_notification()
        return self.page.locator("//*[@id='app']//tbody/tr").filter(
            has_text=expected_status
        )

    def _open_claim_row(self, claim_rows, expected_status: str, not_found: str):
        claim_row = claim_rows.first
        try:
            claim_row.wait_for(state="visible", timeout=30000)
        except PlaywrightTimeoutError:
            raise AssertionError(not_found) from None
        claim_number = self._claim_number_from_row(claim_row)
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
        self.log_step(
            f"Opened claim number {claim_number}; detail URL: {self.page.url}"
        )
        return claim_number

    def _claim_number_from_row(self, claim_row):
        match = re.search(r"\b\d{12}\b", claim_row.inner_text())
        assert match, f"Claim number not found in row: {claim_row.inner_text()}"
        return match.group(0)

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
