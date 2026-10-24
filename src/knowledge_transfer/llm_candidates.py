
import json
import os
from dataclasses import dataclass

from groq import Groq

from src.knowledge_transfer.coverage import (
    GapFinding,
    detect_knowledge_gaps,
)
from src.knowledge_transfer.models import Evidence
from src.knowledge_transfer.validation import (
    validate_exact_quote,
    validate_finding,
)


@dataclass(frozen=True)
class HybridResult:
    findings: tuple[GapFinding, ...]
    llm_status: str
    rejected_candidates: int
    errors: tuple[str, ...]


def _ask_ollama(
    evidence: list[Evidence],
    model: str = "openai/gpt-oss-120b",
    timeout: int = 90,
) -> dict:
    """Request evidence-grounded gap candidates from Groq."""
    materials = [
        {
            "id": item.id,
            "type": item.evidence_type.value,
            "source": item.source,
            "text": item.content,
        }
        for item in evidence
    ]

    prompt = f"""
Compare SOPs against transcripts. Identify concrete procedures,
exceptions, dependencies, or variations present in transcripts but
missing or unclear in SOPs.

Do not invent requirements or report procedures already covered by
the SOP. Every finding must cite an exact source sentence.

For each finding return:
- title: short descriptive title
- description: one concise sentence
- evidence_id: exact evidence ID
- quote: exact contiguous text copied from that evidence

Return at most 3 findings. Return an empty gaps array if none are
defensible.

Evidence:
{json.dumps(materials, ensure_ascii=False)}

Return JSON only:
{{"gaps":[{{"title":"...","description":"...","evidence_id":"...","quote":"..."}}]}}
""".strip()

    client = Groq(
        api_key=os.environ["GROQ_API_KEY"],
        timeout=timeout,
        max_retries=0,
    )

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_completion_tokens=700,
        response_format={"type": "json_object"},
    )

    content = response.choices[0].message.content
    if not content:
        raise ValueError("Groq returned an empty response.")

    result = json.loads(content)
    if not isinstance(result, dict) or not isinstance(result.get("gaps"), list):
        raise ValueError("Response must contain a gaps array.")

    return result


def detect_hybrid_gaps(
    responsibility_id: str,
    evidence_records: list[Evidence],
    model: str = "openai/gpt-oss-120b",
    timeout: int = 90,
) -> HybridResult:
    """Combine deterministic findings with validated Groq candidates."""
    baseline = detect_knowledge_gaps(
        responsibility_id,
        evidence_records,
    )
    accepted = {finding.title: finding for finding in baseline}

    try:
        response = _ask_ollama(evidence_records, model, timeout)
    except Exception as exc:
        return HybridResult(
            findings=tuple(accepted.values()),
            llm_status="unavailable_or_invalid",
            rejected_candidates=0,
            errors=(f"{type(exc).__name__}: {exc}",),
        )

    rejected = 0
    errors: list[str] = []
    evidence_by_id = {item.id: item for item in evidence_records}

    for candidate in response["gaps"]:
        if not isinstance(candidate, dict):
            rejected += 1
            errors.append("Candidate is not a JSON object.")
            continue

        title = candidate.get("title")
        description = candidate.get("description")
        evidence_id = candidate.get("evidence_id")
        quote = candidate.get("quote")

        if not all(
            isinstance(value, str) and value.strip()
            for value in (title, description, evidence_id, quote)
        ):
            rejected += 1
            errors.append("Candidate has missing or invalid fields.")
            continue

        if evidence_id not in evidence_by_id:
            rejected += 1
            errors.append(f"Unknown evidence ID: {evidence_id}")
            continue

        quote_check = validate_exact_quote(
            quote, evidence_id, evidence_records
        )
        if not quote_check.valid:
            rejected += 1
            errors.extend(quote_check.errors)
            continue

        finding = GapFinding(
            title=title.strip(),
            description=description.strip(),
            evidence_ids=(evidence_id,),
            responsibility_id=responsibility_id,
        )

        finding_check = validate_finding(finding, evidence_records)
        if not finding_check.valid:
            rejected += 1
            errors.extend(finding_check.errors)
            continue
        
        if finding.title in accepted:
            continue

        # Avoid duplicate findings with different titles.
        candidate_text = (
            finding.title + " " + finding.description
        ).lower()

        duplicate_terms = {
            "approver": ("approv", "authorit", "supervisor", "manager", "sign off"),
            "workaround": ("workaround", "critical supplier", "urgent payment"),
        }

        is_duplicate = False

        for existing in accepted.values():
            existing_text = (
                existing.title + " " + existing.description
            ).lower()

            candidate_topic = next(
                (
                    topic
                    for topic, terms in duplicate_terms.items()
                    if any(term in candidate_text for term in terms)
                ),
                None,
            )
            existing_topic = next(
                (
                    topic
                    for topic, terms in duplicate_terms.items()
                    if any(term in existing_text for term in terms)
                ),
                None,
            )

            if candidate_topic is not None and candidate_topic == existing_topic:
                is_duplicate = True
                break

        if is_duplicate:
            rejected += 1
            errors.append("Duplicate or overlapping finding rejected.")
            continue

        has_sop = any(
            item.evidence_type.value == "sop"
            for item in evidence_records
        )
        has_transcript = any(
            item.evidence_type.value == "transcript"
            for item in evidence_records
        )

        if not (has_sop and has_transcript):
            rejected += 1
            errors.append(
                "Cannot compare procedure coverage: "
                "SOP or transcript evidence is missing."
            )
            continue

        accepted[finding.title] = finding

    return HybridResult(
        findings=tuple(accepted.values()),
        llm_status="completed",
        rejected_candidates=rejected,
        errors=tuple(errors),
    )
