from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class MedicalClaimPreviewPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # The preview section is in the page (hidden) while the form is shown,
        # so every check here targets the visible preview section only.
        self.heading = page.locator("//h1[normalize-space(.)='Claim Preview']").first
        self.section = page.locator(
            "xpath=//h1[normalize-space(.)='Claim Preview']/ancestor::div[.//button[normalize-space(.)='Submit']][1]"
        )
        self.submit_button = self.section.locator(
            "xpath=.//button[normalize-space(.)='Submit']"
        )
        self.success_toast = page.locator(
            "//*[normalize-space(.)='Claim submitted successfully']"
        ).first

    def is_loaded(self):
        self.heading.wait_for(state="visible", timeout=30000)
        return self.heading.is_visible()

    def contains(self, value: str):
        expect(self.section).to_contain_text(value, timeout=10000)
        return True

    def submit_claim(self):
        self.log_step("Submit the claim from the Preview screen")
        self.submit_button.click()

    def is_submission_confirmed(self):
        self.success_toast.wait_for(state="visible", timeout=30000)
        self.log_step("Claim submitted successfully message displayed")
        self.page.wait_for_timeout(3000)
        return True
