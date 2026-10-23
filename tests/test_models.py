
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from src.knowledge_transfer.models import (
    Evidence,
    EvidenceType,
    GapStatus,
    KnowledgeGap,
    ReadinessStatus,
    VerificationOutcome,
    VerificationRecord,
)


def test_evidence_requires_content():
    with pytest.raises(ValidationError):
        Evidence(
            id="E-01",
            source="demo",
            evidence_type=EvidenceType.TASK_OUTPUT,
            content="",
        )


def test_open_gap_can_be_created():
    gap = KnowledgeGap(
        id="G-01",
        responsibility_id="R-01",
        title="Missing fallback process",
        description="The fallback process is not documented.",
        evidence_ids=["E-01"],
    )

    assert gap.status == GapStatus.OPEN


def test_resolved_gap_requires_note_and_timestamp():
    with pytest.raises(ValidationError):
        KnowledgeGap(
            id="G-02",
            responsibility_id="R-01",
            title="Missing fallback process",
            description="The fallback process was addressed.",
            evidence_ids=["E-01"],
            status=GapStatus.RESOLVED,
        )


def test_resolved_gap_accepts_note_and_timestamp():
    gap = KnowledgeGap(
        id="G-03",
        responsibility_id="R-01",
        title="Missing fallback process",
        description="The fallback process was documented.",
        evidence_ids=["E-01"],
        status=GapStatus.RESOLVED,
        resolution_note="Approved fallback steps added to the SOP.",
        resolved_at=datetime.now(timezone.utc),
    )

    assert gap.status == GapStatus.RESOLVED


def test_passed_assessment_requires_verification_timestamp():
    with pytest.raises(ValidationError):
        VerificationRecord(
            id="V-01",
            responsibility_id="R-01",
            successor="Successor A",
            assessment_criteria="Complete the task independently.",
            outcome=VerificationOutcome.PASSED,
            evidence_ids=["E-01"],
            reviewer="Operations Manager",
        )


def test_complete_passed_assessment_verifies_readiness():
    record = VerificationRecord(
        id="V-02",
        responsibility_id="R-01",
        successor="Successor A",
        assessment_criteria="Complete the task independently.",
        outcome=VerificationOutcome.PASSED,
        evidence_ids=["E-01"],
        reviewer="Operations Manager",
        verified_at=datetime.now(timezone.utc),
    )

    assert record.readiness == ReadinessStatus.VERIFIED


def test_incomplete_assessment_does_not_verify_readiness():
    record = VerificationRecord(
        id="V-03",
        responsibility_id="R-01",
        successor="Successor A",
        assessment_criteria="Complete the task independently.",
        outcome=VerificationOutcome.INCOMPLETE,
        evidence_ids=["E-01"],
        reviewer="Operations Manager",
    )

    assert record.readiness == ReadinessStatus.UNVERIFIED


def test_failed_assessment_does_not_verify_readiness():
    record = VerificationRecord(
        id="V-04",
        responsibility_id="R-01",
        successor="Successor A",
        assessment_criteria="Complete the task independently.",
        outcome=VerificationOutcome.FAILED,
        evidence_ids=["E-01"],
        reviewer="Operations Manager",
    )

    assert record.readiness == ReadinessStatus.UNVERIFIED
