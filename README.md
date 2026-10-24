# Trupeer Knowledge Transfer

**Turn handovers into actionable knowledge gaps and measurable successor readiness.**

People leave. Critical decisions, exceptions, and workarounds often leave with them.

This MVP explores how Trupeer's workflow documentation could help teams identify what's missing from their SOPs, close handover gaps, and verify whether a successor is ready to take over.

## What it does

- **Finds knowledge gaps** by comparing documented procedures with handover transcripts.
- **Links findings to evidence** so reviewers can trace each gap to its source.
- **Tracks gap closure** from open to resolved.
- **Records successor readiness** against assessment criteria, reviewer feedback, and evidence.

## Demo

1. Add an SOP and its handover transcript.
2. Analyse the handover to identify missing procedures and undocumented exceptions.
3. Review evidence-linked findings and track their resolution.
4. Record a successor assessment and verify readiness.

## Evaluation

| Evaluation | Result |
|---|---|
| Initial benchmark | 6/6 scenarios matched expected gap titles |
| Held-out benchmark, local model | 0/3 expected gaps matched |
| Held-out benchmark, Groq hybrid | 0 exact-title matches; 4 findings returned for 3 expected gaps |
| Manual workflow check | Gap tracking and readiness state transitions verified |

The initial benchmark was small and informed by the scenarios used to build the rules. Held-out testing exposed the limits of generalisation and duplicate detection. These results are early evidence, not proof of production accuracy.

## Architecture

- **UI:** Streamlit
- **Models and validation:** Python, Pydantic
- **Gap detection:** Deterministic rules + Groq LLM
- **Evidence checks:** Source IDs and exact-quote validation
- **Evaluation:** Frozen scenarios and separate expected outcomes

## Run locally

```bash
pip install -r requirements.txt
pip install groq
```

Set `GROQ_API_KEY` in your environment, then run:

```bash
streamlit run app.py
```

Run tests:

```bash
python -m pytest -q
```

## Current limitations

- Prototype state is held in the Streamlit session; records are not durably stored.
- Evidence traceability does not guarantee that a finding is logically correct.
- Held-out results show that detection accuracy and duplicate handling need further validation.
- Successor verification is a recorded assessment, not an independent certification.
- This is a standalone MVP, not an integrated Trupeer product.

---

Built to explore how workflow documentation can become a living knowledge-transfer system, rather than a collection of static SOPs.