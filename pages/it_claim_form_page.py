from playwright.sync_api import Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from config import IT_CLAIM_INVOICE_IMAGE, IT_CLAIM_INVOICE_PDF
from pages.base_page import BasePage


class ITClaimFormPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.claim_detail_heading = page.locator(
            "//*[normalize-space(.)='Claim Detail']"
        ).first
        self.form_heading = page.locator(
            "//*[normalize-space(.)='Add New Claim']"
        ).first
        self.file_input = page.locator(
            "(//*[@id='app']//input[@type='file'])[1]"
        )
        self.category_field = page.locator(
            "//input[@placeholder='Enter Category name']"
        )
        self.quantity_field = page.locator(
            "(//input[@type='number'])[1]"
        )
        self.price_field = page.locator(
            "(//input[@type='number'])[2]"
        )
        self.description_field = page.locator(
            "//textarea[@placeholder='Enter description'] | //input[@placeholder='Enter description']"
        )
        self.invoice_number_field = page.locator(
            "//input[@placeholder='Enter invoice number']"
        )
        self.invoice_number_validation_message = page.locator(
            "//*[contains(normalize-space(.), 'invoice number can only be alpha numeric')]"
        ).first
        self.invoice_date_field = page.locator(
            "(//*[normalize-space(.)='Invoice Date']/..//input[@readonly])[1]"
        )
        self.confirmation_checkbox = page.locator(
            "//input[@id='declaration']"
        )
        self.preview_button = page.locator(
            "//*[@id='app']//button[normalize-space(.)='Preview']"
        )
        self.duplicate_invoice_alert = page.locator(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' swal2-popup ')]//*[normalize-space(.)='Duplicate Invoice Alert']"
        ).first
        self.duplicate_invoice_message = page.locator(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' swal2-popup ')]//*[contains(normalize-space(.), 'The invoice') and contains(normalize-space(.), 'is used in following claim')]"
        ).first
        self.alert_ok_button = page.locator(
            "//div[contains(concat(' ', normalize-space(@class), ' '), ' swal2-popup ')]//button[normalize-space(.)='OK']"
        ).first

    def is_loaded(self):
        self.form_heading.wait_for(state="visible", timeout=30000)
        return "/submit-new-claim" in self.page.url

    def upload_invoice_files(self):
        self.log_step("Upload the invoice files")
        self.file_input.wait_for(state="attached", timeout=60000)
        self.file_input.set_input_files(
            [IT_CLAIM_INVOICE_PDF, IT_CLAIM_INVOICE_IMAGE]
        )
        self.page.wait_for_function(
            "() => (document.body.innerText.match(/Uploaded/g) || []).length >= 2",
            timeout=60000,
        )
        self.page.wait_for_timeout(1000)

    def complete_claim(
        self,
        category: str,
        quantity: str = "2",
        price_per_unit: str = "1999",
        invoice_number: str = "test123",
        description: str = "Test IT equipment claim",
    ):
        # Fill every required field before trying to open the Preview screen.
        self.log_step("Complete the claim form fields")
        self.upload_invoice_files()
        self.category_field.locator("..").click()
        self.category_field.fill(category)
        self.page.wait_for_timeout(500)
        self.page.keyboard.press("ArrowDown")
        self.page.keyboard.press("Enter")
        self.log_step(
            f"Category value after selection: {self.category_field.input_value()}"
        )
        self.quantity_field.fill(quantity)
        self.quantity_field.press("Tab")
        self.price_field.fill(price_per_unit)
        self.price_field.press("Tab")
        self.description_field.fill(description)
        self.description_field.press("Tab")
        self.invoice_number_field.fill(invoice_number)
        self.invoice_number_field.press("Tab")
        self.page.wait_for_timeout(1000)
        self.handle_duplicate_invoice_alert_if_present()
        self.invoice_date_field.click()
        self.page.wait_for_timeout(1000)
        if self.duplicate_invoice_alert.is_visible():
            self.handle_duplicate_invoice_alert()
            raise AssertionError(
                f"Cannot continue: invoice number '{invoice_number}' is already used."
            )
        self.page.locator(
            "(//*[contains(concat(' ', normalize-space(@class), ' '), ' flatpickr-day ') and contains(concat(' ', normalize-space(@class), ' '), ' today ') and not(contains(concat(' ', normalize-space(@class), ' '), ' disabled '))])[last()]"
        ).click()
        self.page.wait_for_function(
            r"""() => {
                const text = document.querySelector('#app')?.innerText || '';
                return /Total Amount:\s*₹(?!0(?:\.00)?\b)[\d,]+(?:\.\d{2})?/.test(text);
            }""",
            timeout=10000,
        )
        self.log_step(
            "Claim amount is non-zero; checkbox and Preview validation will run next"
        )
        self.log_step("Click the mandatory confirmation checkbox")
        self.click_confirmation_checkbox()
        assert self.confirmation_checkbox.is_checked(), (
            "Claim confirmation checkbox should be checked"
        )
        self.preview_button.wait_for(state="visible")
        self.page.wait_for_function(
            r"""() => {
                const button = [...document.querySelectorAll('#app button')]
                    .find((element) => element.textContent.trim() === 'Preview');
                return button && !button.disabled;
            }""",
            timeout=10000,
        )

    def click_confirmation_checkbox(self):
        # Click the declaration control after every required form field is filled.
        self.confirmation_checkbox.scroll_into_view_if_needed()
        self.log_step("Scrolled to the confirmation checkbox; inspect it before clicking")
        self.page.wait_for_timeout(1500)
        if not self.confirmation_checkbox.is_checked():
            self.confirmation_checkbox.click(force=True)
        self.log_step(
            "Checkbox checked: "
            f"{self.confirmation_checkbox.is_checked()}; "
            f"Preview disabled: {self.preview_button.is_disabled()}"
        )
        self.page.wait_for_timeout(1500)

    def enter_duplicate_invoice_claim(
        self,
        category: str,
        quantity: str = "2",
        price_per_unit: str = "1999",
        invoice_number: str = "test123",
        description: str = "Test IT equipment claim",
    ):
        self.upload_invoice_files()
        self.category_field.locator("..").click()
        self.category_field.fill(category)
        self.page.keyboard.press("Enter")
        self.quantity_field.fill(quantity)
        self.price_field.fill(price_per_unit)
        self.description_field.fill(description)
        self.invoice_number_field.fill(invoice_number)
        self.invoice_number_field.press("Tab")
        self.page.wait_for_timeout(2000)
        self.handle_duplicate_invoice_alert_if_present()
        self.invoice_date_field.click()
        self.page.wait_for_timeout(1000)
        self.page.locator(
            "(//*[contains(concat(' ', normalize-space(@class), ' '), ' flatpickr-day ') and contains(concat(' ', normalize-space(@class), ' '), ' today ') and not(contains(concat(' ', normalize-space(@class), ' '), ' disabled '))])[last()]"
        ).click()
        self.page.wait_for_function(
            r"""() => {
                const text = document.querySelector('#app')?.innerText || '';
                return /Total Amount:\s*₹(?!0(?:\.00)?\b)[\d,]+(?:\.\d{2})?/.test(text);
            }""",
            timeout=10000,
        )
        self.click_confirmation_checkbox()
        assert self.confirmation_checkbox.is_checked(), (
            "Claim confirmation checkbox should be checked"
        )
        self.page.wait_for_function(
            """() => {
                const button = [...document.querySelectorAll('#app button')]
                    .find((element) => element.textContent.trim() === 'Preview');
                return button && !button.disabled;
            }""",
            timeout=10000,
        )

    def is_duplicate_invoice_alert_visible(self):
        self.duplicate_invoice_alert.wait_for(state="visible", timeout=30000)
        return self.duplicate_invoice_alert.is_visible()

    def handle_duplicate_invoice_alert_if_present(self):
        try:
            self.duplicate_invoice_alert.wait_for(state="visible", timeout=2000)
        except PlaywrightTimeoutError:
            self.log_step("No duplicate invoice popup appeared; continue the form")
            return False
        self.handle_duplicate_invoice_alert()
        self.log_step("Duplicate invoice accepted; continue the claim form")
        return True

    def handle_duplicate_invoice_alert(self):
        self.duplicate_invoice_alert.wait_for(state="visible", timeout=30000)
        message = self.duplicate_invoice_message.inner_text()
        self.log_step(f"Duplicate invoice alert displayed: {message}")
        self.dismiss_duplicate_invoice_alert()
        self.duplicate_invoice_alert.wait_for(state="hidden", timeout=10000)

    def is_invalid_invoice_number_visible(self):
        self.invoice_number_validation_message.wait_for(
            state="visible", timeout=10000
        )
        return self.invoice_number_validation_message.is_visible()

    def duplicate_invoice_alert_contains(self, invoice_number: str):
        return self.duplicate_invoice_message.locator(
            f"xpath=..//*[contains(normalize-space(.), '{invoice_number}')]"
        ).first.is_visible()

    def dismiss_duplicate_invoice_alert(self):
        self.alert_ok_button.click()

    def open_preview(self):
        self.log_step("Open the claim Preview screen")
        self.preview_button.click()
