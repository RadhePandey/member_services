from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage


class MemberSearchPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.member_search_input = page.locator(
            "//input[@placeholder='Search by Name or IC number...']"
        )
        # Shown when the member's previous claim is not yet approved, paid
        # or rejected; a new claim cannot be submitted until it is settled.
        self.previous_claim_popup = page.locator(
            "//*[normalize-space(.)='Previous Claim Status']"
        ).first
        self.previous_claim_message = page.locator(
            "//*[contains(normalize-space(.), 'Previous claim is still under processed') and not(*)]"
        ).first

    def is_loaded(self):
        self.member_search_input.wait_for(state="visible", timeout=30000)
        return "/submit-new-claim" in self.page.url

    def search_by_name(self, member_name: str):
        self.log_step(f"Search for member: {member_name}")
        self.member_search_input.fill(member_name)
        self.page.wait_for_timeout(1000)

    def select_member(self, member_name: str):
        self.log_step(f"Select member: {member_name}")
        result = self.page.locator(
            f"xpath=(//*[@id='app']//*[contains(normalize-space(.), '{member_name}') and not(*)])[last()]"
        )
        result.wait_for(state="visible", timeout=30000)
        result.scroll_into_view_if_needed()
        clickable_card = result.locator(
            "xpath=ancestor::*[self::button or self::a or @role='button' or @tabindex or contains(concat(' ', normalize-space(@class), ' '), ' cursor-pointer ')][1]"
        )
        if clickable_card.count():
            clickable_card.click()
        else:
            result.click()

    def has_open_previous_claim(self, timeout: int = 5000):
        """Return True if the Previous Claim Status popup appears after the
        member is selected (the member already has an unsettled claim)."""
        self.log_step("Check whether the member has an unsettled previous claim")
        try:
            self.previous_claim_popup.wait_for(state="visible", timeout=timeout)
        except PlaywrightTimeoutError:
            self.log_step("No previous open claim; continue to the claim form")
            return False
        message = (
            self.previous_claim_message.inner_text()
            if self.previous_claim_message.count()
            else ""
        )
        self.log_step(f"Previous Claim Status popup displayed: {message}")
        return True
