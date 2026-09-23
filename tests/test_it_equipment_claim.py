import pytest
from playwright.sync_api import Page

from config import (
    APPROVER_EMAIL,
    INITIATOR_EMAIL,
    REVIEWER_EMAIL,
    TEST_OTP,
    BASE_URL,
)
from pages.dashboard_page import DashboardPage
from pages.it_claim_dashboard_page import ITClaimDashboardPage
from pages.it_claim_form_page import ITClaimFormPage
from pages.it_claim_detail_page import ITClaimDetailPage
from pages.it_claim_preview_page import ITClaimPreviewPage
from pages.login import LoginPage
from pages.member_search_page import MemberSearchPage
from test_data.it_claim_data import IT_CLAIM_DATA

VALID_INVOICE_NUMBER = "HPJBLRMD20260917440"
INITIATOR_OTP = "123456"


@pytest.mark.smoke
def test_user_can_submit_valid_it_equipment_claim(page: Page):
    member_name = "Radha Mohan Das Agrawal"
    invoice_number = VALID_INVOICE_NUMBER

    # Login: open the page, request an OTP, enter it, and reach the dashboard.
    LoginPage(page).open()
    LoginPage(page).login_with_otp(INITIATOR_EMAIL, INITIATOR_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()

    # Navigation: open a new claim and select the member who is submitting it.
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded(), "IT Claim Dashboard should be displayed"
    claim_dashboard.open_add_claim()

    member_search = MemberSearchPage(page)
    assert member_search.is_loaded(), "Member Search screen should be displayed"
    member_search.search_by_name(member_name)
    member_search.select_member(member_name)

    # Claim form: fill the fields and check the mandatory confirmation checkbox.
    claim_form = ITClaimFormPage(page)
    assert claim_form.is_loaded(), "IT Equipment Claim form should be displayed"
    claim_form.complete_claim(
        category=IT_CLAIM_DATA.category,
        quantity=IT_CLAIM_DATA.quantity,
        price_per_unit=IT_CLAIM_DATA.price_per_unit,
        invoice_number=invoice_number,
        description=IT_CLAIM_DATA.description,
    )
    claim_form.open_preview()

    # Preview and submission: verify the claim values before submitting.
    preview = ITClaimPreviewPage(page)
    assert preview.is_loaded(), "Claim Preview screen should be displayed"
    assert preview.contains_claim_value(invoice_number)
    assert preview.contains_claim_value(IT_CLAIM_DATA.category)
    preview.submit_claim()

    assert preview.is_submission_confirmed()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded(), (
        "Submitted claim should return to the IT Equipment Claims list "
        "for the Initiator"
    )
    claim_dashboard.open_latest_claim_assigned_to_me(
        member_name, expected_status="Submitted"
    )

    detail = ITClaimDetailPage(page)
    assert detail.is_loaded(), "Submitted claim detail should be displayed"
    detail.fill_distribution("1000", "1000", "3998")
    detail.add_note("Initiator review completed.")
    detail.select_user_and_forward("Prabhat Kiran SDS")

    page.wait_for_timeout(1000)
    print("[STEP] Afroj forwarding completed; preparing logout")
    page.goto(BASE_URL.replace("/login?login=email", "/dashboard"))
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)
    DashboardPage(page).logout()
    page.wait_for_timeout(1000)
    print("[STEP] Afroj logged out; login as Prabhat")
    LoginPage(page).open()
    LoginPage(page).login_with_otp(REVIEWER_EMAIL, INITIATOR_OTP)

    reviewer_dashboard = DashboardPage(page)
    page.wait_for_timeout(1000)
    reviewer_dashboard.open_it_equipment_claims()
    reviewer_claim_dashboard = ITClaimDashboardPage(page)
    assert reviewer_claim_dashboard.is_loaded()
    reviewer_claim_dashboard.open_latest_claim_assigned_to_me(
        member_name, expected_status="Initiated"
    )

    reviewer_detail = ITClaimDetailPage(page)
    assert reviewer_detail.is_loaded()
    reviewer_detail.validate_distribution("3998")
    reviewer_detail.add_note("Reviewer review completed.")
    reviewer_detail.select_user_and_forward("RadhePandey")


