
from src.knowledge_transfer.evidence import find_evidence, validate_evidence_links
from src.knowledge_transfer.models import Evidence, EvidenceType, Responsibility


def make_evidence(
    evidence_id: str,
    source: str,
    content: str,
) -> Evidence:
    return Evidence(
        id=evidence_id,
        source=source,
        evidence_type=EvidenceType.SOP,
        content=content,
    )


def test_valid_evidence_links():
    responsibility = Responsibility(
        id="R-01",
        title="Process invoices",
        description="Match invoices against purchase orders.",
        owner="Finance",
        evidence_ids=["E-01"],
    )

    evidence = [make_evidence("E-01", "invoice_sop", "Match invoice to PO.")]

    assert validate_evidence_links(responsibility, evidence) == []


def test_missing_evidence_link_is_reported():
    responsibility = Responsibility(
        id="R-01",
        title="Process invoices",
        description="Match invoices against purchase orders.",
        owner="Finance",
        evidence_ids=["E-MISSING"],
    )

    assert validate_evidence_links(responsibility, []) == [
        "Evidence 'E-MISSING' does not exist."
    ]


def test_duplicate_evidence_ids_are_reported():
    responsibility = Responsibility(
        id="R-01",
        title="Process invoices",
        description="Match invoices against purchase orders.",
        owner="Finance",
    )

    evidence = [
        make_evidence("E-01", "sop", "First record."),
        make_evidence("E-01", "transcript", "Second record."),
    ]

    assert validate_evidence_links(responsibility, evidence) == [
        "Duplicate evidence IDs exist."
    ]


def test_find_evidence_searches_content_case_insensitively():
    evidence = [
        make_evidence("E-01", "payment_sop", "Finance manager approval required."),
        make_evidence("E-02", "invoice_sop", "Match invoice to purchase order."),
    ]

    results = find_evidence(evidence, "FINANCE MANAGER")

    assert [item.id for item in results] == ["E-01"]


def test_find_evidence_returns_empty_for_blank_query():
    evidence = [make_evidence("E-01", "invoice_sop", "Match invoice to PO.")]

    assert find_evidence(evidence, "   ") == []
