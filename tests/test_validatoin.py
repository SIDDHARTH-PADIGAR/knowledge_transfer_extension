
from src.knowledge_transfer.coverage import GapFinding
from src.knowledge_transfer.models import Evidence, EvidenceType
from src.knowledge_transfer.validation import (
    validate_exact_quote,
    validate_finding,
)


def make_evidence(
    evidence_id: str = "E-01",
    content: str = "If the supervisor is away, the shift lead signs off.",
) -> Evidence:
    return Evidence(
        id=evidence_id,
        source="handover.txt",
        evidence_type=EvidenceType.TRANSCRIPT,
        content=content,
    )


def make_finding(
    evidence_ids: tuple[str, ...] = ("E-01",),
) -> GapFinding:
    return GapFinding(
        title="No documented substitute approval criteria",
        description="The fallback approval criteria are not documented.",
        evidence_ids=evidence_ids,
        responsibility_id="R-01",
    )


def test_valid_finding_passes():
    result = validate_finding(make_finding(), [make_evidence()])
    assert result.valid
    assert result.errors == ()


def test_unknown_evidence_id_fails():
    result = validate_finding(
        make_finding(("MISSING",)),
        [make_evidence()],
    )
    assert not result.valid
    assert any("Unknown evidence ID" in error for error in result.errors)


def test_finding_without_evidence_fails():
    result = validate_finding(make_finding(()), [make_evidence()])
    assert not result.valid
    assert any("no evidence" in error.lower() for error in result.errors)


def test_duplicate_evidence_ids_fail():
    result = validate_finding(
        make_finding(),
        [make_evidence(), make_evidence()],
    )
    assert not result.valid
    assert any("duplicate IDs" in error for error in result.errors)


def test_exact_quote_passes():
    result = validate_exact_quote(
        "the shift lead signs off",
        "E-01",
        [make_evidence()],
    )
    assert result.valid


def test_fabricated_quote_fails():
    result = validate_exact_quote(
        "the shift lead signs off in writing",
        "E-01",
        [make_evidence()],
    )
    assert not result.valid


def test_quote_with_unknown_source_fails():
    result = validate_exact_quote(
        "the shift lead signs off",
        "MISSING",
        [make_evidence()],
    )
    assert not result.valid
