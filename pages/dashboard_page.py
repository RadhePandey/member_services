import re

from playwright.sync_api import Page

from pages.base_page import BasePage


class DashboardPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.executive_dashboard = page.locator(
            "//*[normalize-space(.)='Executive Dashboard']"
        ).first
        self.member_onboarding = page.locator(
            "//*[normalize-space(.)='Member Onboarding']"
        ).first
        self.it_equipment_claims = page.locator(
            "//*[normalize-space(.)='IT Equipment Claims']"
        ).first
        self.profile_toggle = page.locator("button.rounded-full:visible").first
        self.logout_button = page.locator(
            "//*[normalize-space(.)='Logout']"
        ).first

    def is_loaded(self):
        return (
            "/dashboard" in self.page.url.lower()
            or self.executive_dashboard.is_visible()
        )

    def logout(self):
        self.log_step("Open the profile menu and log out")
        if self.profile_toggle.count() == 0:
            self.log_step("Profile menu unavailable; clear the browser session")
            self.page.context.clear_cookies()
            self.page.goto("https://test.rajyasabha.digital/login?login=email")
            self.page.wait_for_load_state("domcontentloaded")
            return
        self.profile_toggle.click()
        logout_button = self.page.locator("button:visible").filter(
            has_text=re.compile(
                r"^\s*(Logout|Log\s*out|Sign\s*out)\s*$", re.IGNORECASE
            )
        ).last
        if logout_button.count() == 0:
            self.log_step("Logout menu item unavailable; clear the browser session")
            self.page.context.clear_cookies()
            self.page.goto("https://test.rajyasabha.digital/login?login=email")
            self.page.wait_for_load_state("domcontentloaded")
            return
        logout_button.click()

    def open_it_equipment_claims(self):
        self.it_equipment_claims.click()
