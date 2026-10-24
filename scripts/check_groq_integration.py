
from src.knowledge_transfer.models import Evidence, EvidenceType
from src.knowledge_transfer.llm_candidates import detect_hybrid_gaps

records = [
    Evidence(
        id="SOP-01",
        source="refund_sop",
        evidence_type=EvidenceType.SOP,
        content=(
            "Confirm the order, check refund eligibility, obtain "
            "required approval, and record the refund."
        ),
    ),
    Evidence(
        id="TR-01",
        source="handover_transcript",
        evidence_type=EvidenceType.TRANSCRIPT,
        content=(
            "When the original payment is still pending, wait until "
            "it settles before processing the duplicate-charge refund. "
            "The standard guide does not explain this situation."
        ),
    ),
]

result = detect_hybrid_gaps(
    responsibility_id="R-REFUNDS",
    evidence_records=records,
)

print("Provider status:", result.llm_status)
print("Rejected candidates:", result.rejected_candidates)
print("Errors:", result.errors)
print("Findings:")

for finding in result.findings:
    print(f"- {finding.title}")
    print(f"  Description: {finding.description}")
    print(f"  Evidence IDs: {finding.evidence_ids}")
