
import json
from pathlib import Path

from src.knowledge_transfer.coverage import detect_knowledge_gaps
from src.knowledge_transfer.models import Evidence, EvidenceType


ROOT = Path(__file__).resolve().parents[1]


def load_scenarios():
    return json.loads(
        (ROOT / "evaluation" / "scenarios.json").read_text(encoding="utf-8")
    )["scenarios"]


def evidence_from_scenario(scenario):
    return [
        Evidence(
            id=f"{scenario['id']}-E-{index:02d}",
            source=material["source"],
            evidence_type=EvidenceType(material["type"]),
            content=material["text"],
        )
        for index, material in enumerate(scenario["materials"], start=1)
    ]


def test_detects_expected_gaps_in_incomplete_scenarios():
    expected_titles = {
        "HT-02": {
            "No defined fallback approver or escalation path",
            "No documented workaround or conditions for using it",
        },
        "HT-03": {
            "No documented fallback procedure for a delayed export",
            "No documented report-selection criteria or replacement-column mapping",
        },
        "HT-06": {
            "No documented criteria for account-specific escalation exceptions",
            "No documented stakeholder coordination or relationship-history handover",
        },
    }

    scenarios = {item["id"]: item for item in load_scenarios()}

    for scenario_id, expected in expected_titles.items():
        findings = detect_knowledge_gaps(
            scenario_id,
            evidence_from_scenario(scenarios[scenario_id]),
        )
        assert {finding.title for finding in findings} == expected
        assert all(finding.evidence_ids for finding in findings)


def test_routine_invoice_scenario_has_no_rule_detected_gaps():
    scenario = next(s for s in load_scenarios() if s["id"] == "HT-01")

    findings = detect_knowledge_gaps(
        scenario["id"],
        evidence_from_scenario(scenario),
    )

    assert findings == []


def test_every_finding_references_existing_evidence():
    for scenario in load_scenarios():
        evidence = evidence_from_scenario(scenario)
        evidence_ids = {item.id for item in evidence}

        findings = detect_knowledge_gaps(scenario["id"], evidence)

        assert all(
            set(finding.evidence_ids).issubset(evidence_ids)
            for finding in findings
        )


def test_empty_evidence_returns_no_findings():
    assert detect_knowledge_gaps("R-01", []) == []
