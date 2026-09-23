from playwright.sync_api import Page

from config import BASE_URL, QR_LOGIN_URL, TEST_EMAIL, TEST_OTP
from pages.base_page import BasePage


class LoginPage(BasePage):
    def __init__(self, page: Page):
        super().__init__(page)
        self.email_input = page.locator(
            "//input[@placeholder='example@sansad.nic.in']"
        )
        self.send_otp_button = page.locator(
            "//button[normalize-space(.)='Send OTP']"
        )
        self.otp_inputs = page.locator(
            "//input[not(@placeholder='example@sansad.nic.in') and (@autocomplete='one-time-code' or @inputmode='numeric' or @type='tel' or @type='text')]"
        )
        self.verify_otp_button = page.locator(
            "//button[normalize-space(.)='Verify OTP']"
        )
        self.resend_otp_button = page.locator(
            "//button[contains(translate(normalize-space(.), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'resend otp')]"
        )
        self.otp_rate_limit_message = page.locator(
            "//*[contains(normalize-space(.), 'You can only request an OTP once every 1 minute')]"
        ).first
        self.invalid_user_message = page.locator(
            "//*[contains(normalize-space(.), 'User details are missing or invalid user')]"
        ).first
        self.invalid_otp_message = page.locator(
            "//*[normalize-space(.)='The OTP you entered is incorrect. Please check and try again.']"
        )
        self.success_message = page.locator(
            "//*[normalize-space(.)='OTP verified successfully']"
        )
        self.qr_login_link = page.locator(
            "//*[normalize-space(.)='Sign-In with QR Code']"
        )

    def open(self):
        self.log_step("Open the email login page")
        self.page.goto(BASE_URL)
        self.page.wait_for_load_state("domcontentloaded")

    def open_qr_login(self):
        self.page.goto(QR_LOGIN_URL)
        self.page.wait_for_load_state("domcontentloaded")

    def is_qr_screen_loaded(self):
        self.page.locator(
            "//*[normalize-space(.)='Rajya Sabha Secretariat']"
        ).first.wait_for(
            state="visible", timeout=30000
        )
        self.page.locator("//canvas").wait_for(state="visible", timeout=30000)
        return "/login" in self.page.url and "login=email" not in self.page.url

    def enter_email(self, email: str = TEST_EMAIL):
        self.log_step(f"Enter login email: {email}")
        self.wait_for_visible(self.email_input)
        self.email_input.fill(email)

    def click_send_otp(self):
        self.log_step("Click Send OTP and wait for the OTP screen")
        self.wait_for_visible(self.send_otp_button)
        self.send_otp_button.click()
        self.page.wait_for_function(
            """() => document.querySelectorAll(
                'input[autocomplete="one-time-code"], input[inputmode="numeric"], input[type="tel"], input[type="text"]:not([placeholder="example@sansad.nic.in"])'
            ).length > 0
            || document.body.innerText.includes('You can only request an OTP once every 1 minute')
            || document.body.innerText.includes('User details are missing or invalid user')""",
            timeout=30000,
        )
        if self.otp_rate_limit_message.is_visible():
            raise AssertionError(
                "OTP request was rate-limited; wait 60 seconds before retrying."
            )
        if self.invalid_user_message.is_visible():
            raise AssertionError("Login user details are missing or invalid.")
        self.otp_inputs.first.wait_for(state="visible", timeout=30000)

    def is_resend_otp_disabled(self):
        self.resend_otp_button.wait_for(state="visible", timeout=30000)
        return self.resend_otp_button.is_disabled()

    def wait_for_resend_otp(self):
        self.resend_otp_button.wait_for(state="visible", timeout=30000)
        self.page.wait_for_function(
            """() => {
                const button = [...document.querySelectorAll('button')]
                    .find((element) => element.textContent.toLowerCase().includes('resend otp'));
                return button && !button.disabled;
            }""",
            timeout=65000,
        )

    def is_invalid_user_visible(self):
        self.invalid_user_message.wait_for(state="visible", timeout=30000)
        return self.invalid_user_message.is_visible()

    def is_otp_rate_limit_visible(self):
        self.otp_rate_limit_message.wait_for(state="visible", timeout=30000)
        return self.otp_rate_limit_message.is_visible()

    def enter_otp(self, otp: str = TEST_OTP):
        self.log_step("Enter the OTP one digit at a time")
        self.otp_inputs.first.wait_for(state="visible", timeout=30000)
        otp_digits = [digit for digit in str(otp)]
        for index, digit in enumerate(otp_digits):
            otp_field = self.otp_inputs.nth(index)
            self.wait_for_visible(otp_field)
            otp_field.fill(digit)

    def verify_otp(self):
        self.log_step("Click Verify OTP and wait for the dashboard")
        self.wait_for_visible(self.verify_otp_button)
        self.verify_otp_button.click()
        self.page.wait_for_url("**/dashboard", timeout=30000)

    def login_with_otp(self, email: str = TEST_EMAIL, otp: str = TEST_OTP):
        # This method combines the individual login steps used by the tests.
        self.enter_email(email)
        self.click_send_otp()
        self.enter_otp(otp)
        self.verify_otp()

    def is_invalid_otp_visible(self):
        self.invalid_otp_message.wait_for(state="visible", timeout=30000)
        return self.invalid_otp_message.is_visible()
