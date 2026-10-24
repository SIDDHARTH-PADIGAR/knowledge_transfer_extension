
import os
import uuid
from datetime import datetime, timezone

import streamlit as st

from src.knowledge_transfer.models import Evidence, EvidenceType
from src.knowledge_transfer.llm_candidates import detect_hybrid_gaps
from src.knowledge_transfer.coverage import GapFinding


st.set_page_config(
    page_title="Knowledge Transfer",
    page_icon="KT",
    layout="wide",
)

st.title("Knowledge Transfer")
st.caption("Evidence-backed handover gaps and successor readiness")

if "evidence_records" not in st.session_state:
    st.session_state.evidence_records = []

if "findings" not in st.session_state:
    st.session_state.findings = []

if "gap_status" not in st.session_state:
    st.session_state.gap_status = {}

if "verification" not in st.session_state:
    st.session_state.verification = {}

with st.sidebar:
    st.header("Configuration")
    model = st.text_input(
        "Groq model",
        value="openai/gpt-oss-120b",
    )
    responsibility_id = st.text_input(
        "Responsibility ID",
        value="R-01",
    )
    responsibility_title = st.text_input(
        "Responsibility",
        value="Supplier and payment operations",
    )
    st.caption(
        "Keep GROQ_API_KEY in your environment. "
        "Never paste API keys into this app."
    )

st.subheader("1. Add handover evidence")

with st.form("evidence_form", clear_on_submit=True):
    source = st.text_input("Source name", placeholder="e.g. refund_sop")
    evidence_type = st.selectbox(
        "Evidence type",
        options=[
            EvidenceType.SOP,
            EvidenceType.TRANSCRIPT,
            EvidenceType.TASK_OUTPUT,
            EvidenceType.VERIFICATION_RECORD,
        ],
        format_func=lambda item: item.value.replace("_", " ").title(),
    )
    content = st.text_area(
        "Paste document or transcript content",
        height=180,
    )
    submitted = st.form_submit_button("Add evidence")

    if submitted:
        if not source.strip() or not content.strip():
            st.error("Enter both a source name and evidence content.")
        else:
            record = Evidence(
                id=f"E-{uuid.uuid4().hex[:8]}",
                source=source.strip(),
                evidence_type=evidence_type,
                content=content.strip(),
            )
            st.session_state.evidence_records.append(record)
            st.success(f"Added evidence: {record.id}")

records = st.session_state.evidence_records

if records:
    st.write(f"**Evidence records:** {len(records)}")
    for record in records:
        with st.expander(
            f"{record.id} · {record.source} · {record.evidence_type.value}"
        ):
            st.write(record.content)
            if st.button("Remove evidence", key=f"remove_{record.id}"):
                st.session_state.evidence_records = [
                    item for item in records if item.id != record.id
                ]
                st.rerun()
else:
    st.info("Add an SOP and its corresponding handover transcript to begin.")

st.divider()
st.subheader("2. Detect knowledge gaps")

if st.button("Analyse handover", type="primary"):
    if not any(r.evidence_type == EvidenceType.SOP for r in records):
        st.error("Add at least one SOP.")
    elif not any(
        r.evidence_type == EvidenceType.TRANSCRIPT for r in records
    ):
        st.error("Add at least one handover transcript.")
    elif not os.environ.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is not configured in this terminal.")
    else:
        with st.spinner("Comparing evidence and validating findings..."):
            result = detect_hybrid_gaps(
                responsibility_id=responsibility_id.strip(),
                evidence_records=records,
                model=model.strip(),
            )
        st.session_state.findings = list(result.findings)
        st.session_state.last_run = {
            "status": result.llm_status,
            "errors": result.errors,
            "rejected": result.rejected_candidates,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        for finding in result.findings:
            st.session_state.gap_status.setdefault(
                finding.title, "Open"
            )
        st.rerun()

last_run = st.session_state.get("last_run")
if last_run:
    st.caption(
        f"Last analysis: {last_run['timestamp']} · "
        f"Provider status: {last_run['status']} · "
        f"Rejected candidates: {last_run['rejected']}"
    )
    for error in last_run["errors"]:
        st.warning(error)

st.divider()
st.subheader("3. Review and resolve findings")

findings = st.session_state.findings
if not findings:
    st.info("No findings yet. Run an analysis to populate this section.")
else:
    for index, finding in enumerate(findings, start=1):
        with st.container(border=True):
            st.markdown(f"**{index}. {finding.title}**")
            st.write(finding.description)
            st.caption(
                f"Responsibility: {finding.responsibility_id} · "
                f"Evidence: {', '.join(finding.evidence_ids)}"
            )

            for evidence_id in finding.evidence_ids:
                linked = [r for r in records if r.id == evidence_id]
                for item in linked:
                    with st.expander(
                        f"View supporting source: {item.source}"
                    ):
                        st.write(item.content)

            status = st.selectbox(
                "Gap status",
                ["Open", "In progress", "Resolved"],
                key=f"status_{index}_{finding.title}",
                index=["Open", "In progress", "Resolved"].index(
                    st.session_state.gap_status.get(
                        finding.title, "Open"
                    )
                ),
            )
            st.session_state.gap_status[finding.title] = status

            if status == "Resolved":
                resolution = st.text_input(
                    "Resolution evidence or note",
                    key=f"resolution_{index}_{finding.title}",
                )
                if resolution.strip():
                    st.session_state.gap_status[
                        finding.title
                    ] = "Resolved"

st.divider()
st.subheader("4. Successor readiness verification")

st.write(
    "A demonstration alone does not establish readiness. "
    "Record an assessed outcome, reviewer, criteria, and evidence."
)

with st.form("verification_form"):
    successor = st.text_input("Successor")
    criteria = st.text_area("Assessment criteria")
    outcome = st.selectbox(
        "Assessment outcome",
        ["Incomplete", "Passed", "Failed"],
    )
    reviewer = st.text_input("Reviewer")
    verification_evidence = st.text_area(
        "Evidence of assessment",
        placeholder="Describe the observed task output or practical assessment.",
    )
    verified = st.form_submit_button("Record verification")

    if verified:
        if not all(
            value.strip()
            for value in (
                successor,
                criteria,
                reviewer,
                verification_evidence,
            )
        ):
            st.error("Complete every verification field.")
        else:
            st.session_state.verification[responsibility_id] = {
                "successor": successor.strip(),
                "criteria": criteria.strip(),
                "outcome": outcome,
                "reviewer": reviewer.strip(),
                "evidence": verification_evidence.strip(),
                "verified_at": (
                    datetime.now(timezone.utc).isoformat()
                    if outcome == "Passed"
                    else None
                ),
            }
            st.success("Assessment recorded.")

verification = st.session_state.verification.get(responsibility_id)

if verification:
    is_verified = (
        verification["outcome"] == "Passed"
        and verification["verified_at"] is not None
        and bool(verification["criteria"])
        and bool(verification["reviewer"])
        and bool(verification["evidence"])
    )
    st.metric(
        "Successor readiness",
        "Verified" if is_verified else "Unverified",
    )
    st.caption(
        f"Successor: {verification['successor']} · "
        f"Outcome: {verification['outcome']} · "
        f"Reviewer: {verification['reviewer']}"
    )
else:
    st.metric("Successor readiness", "Unverified")

st.divider()
st.subheader("Current handover summary")

col1, col2, col3 = st.columns(3)
col1.metric("Evidence records", len(records))
col2.metric("Detected findings", len(findings))
col3.metric(
    "Open gaps",
    sum(
        st.session_state.gap_status.get(f.title, "Open") != "Resolved"
        for f in findings
    ),
)
