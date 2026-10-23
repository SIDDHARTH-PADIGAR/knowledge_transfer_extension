
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.knowledge_transfer.evidence import validate_evidence_links
from src.knowledge_transfer.llm_candidates import detect_hybrid_gaps
from src.knowledge_transfer.models import Evidence, EvidenceType, Responsibility


def main():
    scenarios_path = ROOT / "evaluation" / "heldout_scenarios.json"
    expected_path = ROOT / "evaluation" / "heldout_expected_outcomes.json"
    
    scenarios_data = json.loads(scenarios_path.read_text(encoding="utf-8"))
    expected_data = json.loads(expected_path.read_text(encoding="utf-8"))

    scenarios = (
        scenarios_data["scenarios"]
        if isinstance(scenarios_data, dict) and "scenarios" in scenarios_data
        else scenarios_data
    )

    if isinstance(scenarios, dict):
        scenarios = list(scenarios.values())

    if isinstance(expected_data, dict):
        expected_scenarios = expected_data.get("scenarios", [])
    else:
        expected_scenarios = expected_data

    expected_scenarios = expected_data["outcomes"]
    expected_by_id = {item["scenario_id"]: item for item in expected_scenarios}

    print("HELD-OUT HYBRID EVALUATION")
    print("=" * 40)

    total_expected = 0
    total_matched = 0
    total_detected = 0

    for scenario in scenarios:
        scenario_id = scenario["id"]
        expected = expected_by_id[scenario_id]
        materials = scenario.get("materials", scenario.get("evidence", []))

        evidence = []
        for index, material in enumerate(materials):
            if isinstance(material, str):
                source = f"{scenario_id}-source-{index + 1}"
                content = material
                evidence_type = EvidenceType.TRANSCRIPT
            else:
                source = material.get("source", f"{scenario_id}-source-{index + 1}")
                content = material.get("content", material.get("text", ""))
                raw_type = material.get("type", "transcript").lower()
                try:
                    evidence_type = EvidenceType(raw_type)
                except ValueError:
                    evidence_type = EvidenceType.TRANSCRIPT

            evidence.append(
                Evidence(
                    id=f"{scenario_id}-E{index + 1}",
                    source=source,
                    evidence_type=evidence_type,
                    content=content,
                )
            )

        responsibility = Responsibility(
            id=scenario_id,
            title=scenario.get("title", scenario_id),
            description="Held-out evaluation responsibility",
            owner="Current owner",
            successor="Successor",
            evidence_ids=[item.id for item in evidence],
        )

        link_errors = validate_evidence_links(responsibility, evidence)
        if link_errors:
            print(f"\n{scenario_id}: INVALID EVIDENCE LINKS: {link_errors}")
            continue

        result = detect_hybrid_gaps(
            responsibility_id=scenario_id,
            evidence_records=evidence,
        )

        expected_gaps = expected.get("expected_gaps", expected.get("gaps", []))
        expected_titles = {
            gap if isinstance(gap, str) else gap["title"]
            for gap in expected_gaps
        }
        detected_titles = {finding.title for finding in result.findings}

        matched = expected_titles & detected_titles
        missed = expected_titles - detected_titles
        unexpected = detected_titles - expected_titles

        total_expected += len(expected_titles)
        total_matched += len(matched)
        total_detected += len(detected_titles)

        print(f"\n{scenario_id}: {scenario.get('title', '')}")
        print(f"  LLM status: {result.llm_status}")
        print(f"  Expected gaps: {len(expected_titles)}")
        print(f"  Detected gaps: {len(detected_titles)}")
        print(f"  Exact-title matches: {len(matched)}")
        print(f"  Missed expected titles: {sorted(missed)}")
        print(f"  Unexpected titles: {sorted(unexpected)}")
        print(f"  Rejected candidates: {result.rejected_candidates}")

        for error in result.errors:
            print(f"  Model error: {error}")

        for finding in result.findings:
            linked_ids = {item.id for item in evidence}
            traceable = bool(finding.evidence_ids) and set(finding.evidence_ids).issubset(linked_ids)
            print(f"  Finding: {finding.title}")
            print(f"    Evidence IDs: {list(finding.evidence_ids)}")
            print(f"    Traceable: {traceable}")

    precision = total_matched / total_detected if total_detected else 0.0
    recall = total_matched / total_expected if total_expected else 0.0

    print("\nSUMMARY")
    print(f"Expected gaps: {total_expected}")
    print(f"Detected gaps: {total_detected}")
    print(f"Exact-title matches: {total_matched}")
    print(f"Exact-title precision: {precision:.3f}")
    print(f"Exact-title recall: {recall:.3f}")
    print("Note: exact-title matching does not measure semantic equivalence.")
    print("This small held-out set is an evaluation, not proof of generalisation.")


if __name__ == "__main__":
    main()
