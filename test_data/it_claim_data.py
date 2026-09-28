from dataclasses import dataclass


@dataclass(frozen=True)
class ITClaimTestData:
    member_name: str = "Radha Mohan Das Agrawal"
    category: str = "Desktop Computer"
    quantity: str = "1"
    price_per_unit: str = "1400"
    invoice_number: str = "testing3123"
    description: str = "Test IT equipment claim"


IT_CLAIM_DATA = ITClaimTestData()
