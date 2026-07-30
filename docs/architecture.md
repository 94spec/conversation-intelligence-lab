# Architecture

## Scope

The offline reference implementation begins after semantic extraction. Synthetic JSONL records
represent validated structured outputs consumed by the analytical pipeline.

The boundary keeps execution:

- deterministic;
- free to run;
- independent from a model provider;
- isolated from external data and model calls.

## End-to-end deployment topology

```text
ingestion
  ├── call metadata
  ├── transcript sequence
  └── deal outcome
        ↓
eligibility filter
        ↓
versioned extraction prompt + strict output schema
        ↓
validation and retry policy
        ↓
deal-level analytical record
        ↓
warehouse / BI / report generation
        ↓
human review and taxonomy feedback
```

## Design decisions

### Deal is the unit of analysis

A deal may contain several calls. Evaluating only one call can lose follow-up outcomes, payment events, or later objections.

### Taxonomy precedes prompting

Business questions must be converted into mutually understandable fields, enum values, evidence requirements, and insufficient-data behavior before a prompt is written.

### Aggregation is deterministic

The LLM extracts meaning at the interaction level. Percentages, denominators, comparisons, and quality flags are calculated in code.

### Aggregates remain traceable

Reports expose the source deal IDs for every monthly aggregate. Deployment interfaces can add
drill-down access with role-based authorization.

### Correlation is not causation

The pipeline can show that two indicators moved together. Causal conclusions require a separate experimental or quasi-experimental design.
