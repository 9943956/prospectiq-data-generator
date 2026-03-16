# ProspectIQ Demo Data Generator

A deterministic, seed-based data generator that produces realistic, internally consistent demo data for a B2B sales product. Covers the full sales motion: **Companies → Contacts → Reps → Deals → Emails → Meetings**.

---

## Quick Start

```bash
# 1. Clone / download the repo
# 2. No external dependencies — uses Python standard library only

python generate.py --seed 42 --companies 15 --industries saas,healthcare,finserv,manufacturing
```

Output files appear in `./output/` by default.

### All CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--seed` | `42` | Integer seed for full determinism |
| `--companies` | `15` | Number of companies to generate |
| `--industries` | `saas,healthcare,finserv,manufacturing` | Comma-separated industry filter |
| `--reps` | `6` | Number of sales reps |
| `--out` | `output` | Output directory |
| `--format` | `csv` | Output format: `csv` or `json` |

### Examples

```bash
# Healthcare + SaaS only, larger dataset
python generate.py --seed 99 --companies 30 --industries healthcare,saas

# JSON output for API ingestion
python generate.py --seed 42 --companies 15 --format json

# Reproducible run with custom output folder
python generate.py --seed 7 --companies 20 --out my_data
```

### Requirements

- Python 3.10+ (uses built-in `random`, `csv`, `json`, `uuid`, `datetime`, `argparse`)
- **No pip installs required**

---

## 1. Architecture & Tools

### Language & Libraries
The generator is a **single Python file** (`generate.py`) using only the standard library — no external dependencies, no LLM API calls at runtime.

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python 3.10+ | Universal, easy to run locally, zero setup friction |
| Randomness | `random.Random(seed)` | Instance-level RNG; fully deterministic; isolated from global state |
| Output | `csv` / `json` | Both formats supported via `--format` flag |
| LLMs | None at runtime | All text templates are pre-written; LLMs were used during design to draft template copy and business logic rules |

### Cost Controls
- Zero API cost at runtime — all generation is local and template-driven.
- LLM assistance was used once during development (prompt engineering to draft email/meeting body templates and business logic rules), not in the generation loop.

---

## 2. Data Model

### Entity Relationship Diagram

```
Companies ──< Contacts
    │
    └──< Deals >── Reps
              │
              ├──< Emails (threads)
              └──< Meetings
```

### Keys & Foreign Keys

| Entity | PK | FKs |
|--------|----|-----|
| `companies` | `company_id` | — |
| `contacts` | `contact_id` | `company_id → companies` |
| `sales_reps` | `rep_id` | — |
| `deals` | `deal_id` | `company_id`, `primary_contact_id`, `rep_id` |
| `emails` | `email_id` | `deal_id`, `sender_id` (contact or rep), `in_reply_to_email_id` |
| `meetings` | `meeting_id` | `deal_id`, `attendee_ids[]` (contacts + reps) |

All foreign keys are validated at generation time — if a referenced entity doesn't exist, it is never emitted.

---

## 3. Business Logic

### Deal Values by Company Size

| Growth Stage | Deal Value Range |
|-------------|-----------------|
| Startup | $5,000 – $25,000 |
| Scaleup | $25,000 – $150,000 |
| Enterprise | $150,000 – $800,000 |

### Stage Timing
- `opened_at`: random date within a 6-month window from Jan 2024.
- `expected_close_at`: 30–90 days after `opened_at` (uniform random).
- `closed_at`: set only for `Closed-Won` / `Closed-Lost`; always ≤ `expected_close_at`.

### Deal Health → Behavioral Patterns

| Health | Email Sentiment | Inbound Latency | Meeting Outcome |
|--------|----------------|-----------------|-----------------|
| Positive | 55–70% Positive | < 48h median | High `completed` rate |
| Neutral | 25–40% Positive | 48–72h median | Mix of completed/rescheduled |
| Negative | ≤ 20% Positive | > 120h median | High rescheduled/no-show |

### Rep Tiers & Targets

| Tier | Deals Closed / Quarter |
|------|----------------------|
| Top | 8–12 |
| Good | 5–8 |
| Average | 3–5 |
| Underperformer | 1–3 |

---

## 4. Consistency Guarantees

### Timeline Coherence
- Email `timestamp` and meeting `scheduled_start` are always within `[opened_at, closed_at]`.
- Thread emails are strictly ordered by `timestamp`; `sequence_index` is contiguous from 0.
- `in_reply_to_email_id` always points to the immediately prior email in the same thread.
- `reply_latency_hours` for inbound emails equals the actual delta from the previous message.

