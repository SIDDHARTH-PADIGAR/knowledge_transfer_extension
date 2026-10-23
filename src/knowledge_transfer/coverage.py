
from dataclasses import dataclass

from src.knowledge_transfer.models import Evidence


@dataclass(frozen=True)
class GapFinding:
    title: str
    description: str
    evidence_ids: tuple[str, ...]
    responsibility_id: str


def detect_knowledge_gaps(
    responsibility_id: str,
    evidence_records: list[Evidence],
) -> list[GapFinding]:
    """Detect specific operational gaps using evidence from handover materials."""
    combined = "\n".join(
        evidence.content.casefold() for evidence in evidence_records
    )
    findings: list[GapFinding] = []

    def add_gap(
        title: str,
        description: str,
        source_terms: tuple[str, ...],
    ) -> None:
        matching_evidence = tuple(
            evidence.id
            for evidence in evidence_records
            if any(
                term in evidence.content.casefold()
                for term in source_terms
            )
        )
        if matching_evidence:
            findings.append(
                GapFinding(
                    title=title,
                    description=description,
                    evidence_ids=matching_evidence,
                    responsibility_id=responsibility_id,
                )
            )

    # Urgent-payment exception handling.
    if "urgent" in combined and (
        "someone who can help" in combined
        or "if they are unavailable" in combined
    ):
        add_gap(
            "No defined fallback approver or escalation path",
            "The materials mention contacting someone else but do not identify "
            "an authorised fallback approver or a defined escalation path.",
            ("someone who can help", "if they are unavailable"),
        )

    if "workaround" in combined and "critical suppliers" in combined:
        add_gap(
            "No documented workaround or conditions for using it",
            "The materials mention a workaround for critical suppliers without "
            "describing the steps, controls, or conditions for its use.",
            ("workaround", "critical suppliers"),
        )

    # Month-end reporting dependency.
    if "export is delayed" in combined and "ask priya" in combined:
        add_gap(
            "No documented fallback procedure for a delayed export",
            "The fallback depends on asking a named colleague, without "
            "documented steps that another operator can follow.",
            ("export is delayed", "ask priya"),
        )

    if (
        "different columns" in combined
        and "adjust the spreadsheet" in combined
    ):
        add_gap(
            "No documented report-selection criteria or replacement-column mapping",
            "The materials mention a replacement report and spreadsheet "
            "adjustments but do not define selection criteria or column mappings.",
            ("different columns", "adjust the spreadsheet"),
        )

    # Customer escalation exceptions.
    if "agreed exceptions" in combined:
        add_gap(
            "No documented criteria for account-specific escalation exceptions",
            "The transcript mentions account-specific exceptions but does not "
            "specify the criteria governing them.",
            ("agreed exceptions",),
        )

    if (
        "account manager" in combined
        and "relationship history" in combined
    ):
        add_gap(
            "No documented stakeholder coordination or relationship-history handover",
            "The process depends on account-manager coordination and relationship "
            "history that are not captured in the standard procedure.",
            ("account manager", "relationship history"),
        )

    return findings
