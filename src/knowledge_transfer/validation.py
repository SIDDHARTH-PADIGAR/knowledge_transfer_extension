
from dataclasses import dataclass

from src.knowledge_transfer.coverage import GapFinding
from src.knowledge_transfer.models import Evidence


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    errors: tuple[str, ...]


def validate_finding(
    finding: GapFinding,
    evidence_records: list[Evidence],
) -> ValidationResult:
    """Validate evidence references and quoted claims in a finding.

    This checks traceability and exact quotations. It does not prove
    that the evidence logically supports the conclusion.
    """
    errors: list[str] = []

    evidence_by_id = {evidence.id: evidence for evidence in evidence_records}

    if len(evidence_by_id) != len(evidence_records):
        errors.append("Evidence records contain duplicate IDs.")

    if not finding.evidence_ids:
        errors.append("Finding has no evidence references.")

    linked_evidence: list[Evidence] = []

    for evidence_id in finding.evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is None:
            errors.append(f"Unknown evidence ID: {evidence_id}")
        else:
            linked_evidence.append(evidence)

    if not finding.title.strip():
        errors.append("Finding title is empty.")

    if not finding.description.strip():
        errors.append("Finding description is empty.")

    return ValidationResult(
        valid=not errors,
        errors=tuple(errors),
    )


def validate_exact_quote(
    quote: str,
    evidence_id: str,
    evidence_records: list[Evidence],
) -> ValidationResult:
    """Check that a non-empty quote appears verbatim in its cited source."""
    if not quote.strip():
        return ValidationResult(
            valid=False,
            errors=("Quote is empty.",),
        )

    matches = [
        evidence
        for evidence in evidence_records
        if evidence.id == evidence_id
    ]

    if len(matches) != 1:
        return ValidationResult(
            valid=False,
            errors=(f"Expected one source with ID {evidence_id!r}.",),
        )

    if quote not in matches[0].content:
        return ValidationResult(
            valid=False,
            errors=("Quote does not appear verbatim in the cited source.",),
        )

    return ValidationResult(valid=True, errors=())
