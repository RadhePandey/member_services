from decimal import Decimal
import re

from playwright.sync_api import Page, expect

from pages.base_page import BasePage


class MedicalClaimDetailPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        # "Initiator Medical Claim" or "Approver Medical Claim" by user role.
        self.heading_xpath = "//*[@id='app']//*[normalize-space(text())='{role} Medical Claim']"
        self.claimed_amount_field = page.locator("#claimed_amount")
        self.payable_amount_field = page.locator("#payable_amount")
        self.details_section = page.locator(
            "xpath=//*[normalize-space(.)='Details']/ancestor::div[.//input[@id='claimed_amount']][1]"
        )
        self.note_editor = page.locator("[contenteditable='true']").last
        self.forward_user_dropdown = page.locator("select:visible").last
        self.forward_button = page.locator(
            "//*[@id='app']//button[normalize-space(.)='Forward']"
        ).last

    def is_loaded(self, claim_number: str, role: str = "Initiator"):
        self.page.locator(self.heading_xpath.format(role=role)).first.wait_for(
            state="visible", timeout=30000
        )
        expect(self.page.locator("#app")).to_contain_text(claim_number, timeout=30000)
        return "/medical/detail/" in self.page.url

    def validate_saved_amounts(self, claimed_amount: str, payable_amount: str):
        # Amounts entered by the Initiator are shown to the next user.
        self.log_step("Check the claimed and payable amounts entered by the Initiator")
        expect(self.claimed_amount_field).to_have_value(claimed_amount, timeout=30000)
        expect(self.payable_amount_field).to_have_value(payable_amount, timeout=30000)
        self.validate_amount_summary(claimed_amount, payable_amount)

    def validate_previous_note(self, note: str, author: str):
        self.log_step(f"Check the note added by {author}")
        note_section = self.page.locator(
            "xpath=//*[normalize-space(.)='Note']/parent::*"
        ).first
        expect(note_section).to_contain_text(note, timeout=10000)
        expect(note_section).to_contain_text(author, timeout=10000)
        self.log_step(f"Note from {author} displayed: {note}")

    def enter_amounts(self, claimed_amount: str, payable_amount: str):
        if Decimal(payable_amount) > Decimal(claimed_amount):
            raise ValueError("Payable amount must not exceed the claimed amount.")
        self.log_step(f"Enter claimed amount INR {claimed_amount}")
        self.claimed_amount_field.fill(claimed_amount)
        self.page.wait_for_timeout(1000)
        self.log_step(f"Enter payable amount INR {payable_amount}")
        self.payable_amount_field.fill(payable_amount)
        self.page.wait_for_timeout(1000)

    def validate_amount_summary(self, claimed_amount: str, payable_amount: str):
        # The entered amounts are reflected in the "Claimed Amount" and
        # "Payable Amount" summary above the input fields.
        for label, amount in (("Claimed Amount", claimed_amount), ("Payable Amount", payable_amount)):
            expected = f"₹{Decimal(amount):,.2f}"
            expect(
                self.details_section.locator(
                    f"xpath=.//*[normalize-space(.)='{label}:']/following::*[normalize-space(.)='{expected}'][1]"
                )
            ).to_be_visible(timeout=10000)
        self.log_step(
            f"Validated summary: Claimed Amount INR {claimed_amount}, "
            f"Payable Amount INR {payable_amount}"
        )

    def add_note(self, note: str):
        self.log_step("Add the claim note")
        # The editor can re-render while the claim loads and drop the typed
        # text, so type the note a second time if it did not stick.
        for _ in range(2):
            self.note_editor.click()
            self.page.wait_for_timeout(1000)
            self.note_editor.fill(note)
            self.page.wait_for_timeout(1000)
            if note in self.note_editor.inner_text():
                break
        assert note in self.note_editor.inner_text(), "Claim note was not entered."

    def select_user_and_forward(self, user: str):
        self.log_step(f"Select user: {user}")
        self.forward_user_dropdown.select_option(label=user)
        self.page.wait_for_timeout(1000)
        self.log_step("Forward the claim to the selected user")
        self.forward_button.click()
        self.page.wait_for_timeout(1000)

        self.log_step("Review the Noting letter")
        save_and_continue = self.page.locator("button:visible").filter(
            has_text=re.compile(r"^\s*Save\s+and\s+Continue\s*$", re.IGNORECASE)
        ).last
        # The app may refuse to forward with an error popup instead of
        # opening the Noting letter; report its message if so.
        error_popup = self.page.locator("div.swal2-popup.swal2-icon-error:visible")
        save_and_continue.or_(error_popup).first.wait_for(state="visible", timeout=15000)
        if error_popup.count():
            message = error_popup.locator(".swal2-html-container").inner_text()
            raise AssertionError(f"Application refused to forward the claim: {message}")
        save_and_continue.scroll_into_view_if_needed()
        self.page.wait_for_timeout(1000)
        save_and_continue.click()
        self.page.wait_for_timeout(1000)

        self.log_step("Confirm forwarding the claim")
        confirm_button = self.page.locator("button:visible").filter(
            has_text=re.compile(r"^\s*Yes,\s*confirm\s*it!\s*$", re.IGNORECASE)
        ).last
        confirm_button.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(1000)
        confirm_button.click()
        self.page.wait_for_timeout(1000)

        success_message = self.page.locator(
            "//*[normalize-space(.)='The claim has been forwarded successfully']"
        ).first
        success_message.wait_for(state="visible", timeout=30000)
        self.log_step("Claim forwarded successfully message displayed")
        self.page.wait_for_timeout(1500)
        self.page.locator("//button[normalize-space(.)='OK']").last.click()
        self.page.wait_for_timeout(1000)

    def approve_claim(self):
        esign_approve_button = self.page.locator(
            "//*[@id='app']//button[normalize-space(.)='E-Sign & Approve']"
        ).first
        esign_approve_button.wait_for(state="visible", timeout=10000)
        self.log_step("Click E-Sign & Approve")
        self.page.wait_for_timeout(500)
        esign_approve_button.click()
        self.page.wait_for_timeout(500)

        self.log_step("Save and Continue approval noting letter")
        save_and_continue = self.page.locator("button:visible").filter(
            has_text=re.compile(r"^\s*Save\s+and\s+Continue\s*$", re.IGNORECASE)
        ).last
        save_and_continue.wait_for(state="visible", timeout=15000)
        save_and_continue.scroll_into_view_if_needed()
        self.page.wait_for_timeout(500)
        save_and_continue.click()
        self.page.wait_for_timeout(500)

        self.log_step("Confirm approval submission")
        confirm_button = self.page.locator("button:visible").filter(
            has_text=re.compile(r"^\s*Yes,\s*confirm\s*it!\s*$", re.IGNORECASE)
        ).last
        confirm_button.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)
        confirm_button.click()
        self.page.wait_for_timeout(500)
        self.page.locator(
            "//*[contains(normalize-space(.), 'Digital Signature Request Transaction Number')]"
        ).first.wait_for(state="visible", timeout=30000)
        self.log_step("E-sign request sent to Sanchalan Setu; waiting for mobile approval")

    def wait_for_approval_success(self):
        self.log_step(
            "Wait for Sanchalan Setu e-sign completion and approval confirmation"
        )
        # Match only the visible popup; the notification panel holds hidden
        # "...approved successfully" texts for other claims.
        success_message = self.page.locator(
            "div.swal2-popup:visible #swal2-html-container",
            has_text="The claim has been approved successfully",
        )
        success_message.wait_for(state="visible", timeout=180000)
        # Let the popup finish opening before clicking OK.
        self.page.wait_for_timeout(1500)
        self.log_step(f"Claim approved successfully popup displayed: {success_message.inner_text()}")
        ok_button = self.page.locator("//button[normalize-space(.)='OK']").last
        ok_button.wait_for(state="visible", timeout=10000)
        ok_button.click()
        self.page.wait_for_timeout(500)
