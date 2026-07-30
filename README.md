# Conversation Intelligence Lab

[![tests](https://github.com/94spec/conversation-intelligence-lab/actions/workflows/tests.yml/badge.svg)](https://github.com/94spec/conversation-intelligence-lab/actions/workflows/tests.yml)
[![release](https://img.shields.io/github/v/release/94spec/conversation-intelligence-lab)](https://github.com/94spec/conversation-intelligence-lab/releases/latest)

Reference implementation for turning deal-level conversation signals into traceable sales
analysis. It validates structured LLM outputs, aggregates complete conversation sequences, and
builds evidence-linked monthly reports from deterministic fixtures.

**What this repository is.** A clean-room implementation of the analysis method I use in
production, written from scratch on synthetic data. It contains no employer code, transcripts,
prompts or configuration — the `SYN-` identifier prefix is enforced by the validator precisely
so that a real deal id cannot enter this repository by accident. What it does carry is the
part that matters: explicit denominators, a strict output contract, contradiction checks, and
a report where every aggregate can be traced back to the records behind it.

The same method applied to real commercial data is described, without confidential figures,
at [94spec.github.io/#analytics](https://94spec.github.io/#analytics).

## What it shows

- a strict JSON contract for per-deal LLM output;
- deal-level aggregation across complete conversation sequences;
- monthly comparisons with explicit denominators;
- quality flags for contradictory classifications;
- a deterministic offline pipeline with synthetic fixtures;
- unit tests for the core analytical calculations.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -e .

ci-lab validate data/synthetic_deals.jsonl
ci-lab report data/synthetic_deals.jsonl --output report.md
python -m unittest discover -s tests
```

The project has no runtime dependencies and does not require an API key. The tests run
straight from a checkout, without installing anything.

## Reproducible result

- [Generated sample report](examples/sample-report.md)
- [System design and evidence index](docs/system-evidence.md)
- [Detailed architecture decisions](docs/architecture.md)
- [Structured-output schema](schemas/deal_analysis.schema.json)
- [Synthetic input records](data/synthetic_deals.jsonl)

The checked-in sample report is generated from the synthetic dataset by the same CLI covered by CI.

## Pipeline

```text
conversation sequence
        ↓
LLM structured output (represented by synthetic fixtures here)
        ↓
schema and consistency validation
        ↓
deal-level analytical table
        ↓
monthly aggregates + evidence-aware narrative
```

The repository starts at the structured-output boundary. Upstream adapters connect
transcription ingestion, model providers, prompt versioning, retries, access control, and human
review workflows.

## Evidence standard

The report separates observations from explanations. A decline in high purchase readiness may
support a traffic-quality hypothesis, but on its own it does not prove the cause of a conversion
change — so the report states it as a hypothesis and names what would test it.

Every percentage includes its denominator, and every aggregate can be traced back to the
synthetic deal IDs behind it.

## Repository map

```text
data/                         synthetic input
schemas/                      LLM output contract
src/ci_lab/                   validation and reporting
tests/                        deterministic unit tests
docs/architecture.md          production boundary and design decisions
docs/system-evidence.md       architecture map and evidence index
```

## Privacy

All records are fictional. No transcript, identifier, URL, product rule, or employer artifact is included.

## License

MIT
