import re

from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


class MedicalClaimDashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # The left sidebar is collapsed; hovering it shows the menu labels.
        self.sidebar_claims_menu = page.locator(
            "div.text-box", has_text=re.compile(r"^\s*Claims\s*$")
        ).first
        self.sidebar_medical_claim_link = page.locator(
            "a[href='/rssms/claims/medical']"
        ).first
        self.heading = page.locator(
            "//*[@id='app']//*[normalize-space(text())='Medical Claims']"
        ).first
        self.add_claim_link = page.locator(
            "//*[@id='app']//*[self::a or self::button][contains(normalize-space(.), 'Add Claim')]"
        ).first
        self.claim_rows = page.locator("//*[@id='app']//tbody/tr")

    def open_from_sidebar(self):
        self.log_step("Hover the side menu to expand it")
        self.page.mouse.move(40, 400)
        self.page.wait_for_timeout(1000)
        self.sidebar_claims_menu.wait_for(state="visible", timeout=10000)
        self.log_step("Click Claims in the side menu")
        self.sidebar_claims_menu.click()
        self.page.wait_for_timeout(1000)
        self.log_step("Click Medical Claim")
        self.sidebar_medical_claim_link.click()
        self.page.wait_for_url("**/rssms/claims/medical", timeout=30000)
        # Move the mouse off the sidebar so it collapses again.
        self.page.mouse.move(1000, 400)
        self.page.wait_for_timeout(1000)

    def is_loaded(self):
        self.heading.wait_for(state="visible", timeout=30000)
        return self.page.url.rstrip("/").endswith("/rssms/claims/medical")

    def open_add_claim(self):
        self.log_step("Click Add Claim")
        self.add_claim_link.click()

    def open_claim_by_number(
        self, claim_number: str, expected_status: str, for_approval: bool = False
    ):
        if for_approval:
            # Worded so the report files it under "Claim Approved".
            self.log_step(
                f"Open claim number {claim_number} for approval "
                f"(current status: {expected_status})"
            )
        else:
            self.log_step(
                f"Open claim number {claim_number} in Assigned to Me"
                f" with status {expected_status}"
            )
        claim_row = self.claim_rows.filter(has_text=claim_number).filter(
            has_text=expected_status
        ).first
        try:
            claim_row.wait_for(state="visible", timeout=30000)
        except PlaywrightTimeoutError:
            raise AssertionError(
                f"Claim number {claim_number} with status {expected_status} "
                f"is not in Assigned to Me"
            ) from None
        status_cell = claim_row.locator(
            f"xpath=.//span[normalize-space(.)='{expected_status}']/ancestor::td[1]"
        )
        claim_row.hover(force=True)
        open_button = status_cell.get_by_role("button", name="Open").first
        open_button.wait_for(state="visible", timeout=10000)
        open_button.click(force=True)
        self.page.wait_for_timeout(1000)
        self.log_step(f"Opened claim number {claim_number}; detail URL: {self.page.url}")

    def visible_claim_numbers(self):
        """Claim numbers (e.g. 000000002980) shown in the Assigned to Me list."""
        try:
            self.claim_rows.first.wait_for(state="visible", timeout=30000)
        except PlaywrightTimeoutError:
            return set()
        return set(re.findall(r"\b\d{12}\b", " ".join(self.claim_rows.all_inner_texts())))

    def find_new_claim_number(self, member_name: str, expected_status: str, known_numbers):
        """Return the number of the member's claim with the given status that
        was not in the list before. Several claims can be open for a member
        at once, so the new one is told apart from the earlier ones."""
        self.log_step(
            f"Find the new {expected_status} claim for {member_name} "
            f"in Assigned to Me"
        )
        rows = self.claim_rows.filter(has_text=member_name).filter(
            has_text=expected_status
        )
        rows.first.wait_for(state="visible", timeout=30000)
        for row_text in rows.all_inner_texts():
            match = re.search(r"\b\d{12}\b", row_text)
            if match and match.group(0) not in known_numbers:
                self.log_step(f"New claim number: {match.group(0)}")
                return match.group(0)
        raise AssertionError(
            f"No new {expected_status} claim for {member_name} in Assigned to Me"
        )
