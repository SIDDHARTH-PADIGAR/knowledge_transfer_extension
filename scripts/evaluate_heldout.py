
import json
from pathlib import Path

from src.knowledge_transfer.coverage import detect_knowledge_gaps
from src.knowledge_transfer.models import Evidence, EvidenceType


ROOT = Path(__file__).resolve().parents[1]


def load_json(filename: str) -> dict:
    return json.loads(
        (ROOT / "evaluation" / filename).read_text(encoding="utf-8")
    )


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
    scenarios = load_json("heldout_scenarios.json")["scenarios"]
    outcomes = load_json("heldout_expected_outcomes.json")["outcomes"]
    expected_by_id = {item["scenario_id"]: item for item in outcomes}

    expected_total = 0
    detected_total = 0
    matched_total = 0
    readiness_correct = 0

    print("HELD-OUT BASELINE EVALUATION")
    print("=" * 32)

    for scenario in scenarios:
        sid = scenario["id"]
        expected = expected_by_id[sid]
        evidence = build_evidence(scenario)
        findings = detect_knowledge_gaps(sid, evidence)

        expected_gaps = set(expected["expected_gaps"])
        detected_gaps = {finding.title for finding in findings}

        matched = expected_gaps & detected_gaps
        missed = expected_gaps - detected_gaps
        unexpected = detected_gaps - expected_gaps

        expected_total += len(expected_gaps)
        detected_total += len(detected_gaps)
        matched_total += len(matched)

        verification_text = " ".join(
            item.content.casefold()
            for item in evidence
            if item.evidence_type == EvidenceType.VERIFICATION_RECORD
        )

        required_phrases = (
            "assessment criterion:",
            "outcome: passed",
            "evidence:",
            "reviewer:",
            "verification status: confirmed",
        )
        actual_readiness = (
            "verified"
            if all(phrase in verification_text for phrase in required_phrases)
            else "unverified"
        )

        readiness_ok = actual_readiness == expected["expected_readiness"]
        readiness_correct += int(readiness_ok)

        print(f"\n{sid}: {scenario['title']}")
        print(f"  Expected gaps: {len(expected_gaps)}")
        print(f"  Detected gaps: {len(detected_gaps)}")
        print(f"  Matched: {len(matched)}")
        print(f"  Missed: {sorted(missed)}")
        print(f"  Unexpected: {sorted(unexpected)}")
        print(
            f"  Readiness: expected={expected['expected_readiness']}, "
            f"actual={actual_readiness}, "
            f"{'PASS' if readiness_ok else 'FAIL'}"
        )

    precision = matched_total / detected_total if detected_total else 0.0
    recall = matched_total / expected_total if expected_total else 0.0
    accuracy = readiness_correct / len(scenarios) if scenarios else 0.0

    print("\nSUMMARY")
    print("-" * 32)
    print(f"Scenarios: {len(scenarios)}")
    print(f"Expected gaps: {expected_total}")
    print(f"Detected gaps: {detected_total}")
    print(f"Matched gaps: {matched_total}")
    print(f"Gap precision: {precision:.3f}")
    print(f"Gap recall: {recall:.3f}")
    print(f"Readiness accuracy: {accuracy:.3f}")
    print("Detector rules were not changed for this evaluation.")
    print("Results are limited to this small, human-authored benchmark.")


if __name__ == "__main__":
    main()
