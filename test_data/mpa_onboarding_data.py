"""Dummy test data for the MPA Member Onboarding forms (stage only).

Values are matched to form fields by keywords in the field label or
placeholder (first match wins), so one table covers all 6 forms and their
sub-forms. Change a value here to change it everywhere it is used.
"""
import os

from config import TEST_FILES_DIR

MPA_LOGIN_URL = "https://test.rajyasabha.digital/mpa/login?login=email"
MPA_DASHBOARD_URL = "https://test.rajyasabha.digital/mpa/onboarding"

# LO + member pairs used for testing. Pick one per run with MPA_PROFILE
# (default: first). Member-specific values (names, email id, social links)
# come from the selected profile.
PROFILES = {
    "arjun": dict(lo_email="prabhat.kiran@rajyasabha.digital", lo_name="Prabhat Kiran SDS",
                  member="Arjun Singh", hindi="श्री अर्जुन सिंह", handle="arjunsingh",
                  email_id="arjun.singh.test"),
    "sam": dict(lo_email="claim.rev@rajyasabha.digital", lo_name="RadhePandey",
                member="Sam Singh", hindi="श्री सैम सिंह", handle="samsingh",
                email_id="sam.singh.test"),
    "karmveer": dict(lo_email="claim.rev@rajyasabha.digital", lo_name="RadhePandey",
                     member="Karmveer Singh Rana", hindi="श्री करमवीर सिंह राणा", handle="karmveersinghrana",
                     email_id="karmveer.rana.test"),
    "akhil": dict(lo_email="rsshelpdesk1@rajyasabha.digital", lo_name="Help Desk",
                  member="Akhil", pick="#852662", hindi="श्री अखिल", handle="akhil", email_id="akhil.test"),
    "kapil": dict(lo_email="rsshelpdesk1@rajyasabha.digital", lo_name="Help Desk",
                  member="Kapil Sibal", hindi="श्री कपिल सिब्बल", handle="kapilsibal", email_id="kapil.sibal.test"),
    "deepanshu": dict(lo_email="rsshelpdesk1@rajyasabha.digital", lo_name="Help Desk",
                      member="Deepanshu Hooda", hindi="श्री दीपांशु हुड्डा", handle="deepanshuhooda",
                      email_id="deepanshu.hooda.test"),
    "mayankmem": dict(lo_email="prabhat.kiran@rajyasabha.digital", lo_name="Prabhat Kiran SDS",
                      member="Mayank Kumar", pick="#85217", hindi="श्री मयंक कुमार", handle="mayankkumar",
                      email_id="mayank.kumar.test"),
    "katya": dict(lo_email="prabhat.kiran@rajyasabha.digital", lo_name="Prabhat Kiran SDS",
                  member="Katya Singh", hindi="श्री कात्या सिंह", handle="katyasingh",
                  email_id="katya.singh.test"),
}
PROFILE = PROFILES[os.getenv("MPA_PROFILE", "arjun")]
LO_EMAIL = PROFILE["lo_email"]
LO_NAME = PROFILE["lo_name"]
MEMBER_NAME = PROFILE["member"]
MEMBER_PICK = PROFILE.get("pick", MEMBER_NAME)  # text that identifies the member in the picker
_h = PROFILE["handle"]

ONBOARDING_FORMS = [
    "Personal & Official Detail",
    "Bank Account Details & Nominee for RSS",
    "Achievements & Preferences",
    "Vehicle Pass Details",
    "PA/PS Details",
    "Driver Pass Details",
]

UPLOAD_FILE = str(TEST_FILES_DIR / "Test_Data1.jpeg")