@pytest.mark.regression
def test_same_invoice_can_be_submitted_after_duplicate_alert(page: Page):
    LoginPage(page).open()
    LoginPage(page).login_with_otp(INITIATOR_EMAIL, TEST_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()

    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded(), "IT Claim Dashboard should be displayed"
    claim_dashboard.open_add_claim()

    member_search = MemberSearchPage(page)
    assert member_search.is_loaded(), "Member Search screen should be displayed"
    member_search.search_by_name(IT_CLAIM_DATA.member_name)
    member_search.select_member(IT_CLAIM_DATA.member_name)

    claim_form = ITClaimFormPage(page)
    assert claim_form.is_loaded(), "IT Equipment Claim form should be displayed"
    claim_form.enter_duplicate_invoice_claim(
        category=IT_CLAIM_DATA.category,
        quantity=IT_CLAIM_DATA.quantity,
        price_per_unit=IT_CLAIM_DATA.price_per_unit,
        invoice_number=VALID_INVOICE_NUMBER,
        description=IT_CLAIM_DATA.description,
    )

    claim_form.open_preview()
    preview = ITClaimPreviewPage(page)
    assert preview.is_loaded(), "Claim Preview screen should be displayed"
    assert preview.contains_claim_value(VALID_INVOICE_NUMBER)
    preview.submit_claim()
    assert preview.is_submission_confirmed()

    dashboard.logout()
    assert page.get_by_role("button", name="Send OTP").is_visible(), (
        "User should return to login page after logout"
    )


@pytest.mark.smoke
def test_initiator_forwards_radha_claim_to_radhe_pandey(page: Page):
    member_name = "Radha Mohan Das Agrawal"
    LoginPage(page).open()
    LoginPage(page).login_with_otp(INITIATOR_EMAIL, INITIATOR_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded()
    claim_dashboard.open_latest_claim_assigned_to_me(
        member_name, expected_status="Submitted"
    )

    detail = ITClaimDetailPage(page)
    assert detail.is_loaded()
    detail.fill_distribution("1000", "1000", "3998")
    detail.add_note("Initiator review completed.")
    detail.select_user_and_forward("Prabhat Kiran SDS")


@pytest.mark.smoke
def test_reviewer_forwards_claim_to_approver(page: Page):
    member_name = "Radha Mohan Das Agrawal"
    LoginPage(page).open()
    LoginPage(page).login_with_otp(REVIEWER_EMAIL, INITIATOR_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded()
    claim_dashboard.open_latest_claim_assigned_to_me(
        member_name, expected_status="Initiated"
    )

    reviewer_detail = ITClaimDetailPage(page)
    assert reviewer_detail.is_loaded()
    reviewer_detail.validate_distribution("3998")
    reviewer_detail.add_note("Reviewer review completed.")
    reviewer_detail.select_user_and_forward("RadhePandey")


@pytest.mark.smoke
def test_approver_starts_esign_approval(page: Page):
    member_name = "Radha Mohan Das Agrawal"
    LoginPage(page).open()
    LoginPage(page).login_with_otp(APPROVER_EMAIL, INITIATOR_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded()
    claim_dashboard.open_latest_claim_assigned_to_me(
        member_name, expected_status="Reviewed"
    )

    detail = ITClaimDetailPage(page)
    assert detail.is_loaded()
    detail.validate_distribution("3998")
    detail.add_note("Approver review completed.")
    detail.approve_claim()
    detail.wait_for_approval_success()


@pytest.mark.regression
def test_invoice_number_rejects_special_characters(page: Page):
    LoginPage(page).open()
    LoginPage(page).login_with_otp(INITIATOR_EMAIL, TEST_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()

    claim_dashboard = ITClaimDashboardPage(page)
    claim_dashboard.open_add_claim()

    member_search = MemberSearchPage(page)
    member_search.search_by_name(IT_CLAIM_DATA.member_name)
    member_search.select_member(IT_CLAIM_DATA.member_name)

    claim_form = ITClaimFormPage(page)
    claim_form.invoice_number_field.fill("invalid-invoice")
    claim_form.invoice_number_field.press("Tab")

    assert claim_form.is_invalid_invoice_number_visible(), (
        "Invoice number should reject special characters"
    )
