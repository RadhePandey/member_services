from pathlib import Path

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class MedicalClaimFormPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.form_heading = page.locator(
            "//h1[normalize-space(.)='Add a New Claim']"
        ).first
        self.claim_forms_section = page.locator(
            "xpath=//h2[normalize-space(.)='Upload Claim Forms']/ancestor::div[.//input[@type='file']][1]"
        )
        self.supporting_documents_section = page.locator(
            "xpath=//h2[normalize-space(.)='Upload Supporting Documents']/ancestor::div[.//input[@type='file']][1]"
        )
        self.confirmation_checkbox = page.locator("//input[@id='declaration']")
        self.preview_button = page.locator(
            "//*[@id='app']//button[normalize-space(.)='Preview']"
        )

    def is_loaded(self, member_name: str):
        self.form_heading.wait_for(state="visible", timeout=30000)
        expect(
            self.page.locator(f"//h2[contains(normalize-space(.), '{member_name}')]").first
        ).to_be_visible(timeout=10000)
        return "/medical/submit-new-claim" in self.page.url

    def _upload(self, section, file_path: str, label: str):
        self.log_step(f"Upload {label}: {Path(file_path).name}")
        section.locator("input[type='file']").set_input_files(file_path)
        # The section lists the file name once the upload has finished.
        expect(section).to_contain_text(Path(file_path).name, timeout=60000)
        self.page.wait_for_timeout(1000)

    def upload_claim_forms(self, file_path: str):
        self._upload(self.claim_forms_section, file_path, "the claim forms")

    def upload_supporting_documents(self, file_path: str):
        self._upload(
            self.supporting_documents_section, file_path, "the supporting documents"
        )

    def is_preview_enabled(self):
        return self.preview_button.is_enabled()

    def click_confirmation_checkbox(self):
        self.log_step("Click the confirmation checkbox")
        self.confirmation_checkbox.scroll_into_view_if_needed()
        self.page.wait_for_timeout(1000)
        if not self.confirmation_checkbox.is_checked():
            self.confirmation_checkbox.click(force=True)
        self.page.wait_for_timeout(1000)

    def open_preview(self):
        self.log_step("Open the claim Preview screen")
        expect(self.preview_button).to_be_enabled(timeout=10000)
        self.preview_button.click()
