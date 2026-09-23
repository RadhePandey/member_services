from playwright.sync_api import Page

from pages.base_page import BasePage


class MemberSearchPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.member_search_input = page.locator(
            "//input[@placeholder='Search by Name or IC number...']"
        )

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
