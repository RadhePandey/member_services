from pathlib import Path

import pytest
from playwright.sync_api import Page

from config import (
    ESIGN_APPROVAL,
    MEDICAL_APPROVER_EMAIL,
    MEDICAL_INITIATOR_EMAIL,
    TEST_OTP,
)
from pages.dashboard_page import DashboardPage
from pages.it_claim_dashboard_page import ITClaimDashboardPage
from pages.login import LoginPage
from pages.medical_claim_dashboard_page import MedicalClaimDashboardPage
from pages.medical_claim_detail_page import MedicalClaimDetailPage
from pages.medical_claim_form_page import MedicalClaimFormPage
from pages.medical_claim_preview_page import MedicalClaimPreviewPage
from pages.member_search_page import MemberSearchPage
from test_data.medical_claim_data import MEDICAL_CLAIM_DATA

# Claim number of the Medical claim moving through the flow, kept on disk so
# a later stage (or a re-run of a single stage) can open the same claim.
CLAIM_NUMBER_FILE = (
    Path(__file__).resolve().parents[1] / "reports" / ".medical_claim_number.txt"
)


def _open_medical_claims(page: Page, email: str = MEDICAL_INITIATOR_EMAIL):
    LoginPage(page).open()
    LoginPage(page).login_with_otp(email, TEST_OTP)
    DashboardPage(page).open_it_equipment_claims()
    assert ITClaimDashboardPage(page).is_loaded(), (
        "IT Equipment Claims dashboard should be displayed"
    )
    medical_dashboard = MedicalClaimDashboardPage(page)
    medical_dashboard.open_from_sidebar()
    assert medical_dashboard.is_loaded(), "Medical Claims dashboard should be displayed"
    return medical_dashboard


def _submit_claim(page: Page, medical_dashboard: MedicalClaimDashboardPage):
    member_name = MEDICAL_CLAIM_DATA.member_name
    # Several claims can be open for a member, so remember the existing ones
    # to identify the claim submitted by this test.
    existing_claim_numbers = medical_dashboard.visible_claim_numbers()
    medical_dashboard.open_add_claim()

    member_search = MemberSearchPage(page)
    assert member_search.is_loaded(), "Member Search screen should be displayed"
    member_search.search_by_name(member_name)
    member_search.select_member(member_name)

    # Claim form: Preview is enabled only after both uploads and the checkbox.
    claim_form = MedicalClaimFormPage(page)
    assert claim_form.is_loaded(member_name), "Medical Claim form should be displayed"
    assert not claim_form.is_preview_enabled(), (
        "Preview should be disabled before the files are uploaded"
    )
    claim_form.upload_claim_forms(MEDICAL_CLAIM_DATA.claim_forms_file)
    claim_form.upload_supporting_documents(MEDICAL_CLAIM_DATA.supporting_documents_file)
    assert not claim_form.is_preview_enabled(), (
        "Preview should stay disabled until the confirmation checkbox is checked"
    )
    claim_form.click_confirmation_checkbox()
    claim_form.open_preview()

    # Preview: verify member, processed-by user and both uploaded files.
    preview = MedicalClaimPreviewPage(page)
    assert preview.is_loaded(), "Claim Preview screen should be displayed"
    assert preview.contains(member_name)
    assert preview.contains(MEDICAL_CLAIM_DATA.processed_by_name)
    assert preview.contains(Path(MEDICAL_CLAIM_DATA.claim_forms_file).name)
    assert preview.contains(Path(MEDICAL_CLAIM_DATA.supporting_documents_file).name)
    preview.submit_claim()

    # Result: success message, back on the dashboard, claim in Assigned to Me.
    assert preview.is_submission_confirmed()
    assert medical_dashboard.is_loaded(), (
        "Submitted claim should return to the Medical Claims dashboard"
    )
    claim_number = medical_dashboard.find_new_claim_number(
        member_name, expected_status="Submitted", known_numbers=existing_claim_numbers
    )
    CLAIM_NUMBER_FILE.parent.mkdir(parents=True, exist_ok=True)
    CLAIM_NUMBER_FILE.write_text(claim_number, encoding="utf-8")
    return claim_number


def _initiate_and_forward(page: Page, medical_dashboard, claim_number: str):
    # Initiator opens the submitted claim, enters the amounts and forwards it.
    medical_dashboard.open_claim_by_number(claim_number, expected_status="Submitted")
    detail = MedicalClaimDetailPage(page)
    assert detail.is_loaded(claim_number), "Initiator Medical Claim screen should be displayed"
    detail.enter_amounts(
        MEDICAL_CLAIM_DATA.claimed_amount, MEDICAL_CLAIM_DATA.payable_amount
    )
    detail.validate_amount_summary(
        MEDICAL_CLAIM_DATA.claimed_amount, MEDICAL_CLAIM_DATA.payable_amount
    )
    detail.add_note(MEDICAL_CLAIM_DATA.initiator_note)
    detail.select_user_and_forward(MEDICAL_CLAIM_DATA.forward_to_name)


@pytest.mark.medical
@pytest.mark.smoke
def test_initiator_submits_and_forwards_medical_claim(page: Page):
    medical_dashboard = _open_medical_claims(page)
    claim_number = _submit_claim(page, medical_dashboard)
    _initiate_and_forward(page, medical_dashboard, claim_number)


@pytest.mark.medical
@pytest.mark.smoke
def test_approver_esign_approves_medical_claim(page: Page):
    # kaushlendra ini checks the Initiator's amounts and note, then approves
    # with e-sign (biometric verification in the Sanchalan Setu app).
    if not CLAIM_NUMBER_FILE.exists():
        pytest.skip("No forwarded Medical claim recorded; run the full flow first.")
    claim_number = CLAIM_NUMBER_FILE.read_text(encoding="utf-8").strip()
    medical_dashboard = _open_medical_claims(page, MEDICAL_APPROVER_EMAIL)
    medical_dashboard.open_claim_by_number(
        claim_number, expected_status="Initiated", for_approval=True
    )

    detail = MedicalClaimDetailPage(page)
    assert detail.is_loaded(claim_number, role="Approver"), (
        "Approver Medical Claim screen should be displayed"
    )
    detail.validate_saved_amounts(
        MEDICAL_CLAIM_DATA.claimed_amount, MEDICAL_CLAIM_DATA.payable_amount
    )
    detail.validate_previous_note(
        MEDICAL_CLAIM_DATA.initiator_note, MEDICAL_CLAIM_DATA.processed_by_name
    )
    detail.add_note(MEDICAL_CLAIM_DATA.approver_note)
    detail.approve_claim()
    if not ESIGN_APPROVAL:
        # Unattended run: the e-sign request was sent; nobody can approve it.
        detail.log_step(
            "E-sign approval skipped (ESIGN_APPROVAL=false); "
            f"claim {claim_number} is waiting for e-sign"
        )
        return
    detail.wait_for_approval_success()
    # The claim is settled; the next run starts a new claim.
    CLAIM_NUMBER_FILE.unlink(missing_ok=True)


@pytest.mark.medical
@pytest.mark.regression
def test_initiator_forwards_submitted_medical_claim(page: Page):
    """Re-run only the initiation stage for the last submitted claim."""
    if not CLAIM_NUMBER_FILE.exists():
        pytest.skip("No submitted Medical claim recorded; run the full flow first.")
    claim_number = CLAIM_NUMBER_FILE.read_text(encoding="utf-8").strip()
    medical_dashboard = _open_medical_claims(page)
    _initiate_and_forward(page, medical_dashboard, claim_number)