### Thread Memory
- After the first email in a thread, subsequent bodies open with `"Following up on [prior subject] —"` to simulate genuine context carryover.
- Meeting notes reference prior email subjects for the first meeting in a deal.

### Name & Reference Alignment
- Contact names, rep names, company names, and `contact_id`/`rep_id` values are consistent across all entities — generated once and referenced by ID everywhere.
- Email `sender_id` and `recipient_ids` always resolve to valid `contact_id` or `rep_id` values.

### Contradiction Prevention
- All timestamps are generated sequentially within a deal's window; a hard clamp ensures no activity exceeds `closed_at`.
- Stage-appropriate vocabulary: email subjects and meeting titles are drawn from stage-specific pools (e.g., Prospecting emails never mention "contract redlines").

---

## 5. Scalability: Industry Packs

Each industry has its own tracker vocabulary (≥ 12 trackers) defined in `INDUSTRY_TRACKERS`:

```python
INDUSTRY_TRACKERS = {
    "SaaS":                 ["SSO", "SOC2", "API limits", "RBAC", ...],
    "Healthcare":           ["HIPAA", "PHI", "EHR integration", "HL7 FHIR", ...],
    "Financial Services":   ["SOX compliance", "PCI-DSS", "AML", "KYC", ...],
    "Manufacturing":        ["ERP integration", "supply chain", "IoT sensors", ...],
}
```

To **add a new industry pack** (e.g., Legal Tech or Retail), you only need to:

1. Add an entry to `INDUSTRY_MAP` (`"legaltech": "Legal Technology"`).
2. Add a tracker list to `INDUSTRY_TRACKERS`.
3. Add a `context_note()` entry for the three growth stages.

No other code changes are required. The generation pipeline is industry-agnostic.

---

## 6. Generation Flow (Sequence Diagram)

```
CLI Args
   │
   ▼
main()
   │
   ├─[1]─► gen_companies(n, industries, rng)
   │           └── returns companies[]
   │
   ├─[2]─► gen_contacts(companies, rng)
   │           └── returns contacts[]  (2–5 per company)
   │
   ├─[3]─► gen_reps(n_reps, rng)
   │           └── returns reps[]
   │
   ├─[4]─► gen_deals(companies, contacts, reps, rng)
   │           └── assigns stage, health, value, timeline
   │           └── returns deals[]
   │
   ├─[5]─► gen_emails(deals, companies, contacts, reps, rng)
   │           └── per deal: build threads, subjects, bodies
   │           └── enforces latency, sentiment, sequence_index
   │           └── returns emails[]
   │
   ├─[6]─► gen_meetings(deals, ..., emails, rng)
   │           └── canonical path: Discovery→Demo→Tech Dive→Proposal→Decision
   │           └── notes reference prior email subjects
   │           └── attendees vary by meeting type
   │           └── returns meetings[]
   │
   └──────► write_csv / write_json  →  ./output/
```

Each generator receives only the entities it depends on (no global state). The `rng` instance is passed through so the full run is reproducible from a single `--seed`.

---

## Output Files

| File | Rows (default run) | Description |
|------|--------------------|-------------|
| `companies.csv` | 15 | B2B companies with industry/stage/revenue |
| `contacts.csv` | ~45–75 | Contacts per company with seniority/title |
| `sales_reps.csv` | 6 | Reps with tier and quota targets |
| `deals.csv` | ~25–45 | Deals with stage, health, value, timeline |
| `emails.csv` | ~200–400 | Email threads with full metadata |
| `meetings.csv` | ~70–130 | Meeting records with notes and outcomes |

All row counts scale proportionally with `--companies` and `--reps`.

---

## Validation Checklist

| Rule | How It's Met |
|------|-------------|
| All FKs resolve | IDs are generated first; child entities always reference existing parent IDs |
| Thread `sequence_index` is continuous | Emails per thread are emitted in order starting at 0 |
| `in_reply_to_email_id` points to prior message | Set to `prev_email_id` which is updated per iteration |
| `reply_latency_hours` matches actual delta | Computed from `timedelta` between consecutive thread timestamps |
| Sentiment distribution matches health | Weighted `rng.choices()` per health tier |
| Meeting titles match stage sequence | Drawn from `MEETING_SEQ` array in canonical order |
| At least one meeting references a prior email | First meeting's notes prepend the deal's first email subject |
| Trackers appear across both emails and meetings | `trackers` sampled from industry list for every entity |
| Deal values scale with company size | `deal_value()` function dispatches by `growth_stage` |
| Average cycle time 30–90 days | `cycle = rng.randint(30, 90)` per deal |
