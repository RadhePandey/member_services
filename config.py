import os

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
TEST_LOGIN_ALT_EMAIL = os.getenv("TEST_LOGIN_ALT_EMAIL")
TEST_INVALID_EMAIL = os.getenv("TEST_INVALID_EMAIL")
IT_CLAIM_INVOICE_PDF = os.getenv(
    "IT_CLAIM_INVOICE_PDF",
    r"C:\Users\Radhe\OneDrive\Desktop\Test_Data_Upload\AI\Test_Data1.jpeg",
)
IT_CLAIM_INVOICE_IMAGE = os.getenv(
    "IT_CLAIM_INVOICE_IMAGE",
    r"C:\Users\Radhe\OneDrive\Desktop\Test_Data_Upload\AI\SignatureDummy.png",
)
BROWSER_HEADLESS = os.getenv("BROWSER_HEADLESS", "true").lower() == "true"
BROWSER_SLOW_MO = float(os.getenv("BROWSER_SLOW_MO", "0"))
BROWSER_KEEP_OPEN = os.getenv("BROWSER_KEEP_OPEN", "false").lower() == "true"
