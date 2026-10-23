
from unittest.mock import patch

from src.knowledge_transfer.coverage import GapFinding
from src.knowledge_transfer.models import Evidence, EvidenceType
from src.knowledge_transfer.llm_candidates import (
    detect_hybrid_gaps,
)


def evidence():
    return [
        Evidence(
            id="E-SOP",
            source="procedure.txt",
            evidence_type=EvidenceType.SOP,
            content="The supervisor must approve inventory adjustments.",
        ),
        Evidence(
            id="E-01",
            source="handover.txt",
            evidence_type=EvidenceType.TRANSCRIPT,
            content=(
                "If the supervisor is away, "
                "the shift lead signs off instead."
            ),
        )
    ]


def candidate(quote):
    return {
        "gaps": [
            {
                "title": "Missing fallback approval procedure",
                "description": "The fallback approver is undocumented.",
                "evidence_id": "E-01",
                "quote": quote,
            }
        ]
    }


@patch(
    "src.knowledge_transfer.llm_candidates._ask_ollama",
    return_value=candidate(
        "If the supervisor is away, the shift lead signs off instead."
    ),
)
def test_valid_llm_candidate_is_accepted(mock_ollama):
    records = evidence()
    result = detect_hybrid_gaps("R-01", records)

    assert result.llm_status == "completed"
    assert any(
        finding.title == "Missing fallback approval procedure"
        for finding in result.findings
    )
    assert result.rejected_candidates == 0


@patch(
    "src.knowledge_transfer.llm_candidates._ask_ollama",
    return_value=candidate("The manager approves it in writing."),
)
def test_fabricated_quote_is_rejected(mock_ollama):
    records = evidence()
    result = detect_hybrid_gaps("R-01", records)

    assert not any(
        finding.title == "Missing fallback approval procedure"
        for finding in result.findings
    )
    assert result.rejected_candidates == 1


@patch(
    "src.knowledge_transfer.llm_candidates.detect_knowledge_gaps",
)
@patch(
    "src.knowledge_transfer.llm_candidates._ask_ollama",
    side_effect=ConnectionError("Ollama unavailable"),
)
def test_llm_failure_preserves_baseline(
    mock_ollama,
    mock_detector,
):
    baseline_finding = GapFinding(
        title="Baseline finding",
        description="A deterministic finding must be preserved.",
        evidence_ids=("E-01",),
        responsibility_id="R-01",
    )
    mock_detector.return_value = [baseline_finding]

    records = evidence()
    result = detect_hybrid_gaps("R-01", records)

    assert result.llm_status == "unavailable_or_invalid"
    assert result.errors
    assert result.findings == (baseline_finding,)
    mock_detector.assert_called_once_with("R-01", records)


@patch(
    "src.knowledge_transfer.llm_candidates._ask_ollama",
    return_value={"gaps": [{"title": "Incomplete candidate"}]},
)
def test_malformed_candidate_is_rejected(mock_ollama):
    result = detect_hybrid_gaps("R-01", evidence())

    assert result.rejected_candidates == 1
    assert result.errors