def _aadhaar(base: str) -> str:
    """Append the Verhoeff check digit so the dummy Aadhaar is well-formed."""
    d = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
         [2, 3, 4, 0, 1, 7, 8, 9, 5, 6], [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
         [4, 0, 1, 2, 3, 9, 5, 6, 7, 8], [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
         [6, 5, 9, 8, 7, 1, 0, 4, 3, 2], [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
         [8, 7, 6, 5, 9, 3, 2, 1, 0, 4], [9, 8, 7, 6, 5, 4, 3, 2, 1, 0]]
    p = [[0, 1, 2, 3, 4, 5, 6, 7, 8, 9], [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
         [5, 8, 0, 3, 7, 9, 6, 1, 4, 2], [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
         [9, 4, 5, 3, 1, 2, 6, 8, 7, 0], [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
         [2, 7, 9, 3, 8, 0, 6, 4, 1, 5], [7, 0, 4, 6, 9, 1, 3, 2, 5, 8]]
    inv = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]
    c = 0
    for i, digit in enumerate(reversed(base)):
        c = d[c][p[(i + 1) % 8][int(digit)]]
    return base + str(inv[c])


# (keywords, value) for text/number/tel/email inputs and textareas.
TEXT_VALUES = [
    (("hindi",), PROFILE["hindi"]),
    (("i-card", "icard"), "IC12345"),
    (("railway",), "New Delhi Railway Station"),
    (("airport name",), "Indira Gandhi International Airport"),
    (("seaport",), "Mumbai Port"),
    (("distance",), "15"),
    (("preferred sansad",), PROFILE["email_id"]),
    (("device make",), "Samsung"),
    (("device model",), "Galaxy S23"),
    (("device os",), "Android 14"),
    (("mac address",), "AA:BB:CC:DD:EE:FF"),
    (("facebook",), f"https://facebook.com/{_h}"),
    (("instagram",), f"https://instagram.com/{_h}"),
    (("twitter", "x.com"), f"https://x.com/{_h}"),
    (("linkedin",), f"https://linkedin.com/in/{_h}"),
    (("blog",), f"https://{_h}.blogspot.com"),
    (("period",), "2015-2021"),
    (("position",), "Member"),
    (("terms in",), "1"),
    (("university", "board"), "Delhi University"),
    (("subject", "specialization"), "Political Science"),
    (("other profession",), "Social Worker"),
    (("occupation", "profession"), "Service"),
    (("branch name",), "New Delhi Main Branch"),
    (("relation",), "Spouse"),
    (("age *", "age (years)"), "35"),
    (("post office",), "Parliament Street"),
    (("police station",), "Parliament Street"),
    (("nominee name",), "Sunita Singh"),
    (("ifsc",), "SBIN0000691"),
    (("micr",), "110002087"),
    (("account holder", "name as per rc", "as per bank"), MEMBER_NAME),
    (("account number", "account no"), "12345678901"),
    (("aadhaar", "aadhar"), _aadhaar("23456789012")),
    (("pan number", "pan no", "pan card", "e.g. abcde"), "ABCPS1234K"),
    (("style of name",), "Shri " + MEMBER_NAME),
    (("passport",), "A1234567"),
    (("countries",), "Japan, France"),
    (("delegation",), "Indian Parliamentary Delegation"),
    (("reason", "purpose"), "Official parliamentary visit"),
    (("telephone", "landline", "residence tel", "office tel", "fax"), "01123034567"),
    (("mobile", "phone", "whatsapp"), "9876543210"),
    (("email", "mail"), PROFILE["email_id"] + "@example.com"),
    (("pin", "postal"), "110001"),
    (("father",), "Ram Prasad Singh"),
    (("mother",), "Sita Devi"),
    (("spouse", "wife", "husband"), "Sunita Singh"),
    (("registration number", "vehicle no", "vehicle number", "e.g. dl"), "DL01AB1234"),
    (("engine",), "ENG123456"),
    (("chassis",), "CHS123456"),
    (("parking", "label no"), "PL123"),
    (("vehicle type",), "Car"),
    (("brand", "make"), "Maruti"),
    (("model",), "Swift"),
    (("colo",), "White"),
    (("identification",), "Mole on left cheek"),
    (("salary", "income", "amount"), "25000"),
    (("percentage", "share"), "100"),
    (("year",), "2020"),
    (("address",), "House No 12, Sector 5, New Delhi"),
    (("city", "village", "place", "location", "town", "constituency"), "New Delhi"),
    (("website", "url", "link"), "https://example.com"),
    (("full name", "name"), "Rakesh Kumar"),
]
DEFAULT_TEXT = "Test data"
DEFAULT_NUMBER = "1"

# (keywords, yyyy-mm-dd) for date inputs.
DATE_VALUES = [
    (("birth", "dob"), "1990-05-15"),
    (("term from", "from date", "start"), "2015-01-10"),
    (("term to", "to date", "end date", "till"), "2021-01-09"),
    (("registration",), "2022-01-10"),
]
DEFAULT_DATE = "2025-01-10"

# Preferred option text for selects (first match wins); otherwise the
# first real option is chosen.
SELECT_PREFERENCES = [
    (("state",), "Delhi"),
    (("gender",), "Male"),
    (("blood",), "B+"),
]

# Fields left empty: optional sections, auto-filled and auto-calculated fields.
SKIP_KEYWORDS = ("auto-filled", "auto-calculated", "leaving")
SKIP_SECTIONS_AFTER = ("Alternate Account",)

# Wrong values an earlier automation run put in some fields; a field holding
# one of these is corrected even though "keep existing values" applies.
REPAIR_VALUES = {
    "Rakesh Kumar", "Sunita Singh", "Test data", "1", "2025-01-10", "Maruti",
    "9876543210", "E1:2E:C", "https://example.com", PROFILE["email_id"] + "@example.com",
}
