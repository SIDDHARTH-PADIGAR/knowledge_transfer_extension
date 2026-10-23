
from src.knowledge_transfer.models import Evidence, Responsibility


def validate_evidence_links(
    responsibility: Responsibility,
    evidence_records: list[Evidence],
) -> list[str]:
    """Return evidence-link errors for a responsibility."""
    errors: list[str] = []

    evidence_by_id = {evidence.id: evidence for evidence in evidence_records}

    if len(evidence_by_id) != len(evidence_records):
        errors.append("Duplicate evidence IDs exist.")

    for evidence_id in responsibility.evidence_ids:
        if evidence_id not in evidence_by_id:
            errors.append(f"Evidence '{evidence_id}' does not exist.")

    return errors


def find_evidence(
    evidence_records: list[Evidence],
    query: str,
) -> list[Evidence]:
    """Find evidence whose source or content contains the query."""
    query = query.strip().casefold()

    if not query:
        return []

    return [
        evidence
        for evidence in evidence_records
        if query in evidence.source.casefold()
        or query in evidence.content.casefold()
    ]
