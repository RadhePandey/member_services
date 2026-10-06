from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class ITClaimTestData:
    member_name: str = "Radha Mohan Das Agrawal"
    category: str = "Desktop Computer"
    quantity: str = "1"
    price_per_unit: str = "1400"
    # Duplicate invoice numbers are allowed (the app only shows an alert).
    invoice_number: str = "HPJBLRMD20260917440"
    # Value with special characters, rejected by the invoice number field.
    invalid_invoice_number: str = "invalid-invoice"
    description: str = "Test IT equipment claim"
    # Split of the claim amount entered by the Initiator. Each part must be
    # greater than zero and ICT + Digital must not exceed the claim amount.
    ict_amount: str = "1000"
    digital_amount: str = "400"
    # Names shown in the Forward dropdown for the next user in the flow.
    reviewer_forward_name: str = "Prabhat Kiran SDS"
    approver_forward_name: str = "RadhePandey"
    initiator_note: str = "Initiator review completed."
    initiator_item_remark: str = "Initiator item remark."
    reviewer_note: str = "Reviewer review completed."
    reviewer_item_remark: str = "Reviewer item remark."
    approver_note: str = "Approver review completed."

    @property
    def claim_amount(self) -> str:
        # Claim amount = price per unit * quantity (summed per product).
        return str(Decimal(self.price_per_unit) * Decimal(self.quantity))


IT_CLAIM_DATA = ITClaimTestData()
