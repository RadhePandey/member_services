import os
from pathlib import Path

BASE_URL = os.getenv("APP_BASE_URL", "https://test.rajyasabha.digital/login?login=email")
QR_LOGIN_URL = os.getenv("QR_LOGIN_URL", "https://test.rajyasabha.digital/login")
TEST_EMAIL = os.getenv("TEST_EMAIL", "claim.rev@rajyasabha.digital")
TEST_OTP = os.getenv("TEST_OTP", "123456")
INITIATOR_EMAIL = os.getenv(
    "INITIATOR_EMAIL", "mohd.afroj@rajyasabha.digital"
)
REVIEWER_EMAIL = os.getenv(
    "REVIEWER_EMAIL", "prabhat.kiran@rajyasabha.digital"
)
APPROVER_EMAIL = os.getenv("APPROVER_EMAIL", "claim.rev@rajyasabha.digital")
# Medical claims are auto-assigned to every Initiator; this user submits the
# claim and also initiates (forwards) it.
MEDICAL_INITIATOR_EMAIL = os.getenv(
    "MEDICAL_INITIATOR_EMAIL", "prabhat.kiran@rajyasabha.digital"
)
# Shown as "kaushlendra ini"; approves Medical claims with e-sign.
MEDICAL_APPROVER_EMAIL = os.getenv(
    "MEDICAL_APPROVER_EMAIL", "kaushalendra.panday@rajyasabha.digital"
)
TEST_LOGIN_ALT_EMAIL = os.getenv("TEST_LOGIN_ALT_EMAIL")
TEST_INVALID_EMAIL = os.getenv("TEST_INVALID_EMAIL")
# Sample upload files kept in the project so any machine (e.g. Jenkins) can
# run the tests.
TEST_FILES_DIR = Path(__file__).resolve().parent / "test_data" / "files"
IT_CLAIM_INVOICE_PDF = os.getenv(
    "IT_CLAIM_INVOICE_PDF", str(TEST_FILES_DIR / "Test_Data1.jpeg")
)
IT_CLAIM_INVOICE_IMAGE = os.getenv(
    "IT_CLAIM_INVOICE_IMAGE", str(TEST_FILES_DIR / "SignatureDummy.png")
)
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_SLOW_MO = float(os.getenv("BROWSER_SLOW_MO", "0"))
BROWSER_KEEP_OPEN = os.getenv("BROWSER_KEEP_OPEN", "false").lower() == "true"
# When enabled, records a .webm video of every test's browser session so the
# run can be watched/shared afterwards even in environments where the headed
# browser window isn't visible on screen. Videos are saved under VIDEOS_DIR.
BROWSER_RECORD_VIDEO = os.getenv("BROWSER_RECORD_VIDEO", "false").lower() == "true"
# E-sign approval needs a person's biometric in the Sanchalan Setu app. Set
# ESIGN_APPROVAL=false for unattended runs (e.g. Jenkins): the approval test
# then passes once the e-sign request is sent, without waiting for approval.
ESIGN_APPROVAL = os.getenv("ESIGN_APPROVAL", "true").lower() == "true"
