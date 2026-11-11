from pathlib import Path

import pytest
from playwright.sync_api import Page

from config import (
    ESIGN_APPROVAL,
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

# Claim number of the claim currently moving through the flow. Stage 2
# (approval) runs as a separate pytest invocation, so it is kept on disk.
CLAIM_NUMBER_FILE = (
    Path(__file__).resolve().parents[1] / "reports" / ".it_claim_number.txt"
)


def _save_claim_number(claim_number: str):
    CLAIM_NUMBER_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLAIM_NUMBER_FILE.write_text(claim_number, encoding="utf-8")


def _open_tracked_claim(claim_dashboard: ITClaimDashboardPage, expected_status: str):
    """Open the claim started by the Initiator; fall back to the member's
    claim with that status when no claim number has been recorded."""
    if CLAIM_NUMBER_FILE.exists():
        claim_number = CLAIM_NUMBER_FILE.read_text(encoding="utf-8").strip()
        return claim_dashboard.open_claim_by_number(claim_number, expected_status)
    return claim_dashboard.open_latest_claim_assigned_to_me(
        IT_CLAIM_DATA.member_name, expected_status=expected_status
    )


def _assert_no_open_previous_claim(member_search: MemberSearchPage):
    assert not member_search.has_open_previous_claim(), (
        f"{IT_CLAIM_DATA.member_name} has an unsettled previous claim; a new "
        f"claim can be submitted once it is approved, paid or rejected."
    )


@pytest.mark.smoke
def test_user_can_submit_valid_it_equipment_claim(page: Page):
    member_name = IT_CLAIM_DATA.member_name
    invoice_number = IT_CLAIM_DATA.invoice_number

    # Login: open the page, request an OTP, enter it, and reach the dashboard.
    LoginPage(page).open()
    LoginPage(page).login_with_otp(INITIATOR_EMAIL, TEST_OTP)

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
    _assert_no_open_previous_claim(member_search)

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
    claim_number = claim_dashboard.open_latest_claim_assigned_to_me(
        member_name, expected_status="Submitted"
    )
    _save_claim_number(claim_number)

    detail = ITClaimDetailPage(page)
    assert detail.is_loaded(), "Submitted claim detail should be displayed"
    detail.fill_distribution(
        IT_CLAIM_DATA.ict_amount,
        IT_CLAIM_DATA.digital_amount,
        IT_CLAIM_DATA.claim_amount,
    )
    detail.add_note(IT_CLAIM_DATA.initiator_note)
    detail.add_item_remark(IT_CLAIM_DATA.initiator_item_remark)
    detail.select_user_and_forward(IT_CLAIM_DATA.reviewer_forward_name)

    page.wait_for_timeout(1000)
    print("[STEP] Afroj forwarding completed; preparing logout")
    page.goto(BASE_URL.replace("/login?login=email", "/dashboard"))
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_timeout(1000)
    DashboardPage(page).logout()
    page.wait_for_timeout(1000)
    print("[STEP] Afroj logged out; login as Prabhat")
    LoginPage(page).open()
    LoginPage(page).login_with_otp(REVIEWER_EMAIL, TEST_OTP)

    reviewer_dashboard = DashboardPage(page)
    page.wait_for_timeout(1000)
    reviewer_dashboard.open_it_equipment_claims()
    reviewer_claim_dashboard = ITClaimDashboardPage(page)
    assert reviewer_claim_dashboard.is_loaded()
    reviewer_claim_dashboard.open_claim_by_number(
        claim_number, expected_status="Initiated"
    )

    reviewer_detail = ITClaimDetailPage(page)
    assert reviewer_detail.is_loaded()
    reviewer_detail.validate_distribution(IT_CLAIM_DATA.claim_amount)
    reviewer_detail.add_note(IT_CLAIM_DATA.reviewer_note)
    reviewer_detail.add_item_remark(IT_CLAIM_DATA.reviewer_item_remark)
    reviewer_detail.select_user_and_forward(IT_CLAIM_DATA.approver_forward_name)


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
    _assert_no_open_previous_claim(member_search)

    claim_form = ITClaimFormPage(page)
    assert claim_form.is_loaded(), "IT Equipment Claim form should be displayed"
    claim_form.enter_duplicate_invoice_claim(
        category=IT_CLAIM_DATA.category,
        quantity=IT_CLAIM_DATA.quantity,
        price_per_unit=IT_CLAIM_DATA.price_per_unit,
        invoice_number=IT_CLAIM_DATA.invoice_number,
        description=IT_CLAIM_DATA.description,
    )

    claim_form.open_preview()
    preview = ITClaimPreviewPage(page)
    assert preview.is_loaded(), "Claim Preview screen should be displayed"
    assert preview.contains_claim_value(IT_CLAIM_DATA.invoice_number)
    preview.submit_claim()
    assert preview.is_submission_confirmed()

    dashboard.logout()
    assert page.get_by_role("button", name="Send OTP").is_visible(), (
        "User should return to login page after logout"
    )


@pytest.mark.smoke
def test_initiator_forwards_radha_claim_to_radhe_pandey(page: Page):
    LoginPage(page).open()
    LoginPage(page).login_with_otp(INITIATOR_EMAIL, TEST_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded()
    claim_number = claim_dashboard.open_latest_claim_assigned_to_me(
        IT_CLAIM_DATA.member_name, expected_status="Submitted"
    )
    _save_claim_number(claim_number)

    detail = ITClaimDetailPage(page)
    assert detail.is_loaded()
    detail.fill_distribution(
        IT_CLAIM_DATA.ict_amount,
        IT_CLAIM_DATA.digital_amount,
        IT_CLAIM_DATA.claim_amount,
    )
    detail.add_note(IT_CLAIM_DATA.initiator_note)
    detail.add_item_remark(IT_CLAIM_DATA.initiator_item_remark)
    detail.select_user_and_forward(IT_CLAIM_DATA.reviewer_forward_name)


@pytest.mark.smoke
def test_reviewer_forwards_claim_to_approver(page: Page):
    LoginPage(page).open()
    LoginPage(page).login_with_otp(REVIEWER_EMAIL, TEST_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded()
    _open_tracked_claim(claim_dashboard, expected_status="Initiated")

    reviewer_detail = ITClaimDetailPage(page)
    assert reviewer_detail.is_loaded()
    reviewer_detail.validate_distribution(IT_CLAIM_DATA.claim_amount)
    reviewer_detail.add_note(IT_CLAIM_DATA.reviewer_note)
    reviewer_detail.add_item_remark(IT_CLAIM_DATA.reviewer_item_remark)
    reviewer_detail.select_user_and_forward(IT_CLAIM_DATA.approver_forward_name)


@pytest.mark.smoke
def test_approver_starts_esign_approval(page: Page):
    LoginPage(page).open()
    LoginPage(page).login_with_otp(APPROVER_EMAIL, TEST_OTP)

    dashboard = DashboardPage(page)
    dashboard.open_it_equipment_claims()
    claim_dashboard = ITClaimDashboardPage(page)
    assert claim_dashboard.is_loaded()
    _open_tracked_claim(claim_dashboard, expected_status="Reviewed")

    detail = ITClaimDetailPage(page)
    assert detail.is_loaded()
    detail.validate_distribution(IT_CLAIM_DATA.claim_amount)
    detail.add_note(IT_CLAIM_DATA.approver_note)
    detail.approve_claim()
    if not ESIGN_APPROVAL:
        # Unattended run: the e-sign request was sent; nobody can approve it.
        detail.log_step("E-sign approval skipped (ESIGN_APPROVAL=false)")
        return
    detail.wait_for_approval_success()
    # The claim is settled; the next run starts a new claim.
    CLAIM_NUMBER_FILE.unlink(missing_ok=True)


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
    _assert_no_open_previous_claim(member_search)

    claim_form = ITClaimFormPage(page)
    claim_form.invoice_number_field.fill(IT_CLAIM_DATA.invalid_invoice_number)
    claim_form.invoice_number_field.press("Tab")

    assert claim_form.is_invalid_invoice_number_visible(), (
        "Invoice number should reject special characters"
    )
