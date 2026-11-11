from dataclasses import dataclass

from config import IT_CLAIM_INVOICE_IMAGE, IT_CLAIM_INVOICE_PDF


@dataclass(frozen=True)
class MedicalClaimTestData:
    member_name: str = "Radha Mohan Das Agrawal"
    # Name shown as "Processed By" on the Preview screen for the Initiator.
    processed_by_name: str = "Prabhat Kiran SDS"
    # Same sample files as the IT Equipment claim.
    claim_forms_file: str = IT_CLAIM_INVOICE_PDF
    supporting_documents_file: str = IT_CLAIM_INVOICE_IMAGE
    # Entered by the Initiator; payable must be <= claimed.
    claimed_amount: str = "500"
    payable_amount: str = "450"
    initiator_note: str = "Initiator review completed."
    approver_note: str = "Approver review completed."
    # Name shown in the Forward dropdown for the next user in the flow.
    forward_to_name: str = "kaushlendra ini"


MEDICAL_CLAIM_DATA = MedicalClaimTestData()
