
import json
from pathlib import Path

from src.knowledge_transfer.coverage import detect_knowledge_gaps
from src.knowledge_transfer.models import Evidence, EvidenceType
from src.knowledge_transfer.validation import validate_finding


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_evidence(scenario: dict) -> list[Evidence]:
    return [
        Evidence(
            id=f"{scenario['id']}-E-{index:02d}",
            source=material["source"],
            evidence_type=EvidenceType(material["type"]),
            content=material["text"],
        )
        for index, material in enumerate(scenario["materials"], start=1)
    ]


def main() -> None:
    scenarios = load_json(ROOT / "evaluation" / "scenarios.json")["scenarios"]
    expected = load_json(
        ROOT / "evaluation" / "expected_outcomes.json"
    )["outcomes"]

    expected_by_id = {item["scenario_id"]: item for item in expected}
    total_expected_gaps = 0
    total_detected_gaps = 0
    total_matched_gaps = 0
    readiness_correct = 0

    print("KNOWLEDGE-TRANSFER EVALUATION")
    print("=" * 32)

    for scenario in scenarios:
        scenario_id = scenario["id"]
        outcome = expected_by_id[scenario_id]
        evidence = build_evidence(scenario)
        findings = detect_knowledge_gaps(scenario_id, evidence)
        
        invalid_findings = []

        for finding in findings:
            result = validate_finding(finding, evidence)
            if not result.valid:
                invalid_findings.append(finding.title)

        valid_findings = [
            finding for finding in findings
            if finding.title not in invalid_findings
        ]

        findings = valid_findings

        expected_titles = set(outcome["expected_gaps"])
        detected_titles = {finding.title for finding in findings}

        matched = expected_titles & detected_titles
        missed = expected_titles - detected_titles
        unexpected = detected_titles - expected_titles

        total_expected_gaps += len(expected_titles)
        total_detected_gaps += len(detected_titles)
        total_matched_gaps += len(matched)

        # Readiness is derived from recorded verification evidence,
        # not inferred from whether a procedure or demonstration exists.
        verification_text = " ".join(
            item.content.casefold()
            for item in evidence
            if item.evidence_type == EvidenceType.VERIFICATION_RECORD
        )

        actual_readiness = (
            "verified"
            if (
                "recorded outcome: passed" in verification_text
                and "reviewer:" in verification_text
                and "verification status: confirmed" in verification_text
                and "evidence:" in verification_text
                and "assessment criterion:" in verification_text
            )
            else "unverified"
        )

        readiness_ok = actual_readiness == outcome["expected_readiness"]
        readiness_correct += int(readiness_ok)

        print(f"\n{scenario_id}: {scenario['title']}")
        print(f"  Expected gaps: {len(expected_titles)}")
        print(f"  Detected gaps: {len(detected_titles)}")
        print(f"  Matched: {len(matched)}")
        print(f"  Missed: {sorted(missed)}")
        print(f"  Unexpected: {sorted(unexpected)}")
        print(
            f"  Readiness: expected={outcome['expected_readiness']}, "
            f"actual={actual_readiness}, "
            f"{'PASS' if readiness_ok else 'FAIL'}"
        )

    precision = (
        total_matched_gaps / total_detected_gaps
        if total_detected_gaps
        else 0.0
    )
    recall = (
        total_matched_gaps / total_expected_gaps
        if total_expected_gaps
        else 0.0
    )
    readiness_accuracy = readiness_correct / len(scenarios) if scenarios else 0.0

    print("\nSUMMARY")
    print("-" * 32)
    print(f"Scenarios: {len(scenarios)}")
    print(f"Expected gaps: {total_expected_gaps}")
    print(f"Detected gaps: {total_detected_gaps}")
    print(f"Matched gaps: {total_matched_gaps}")
    print(f"Gap precision: {precision:.3f}")
    print(f"Gap recall: {recall:.3f}")
    print(f"Readiness accuracy: {readiness_accuracy:.3f}")
    print(
        "Note: These results use a small, human-authored benchmark "
        "and scenario-informed rules; they do not establish generalisation."
    )


if __name__ == "__main__":
    main()
