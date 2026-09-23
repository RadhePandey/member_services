from playwright.sync_api import Page

from pages.base_page import BasePage


class ITClaimPreviewPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.heading = page.locator(
            "//*[normalize-space(.)='Claim Preview']"
        ).first
        self.submit_button = page.locator(
            "//*[@id='app']//button[normalize-space(.)='Submit']"
        ).first
        self.duplicate_invoice_alert = page.locator(
            "//*[normalize-space(.)='Duplicate Invoice Alert']"
        ).first
        self.duplicate_invoice_message = page.locator(
            "//*[contains(normalize-space(.), 'The invoice') and contains(normalize-space(.), 'is used in following claim')]"
        ).first
        self.alert_ok_button = page.locator(
            "//button[normalize-space(.)='OK']"
        ).first

    def is_loaded(self):
        return self.heading.is_visible()

    def contains_claim_value(self, value: str):
        return self.page.locator(
            f"//*[contains(normalize-space(.), '{value}')]"
        ).first.is_visible()

    def submit_claim(self):
        self.log_step("Submit the claim from the Preview screen")
        self.submit_button.click()
        self.log_step("Claim submitted; keep the result visible for 5 seconds")
        self.page.wait_for_timeout(5000)

    def is_submission_confirmed(self):
        return self.page.locator(
            "//*[normalize-space(.)='Claim Submitted' or normalize-space(.)='Submitted']"
        ).first.is_visible()

    def is_duplicate_invoice_alert_visible(self):
        self.duplicate_invoice_alert.wait_for(state="visible", timeout=30000)
        return self.duplicate_invoice_alert.is_visible()

    def duplicate_invoice_alert_contains(self, invoice_number: str):
        return self.duplicate_invoice_message.locator(
            f"xpath=..//*[contains(normalize-space(.), '{invoice_number}')]"
        ).first.is_visible()

    def dismiss_duplicate_invoice_alert(self):
        self.alert_ok_button.click()
