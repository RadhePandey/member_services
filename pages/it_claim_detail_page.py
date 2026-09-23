from decimal import Decimal
import re

from playwright.sync_api import Page

from pages.base_page import BasePage


class ITClaimDetailPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.ict_amount_field = page.locator(
            "//*[normalize-space(.)='ICT - (Capital)']/following::input[1]"
        ).first
        self.digital_amount_field = page.locator(
            "//*[normalize-space(.)='Digital - (Revenue)']/following::input[1]"
        ).first
        self.note_editor = page.locator("[contenteditable='true']").last
        self.forward_user_dropdown = page.locator("select:visible").last
        self.forward_button = page.locator(
            "//*[@id='app']//button[normalize-space(.)='Forward']"
        ).last
        self.forward_template_modal = page.locator("div.sds-modal:visible").last

    def is_loaded(self):
        self.ict_amount_field.wait_for(state="visible", timeout=30000)
        return "/detail" in self.page.url.lower()

    def fill_distribution(self, ict_amount: str, digital_amount: str, claim_amount: str):
        ict = Decimal(ict_amount)
        digital = Decimal(digital_amount)
        claimed = Decimal(claim_amount)
        if ict <= 0 or digital <= 0:
            raise ValueError("ICT and Digital amounts must be greater than zero.")
        if ict >= claimed or digital >= claimed:
            raise ValueError("Each distribution amount must be less than the claim amount.")
        if ict + digital > claimed:
            raise ValueError("ICT plus Digital cannot exceed the claim amount.")
        self.log_step(
            f"Enter ICT amount INR {ict_amount} and Digital amount INR {digital_amount}"
        )
        self.ict_amount_field.fill(ict_amount)
        self.page.wait_for_timeout(1000)
        self.digital_amount_field.fill(digital_amount)
        self.page.wait_for_timeout(1000)
        self.validate_distribution(claim_amount)

    def validate_distribution(self, claim_amount: str):
        claimed = Decimal(claim_amount)
        ict_text = self.ict_amount_field.input_value().strip()
        digital_text = self.digital_amount_field.input_value().strip()
        if not ict_text or not digital_text:
            raise AssertionError("ICT and Digital amounts must not be empty.")
        ict = Decimal(ict_text)
        digital = Decimal(digital_text)
        if ict <= 0 or digital <= 0:
            raise AssertionError("ICT and Digital amounts must be greater than zero.")
        if ict >= claimed or digital >= claimed:
            raise AssertionError(
                "ICT and Digital amounts must be less than the claim amount."
            )
        if ict + digital > claimed:
            raise AssertionError(
                "ICT plus Digital cannot exceed the claim amount."
            )
        self.log_step(
            f"Validated ICT INR {ict_text} and Digital INR {digital_text} "
            f"against claim amount INR {claim_amount}"
        )

    def add_note(self, note: str):
        self.log_step("Add the claim note")
        self.note_editor.click()
        self.page.wait_for_timeout(1000)
        self.note_editor.fill(note)
        self.page.wait_for_timeout(1000)
        assert note in self.note_editor.inner_text(), "Claim note was not entered."

    def select_reviewer_and_forward(self, reviewer: str):
        self.select_user_and_forward(reviewer, "Add the Initiator note")

    def select_user_and_forward(self, user: str):
        self.log_step(f"Select user: {user}")
        self.forward_user_dropdown.select_option(label=user)
        self.page.wait_for_timeout(1000)
        self.log_step("Forward the claim to the selected user")
        self.forward_button.click()
        self.page.wait_for_timeout(1000)
        self.log_step("Review the Noting and Member templates")
        save_and_continue = self.page.locator(
            "button:visible"
        ).filter(has_text=re.compile(r"^\s*Save\s+and\s+Continue\s*$", re.IGNORECASE)).last
        save_and_continue.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(1000)
        save_and_continue.click()
        self.page.wait_for_timeout(1000)

        self.log_step("Confirm forwarding the claim")
        confirm_button = self.page.locator(
            "button:visible"
        ).filter(
            has_text=re.compile(
                r"^\s*(Confirm|Yes|Proceed|Confirm\s+Forward|Yes,\s*confirm\s*it!)\s*$",
                re.IGNORECASE,
            )
        ).last
        if confirm_button.count() == 0:
            visible_buttons = self.page.locator("button:visible").all_inner_texts()
            raise AssertionError(
                f"Forward confirmation button not found. Visible buttons: "
                f"{visible_buttons}"
            )
        confirm_button.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(1000)
        confirm_button.click()
        self.page.wait_for_url(
            re.compile(r"/(?:history|forwardedclaim)(?:[/?#]|$)"),
            timeout=30000,
        )
        self.log_step("Claim forwarding completed; forwarding result page opened")

    def approve_claim(self):
        review_approval_button = self.page.locator(
            '//span[text()="Review & Approve"]'
        )
        review_approval_button.wait_for(state="visible", timeout=10000)
        self.log_step("Click Review & Approve")
        self.page.wait_for_timeout(500)
        review_approval_button.click()
        self.page.wait_for_timeout(500)

        self.log_step("Save and Continue approval noting letter")
        save_and_continue = self.page.locator(
            '//span[text()="Save and Continue"]'
        )
        save_and_continue.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)
        save_and_continue.click()
        self.page.wait_for_timeout(500)

        self.log_step("Confirm approval submission")
        confirm_button = self.page.locator(
            '//button[text()="Yes, confirm it!"]'
        ).last
        confirm_button.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(500)
        confirm_button.click()
        self.page.wait_for_timeout(500)
        self.page.locator(
            "//*[contains(normalize-space(.), "
            "'Digital Signature Request Transaction Number')]"
        ).first.wait_for(state="visible", timeout=30000)
        self.log_step(
            "E-sign request sent to Sanchalan Setu; waiting for mobile approval"
        )

    def wait_for_approval_success(self):
        self.log_step(
            "Wait for Sanchalan Setu e-sign completion and approval confirmation"
        )
        success_message = self.page.locator(
            "//*[contains(normalize-space(.), "
            "'The claim has been approved successfully')]"
        ).first
        success_message.wait_for(state="visible", timeout=180000)
        self.page.wait_for_timeout(500)
        self.log_step("Claim approved successfully popup displayed")
        ok_button = self.page.locator(
            '//button[normalize-space(.)="OK"]'
        ).last
        ok_button.wait_for(state="visible", timeout=10000)
        ok_button.click()
        self.page.wait_for_timeout(500)

    def wait_for_esign_notification(self):
        notification = self.page.locator(
            "//*[contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
            "'e-sign') or contains(translate(normalize-space(.), "
            "'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), "
            "'esign') or contains(normalize-space(.), "
            "'Sanchalan Setu')]"
        ).first
        notification.wait_for(state="visible", timeout=30000)
        return notification.is_visible()

    def pull_back_claim(self):
        pull_back_button = self.page.get_by_role(
            "button", name=re.compile(r"^Pull Back$", re.IGNORECASE)
        )
        pull_back_button.wait_for(state="visible", timeout=10000)
        self.log_step("Click Pull Back for the claim")
        pull_back_button.click()

        confirmation_modal = self.page.locator("div.sds-modal:visible").last
        if confirmation_modal.is_visible():
            confirm_button = confirmation_modal.get_by_role(
                "button", name=re.compile(r"^Confirm$", re.IGNORECASE)
            )
            confirm_button.click()
        self.page.wait_for_timeout(1000)
