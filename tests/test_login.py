import pytest
from playwright.sync_api import Page

from config import TEST_EMAIL, TEST_INVALID_EMAIL, TEST_LOGIN_ALT_EMAIL, TEST_OTP
from pages.dashboard_page import DashboardPage
from pages.login import LoginPage


@pytest.mark.smoke
def test_user_can_login_with_valid_email_and_otp(page: Page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login_with_otp(TEST_EMAIL, TEST_OTP)

    dashboard_page = DashboardPage(page)
    assert dashboard_page.is_loaded(), "Dashboard should be visible after valid login"
    assert "/dashboard" in page.url.lower()
    page.wait_for_timeout(2000)


@pytest.mark.smoke
def test_qr_login_screen_is_displayed(page: Page):
    login_page = LoginPage(page)
    login_page.open_qr_login()

    assert login_page.is_qr_screen_loaded(), (
        "QR login screen should display the Rajya Sabha heading and QR code"
    )


@pytest.mark.regression
@pytest.mark.skipif(
    not TEST_LOGIN_ALT_EMAIL,
    reason="Requires a second valid login email to avoid OTP resend throttling.",
)
def test_user_sees_invalid_otp_error(page: Page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.enter_email(TEST_LOGIN_ALT_EMAIL)
    login_page.click_send_otp()
    login_page.enter_otp("000000")
    login_page.verify_otp()

    assert login_page.is_invalid_otp_visible(), (
        "Invalid OTP message should be visible for incorrect OTP"
    )


@pytest.mark.regression
@pytest.mark.skipif(
    not TEST_INVALID_EMAIL,
    reason="Requires TEST_INVALID_EMAIL to verify invalid-user validation.",
)
def test_user_sees_invalid_user_error(page: Page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.enter_email(TEST_INVALID_EMAIL)
    login_page.click_send_otp()

    assert login_page.is_invalid_user_visible(), (
        "Invalid-user message should be visible for an unknown user"
    )


@pytest.mark.sanity
@pytest.mark.skipif(
    not TEST_LOGIN_ALT_EMAIL,
    reason="Requires a second valid login email to avoid OTP resend throttling.",
)
def test_user_can_logout_after_login(page: Page):
    login_page = LoginPage(page)
    login_page.open()
    login_page.login_with_otp(TEST_LOGIN_ALT_EMAIL, TEST_OTP)

    dashboard_page = DashboardPage(page)
    assert dashboard_page.is_loaded(), "Dashboard should load before logout"

    dashboard_page.logout()
    assert page.get_by_role("button", name="Send OTP").is_visible(), (
        "User should return to login page after logout"
    )