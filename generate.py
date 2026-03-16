"""
ProspectIQ Demo Data Generator
Usage: python generate.py --seed 42 --companies 15 --industries saas,healthcare,finserv
"""

import argparse
import csv
import json
import os
import random
import uuid
from datetime import datetime, timedelta
from itertools import count

# ── helpers ──────────────────────────────────────────────────────────────────

def make_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def write_csv(path: str, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

def write_json(path: str, rows: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)

# ── static data ───────────────────────────────────────────────────────────────

INDUSTRY_MAP = {
    "saas": "SaaS",
    "healthcare": "Healthcare",
    "finserv": "Financial Services",
    "manufacturing": "Manufacturing",
}

INDUSTRY_TRACKERS = {
    "SaaS": ["SSO", "SOC2", "API limits", "uptime SLA", "multi-tenant", "OAuth2",
             "rate limiting", "webhook", "sandbox env", "RBAC", "data residency", "SCIM provisioning"],
    "Healthcare": ["HIPAA", "PHI", "EHR integration", "EMR", "HL7 FHIR", "patient data",
                   "BAA", "clinical workflow", "interoperability", "audit trail", "VPN", "HITRUST"],
    "Financial Services": ["SOX compliance", "PCI-DSS", "AML", "KYC", "data encryption",
                           "audit log", "MFA", "FedRAMP", "regulatory reporting", "risk scoring",
                           "trade data", "reconciliation"],
    "Manufacturing": ["ERP integration", "supply chain", "IoT sensors", "OEE", "downtime tracking",
                      "MES", "SCADA", "predictive maintenance", "BOM", "inventory sync",
                      "quality control", "PLM"],
}

STAGE_ORDER = ["Prospecting", "Qualified", "Demo", "Proposal", "Negotiation", "Closed-Won", "Closed-Lost"]
ACTIVE_STAGES = ["Prospecting", "Qualified", "Demo", "Proposal", "Negotiation"]

MEETING_TITLES = {
    "Prospecting":  ["Discovery Call", "Intro Call"],
    "Qualified":    ["Qualification Review", "Business Needs Deep Dive"],
    "Demo":         ["Product Demo", "Live Demo Session"],
    "Proposal":     ["Proposal Review", "Technical Deep Dive"],
    "Negotiation":  ["Final Decision Meeting", "Contract Review Call"],
}

COMPANY_NAMES = [
    "Axion Technologies", "BlueRidge Analytics", "Cloudspan Systems", "DeltaCore Solutions",
    "Elevate Health", "Foundry Digital", "Graystone Financial", "Harbor Logistics",
    "Infinex Software", "Juno Medical", "Keyline Manufacturing", "Luminary Fintech",
    "Meridian Health", "NorthStar SaaS", "Orbis Capital", "Pinnacle Works",
    "Quantum Health Systems", "Redwood Platforms", "Silverline Industries", "Titan Analytics",
    "Unison Financial", "Vertex Manufacturing", "Wavefront Tech", "Xenon Health",
    "Yellowstone Data", "Zenith Financial", "Apex Robotics", "Beacon Software",
    "Cascade Medical", "Drift Analytics",
]

FIRST_NAMES = ["Alex", "Jordan", "Morgan", "Taylor", "Casey", "Riley", "Jamie", "Dana",
               "Chris", "Pat", "Sam", "Avery", "Blake", "Drew", "Emery", "Finley",
               "Harper", "Indigo", "Jesse", "Kendall", "Lane", "Marlowe", "Nico", "Oakley"]

LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
              "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
              "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Perez", "Thompson"]

REGIONS = ["US-West", "US-East", "US-Midwest", "US-South", "EU-West", "APAC", "LATAM"]

TITLES_BY_SENIORITY = {
    "IC":       ["Software Engineer", "Data Analyst", "Sales Development Rep", "Implementation Specialist", "Solutions Engineer"],
    "Manager":  ["Engineering Manager", "Sales Manager", "Operations Manager", "IT Manager", "Finance Manager"],
    "Director": ["Director of Engineering", "Director of Sales", "Director of IT", "Director of Operations"],
    "VP":       ["VP of Engineering", "VP of Sales", "VP of Operations", "VP of Finance"],
    "C-Level":  ["CTO", "CFO", "CEO", "COO", "CISO", "CPO"],
}

LOSS_REASONS = [
    "Budget constraints prevented deal closure",
    "Selected competitor with deeper native integrations",
    "Internal project deprioritized for fiscal year",
    "Champion left the company mid-cycle",
    "Security review failed to meet compliance requirements",
    "Pricing mismatch vs. expected budget",
    "No executive sponsorship to drive decision",
]

# ── business logic helpers ────────────────────────────────────────────────────

def revenue_for_stage(stage: str, employees: int) -> int:
    if stage == "Startup":
        return random.randint(500_000, 5_000_000)
    elif stage == "Scaleup":
        return random.randint(5_000_000, 50_000_000)
    else:
        return random.randint(50_000_000, 500_000_000)

def deal_value(growth_stage: str, employees: int) -> int:
    if growth_stage == "Startup":
        return random.randint(5_000, 25_000)
    elif growth_stage == "Scaleup":
        return random.randint(25_000, 150_000)
    else:
        return random.randint(150_000, 800_000)

def context_note(industry: str, growth_stage: str) -> str:
    notes = {
        "SaaS": {
            "Startup": "Early-stage team struggling with manual onboarding and lack of SSO; seeking scalable auth solutions.",
            "Scaleup": "Rapid user growth exposing API rate limit gaps and multi-tenant isolation issues.",
            "Enterprise": "Large engineering org requires SOC2-compliant data residency and SCIM provisioning for 2,000+ seats.",
        },
        "Healthcare": {
            "Startup": "Bootstrapped clinic network needing HIPAA-compliant data pipelines and EHR connectors.",
            "Scaleup": "Expanding telehealth platform facing PHI audit challenges and HL7 FHIR interoperability gaps.",
            "Enterprise": "Regional hospital system requiring BAA agreements, full audit trail, and EMR integration across 12 sites.",
        },
        "Financial Services": {
            "Startup": "Fintech startup building KYC workflows; needs PCI-DSS compliant data handling from day one.",
            "Scaleup": "Growth-stage lender adding AML monitoring and regulatory reporting to support Series B expansion.",
            "Enterprise": "Enterprise bank undergoing digital transformation; SOX compliance and trade data reconciliation are blockers.",
        },
        "Manufacturing": {
            "Startup": "Small-batch manufacturer looking to replace spreadsheets with ERP-integrated quality control tracking.",
            "Scaleup": "Mid-market shop floor automation initiative; IoT sensor data needs MES and SCADA integration.",
            "Enterprise": "Global manufacturer requiring PLM-to-ERP BOM sync and predictive maintenance across 8 facilities.",
        },
    }
    return notes.get(industry, {}).get(growth_stage, "Digital transformation initiative underway.")

def relationship_note(title: str, seniority: str, industry: str) -> str:
    if seniority == "C-Level":
        return f"Executive sponsor who approved the initial budget exploration; aligned on {industry} modernization goals."
    elif seniority == "VP":
        return f"Engaged during qualification call; owns the procurement decision and integration roadmap."
    elif seniority == "Director":
        return f"Day-to-day champion steering internal alignment; introduced us to the technical evaluators."
    elif seniority == "Manager":
        return f"Operational lead coordinating the evaluation; manages the team that will use the product daily."
    else:
        return f"Technical evaluator who ran the sandbox trial and flagged integration requirements."

def email_for(name: str, company: str) -> str:
    first, *last = name.lower().split()
    domain = company.lower().replace(" ", "") + ".com"
    return f"{first}.{''.join(last)[:8]}@{domain}"

def rep_email(name: str) -> str:
    first, *last = name.lower().split()
    return f"{first}.{''.join(last)[:8]}@prospectiq.com"

# ── sentiment helpers ─────────────────────────────────────────────────────────

def pick_sentiment(health: str, rng: random.Random) -> str:
    if health == "Positive":
        return rng.choices(["Positive", "Neutral", "Negative"], weights=[62, 30, 8])[0]
    elif health == "Neutral":
        return rng.choices(["Positive", "Neutral", "Negative"], weights=[32, 42, 26])[0]
    else:
        return rng.choices(["Positive", "Neutral", "Negative"], weights=[15, 37, 48])[0]

def reply_latency(health: str, rng: random.Random) -> int:
    if health == "Positive":
        return rng.randint(4, 36)
    elif health == "Neutral":
        return rng.randint(24, 96)
    else:
        return rng.randint(96, 200)

# ── email body generation (deterministic, no LLM) ────────────────────────────

STAGE_SUBJECTS = {
    "Prospecting": [
        "Reaching out re: {pain}",
        "Quick question about your {topic} workflow",
        "How {company} is solving {pain}",
    ],
    "Qualified": [
        "Following up on our discovery call",
        "Next steps after our conversation",
        "Resources on {topic} you requested",
    ],
    "Demo": [
        "Recording + next steps from today's demo",
        "Questions from the {company} demo session",
        "Demo follow-up: {topic} deep dive",
    ],
    "Proposal": [
        "ProspectIQ proposal for {company}",
        "Draft proposal — please review",
        "RE: Proposal questions on {topic}",
    ],
    "Negotiation": [
        "RE: Contract redlines from {company}",
        "Updated MSA — {topic} clauses addressed",
        "Final terms for review",
    ],
    "Closed-Won": ["Welcome aboard, {company}!"],
    "Closed-Lost": ["Following up on our evaluation"],
}

def build_subject(stage: str, company_name: str, trackers: list, rng: random.Random) -> str:
    templates = STAGE_SUBJECTS.get(stage, ["Update from ProspectIQ"])
    tmpl = rng.choice(templates)
    pain = rng.choice(trackers) if trackers else "integration"
    topic = rng.choice(trackers) if trackers else "workflow"
    return tmpl.format(company=company_name, pain=pain, topic=topic)

OUTBOUND_BODIES = {
    "Prospecting": (
        "Hi {contact_first}, I hope this finds you well. "
        "I've been following {company}'s growth and noticed you're likely wrestling with {pain}. "
        "At ProspectIQ, we've helped similar {industry} teams cut that friction by 40% on average. "
        "Many of our customers initially struggled with {topic} before switching to our platform. "
        "I'd love to show you a quick 20-minute overview tailored to your stack. "
        "Would you have time next week for a brief call? "
        "Happy to work around your schedule."
    ),
    "Qualified": (
        "Hi {contact_first}, great speaking with you earlier this week. "
        "As promised, I'm attaching the resources we discussed on {topic}. "
        "Based on your notes around {pain}, I've highlighted the sections most relevant to your use case. "
        "Our {industry} customers typically see ROI within the first quarter of deployment. "
        "I've looped in our solutions engineer to help answer any technical questions that come up. "
        "Let me know if you'd like to schedule a deeper dive with the broader team. "
        "Looking forward to continuing the conversation."
    ),
    "Demo": (
        "Hi {contact_first}, thank you for joining today's demo — it was a great session. "
        "Sharing the recording and the slide deck as discussed. "
        "I noticed the {topic} question resonated strongly with your team — I've added a dedicated section to our follow-up doc. "
        "For your {industry} environment specifically, the {pain} workflow we showed is already live with three similar customers. "
        "Next step is a technical deep dive with your {ic_title} to validate the integration path. "
        "I'll send a calendar invite shortly. "
        "Please don't hesitate to share the recording with other stakeholders."
    ),
    "Proposal": (
        "Hi {contact_first}, please find attached our formal proposal for {company}. "
        "The pricing reflects the scope we aligned on: {topic} coverage for your full team. "
        "I've included a phased rollout option that addresses the {pain} concern raised in last week's meeting. "
        "Legal has pre-cleared the {industry}-specific compliance clauses in section 4. "
        "We're happy to adjust the payment schedule if that helps with your budget cycle. "
        "Let me know if you'd like to walk through the proposal together on a call. "
        "We're targeting signature by end of month to meet your go-live date."
    ),
    "Negotiation": (
        "Hi {contact_first}, thank you for your team's comments on the draft MSA. "
        "I've worked through the redlines with our legal team and addressed the {topic} clauses in section 7. "
        "The {pain} indemnification language has been updated to reflect standard {industry} practice. "
        "We can accept the liability cap adjustment as proposed. "
        "One remaining open item is the data retention period — our team suggests 24 months as a compromise. "
        "Can we schedule a 30-minute call to close out the remaining points? "
        "We're very close and want to get this across the line."
    ),
}

INBOUND_BODIES = {
    "Prospecting": (
        "Hi {rep_first}, thanks for reaching out. "
        "We've actually been evaluating options in this space for the past few weeks. "
        "The {topic} angle you mentioned is relevant — we've had issues with {pain} for a while. "
        "Happy to jump on a quick call. "
        "Does Thursday afternoon work? "
        "Please send a calendar invite with a dial-in. "
        "Looking forward to learning more."
    ),
    "Qualified": (
        "Hi {rep_first}, thanks for sending over those resources. "
        "I shared the {topic} overview with my team and they had a few follow-up questions. "
        "Specifically, how does the platform handle {pain} at our scale? "
        "Also, can you confirm {industry} compliance certifications are current? "
        "We'd like to include our {ic_title} in the next conversation. "
        "Please send calendar options for next week. "
        "Appreciate the responsiveness so far."
    ),
    "Demo": (
        "Hi {rep_first}, appreciate you walking us through the platform today. "
        "The {topic} functionality was impressive — definitely addresses the core {pain} we outlined. "
        "Our {ic_title} wants to dig into the API side before we move forward. "
        "Can you share the technical documentation for the {industry} integration? "
        "Also, we'd like to understand the implementation timeline better. "
        "Send over availability for a technical session and we'll get something on the calendar. "
        "Good demo overall."
    ),
    "Proposal": (
        "Hi {rep_first}, we've reviewed the proposal internally. "
        "The pricing is higher than expected for the {topic} tier we discussed. "
        "Our CFO flagged the {pain} line item as needing justification before approval. "
        "Can you provide a breakdown of how the {industry} compliance features contribute to the overall cost? "
        "We're also wondering if a shorter initial term is possible to reduce risk. "
        "Please share an updated version reflecting a 12-month pilot. "
        "We want to move forward but need these addressed first."
    ),
    "Negotiation": (
        "Hi {rep_first}, our legal team reviewed the MSA draft. "
        "We have redlines on sections 5 and 7 — primarily around {pain} and data ownership. "
        "The {topic} clause needs to align with our {industry} compliance requirements. "
        "We're also requesting a 30-day cure period before termination for convenience. "
        "Finance has approved the budget pending these legal revisions. "
        "Once those are resolved, we can target signature within the week. "
        "Please share the revised doc when ready."
    ),
}

def build_body(
    direction: str, stage: str, contact_first: str, rep_first: str,
    company_name: str, industry: str, trackers: list, rng: random.Random,
    prior_ref: str = "", ic_title: str = "solutions engineer"
) -> str:
    bodies = OUTBOUND_BODIES if direction == "outbound" else INBOUND_BODIES
    template = bodies.get(stage, bodies.get("Qualified", ""))
    pain = rng.choice(trackers) if trackers else "integration"
    topic = rng.choice([t for t in trackers if t != pain] or trackers or ["workflow"])
    body = template.format(
        contact_first=contact_first,
        rep_first=rep_first,
        company=company_name,
        industry=industry,
        pain=pain,
        topic=topic,
        ic_title=ic_title,
    )
    if prior_ref:
        body = f"Following up on {prior_ref} — " + body
    return body

# ── meeting notes ─────────────────────────────────────────────────────────────

MEETING_NOTES_TEMPLATES = {
    "Discovery Call": (
        "Opened with a review of {company}'s current challenges around {pain}. "
        "{contact_first} confirmed that {topic} has been a recurring blocker for their team. "
        "Discussed ProspectIQ's {industry}-specific workflow and how it maps to their existing stack. "
        "Rep walked through three customer case studies relevant to {company}'s growth stage. "
        "{contact_first} mentioned they are evaluating two other vendors in parallel. "
        "Agreed to schedule a product demo within the next 7 days. "
        "Action: Rep to send {industry} compliance overview and case study PDF before demo."
    ),
    "Product Demo": (
        "Opened with a recap of the discovery call and the {pain} priority {contact_first} highlighted. "
        "Demonstrated the core {topic} workflow live against {company}'s stated requirements. "
        "Technical questions from the {ic_title} focused on API rate limits and {industry} data handling. "
        "Rep screen-shared the sandbox environment and walked through a realistic use case. "
        "{contact_first} responded positively to the reporting module; flagged pricing as a future question. "
        "Minor concern raised about implementation timeline — rep committed to a detailed project plan. "
        "Next step: schedule a Technical Deep Dive with the engineering team."
    ),
    "Technical Deep Dive": (
        "Started with a review of open technical questions from the demo, including {topic} and {pain}. "
        "{ic_title} validated the API integration path and confirmed compatibility with their {industry} stack. "
        "Reviewed the {topic} architecture diagram shared via email prior to this session. "
        "Discussed {industry}-specific compliance posture — rep confirmed SOC2 report is available under NDA. "
        "One blocker identified: VPN restrictions on their {ic_title}'s sandbox access need IT sign-off. "
        "Rep committed to sending a revised integration guide addressing the {pain} edge case. "
        "Agreed to move to Proposal stage pending IT approval."
    ),
    "Proposal Review": (
        "Reviewed the formal proposal document shared earlier this week. "
        "{contact_first} confirmed budget approval is pending CFO sign-off on the {topic} line item. "
        "Discussed phased rollout option to reduce initial investment and address {pain} concerns. "
        "Rep clarified {industry} compliance clauses and referenced the BAA/DPA addendum. "
        "Minor pushback on the implementation fee — rep offered to bundle it into year-one pricing. "
        "Legal review expected within 5 business days before MSA can be shared. "
        "Action: Rep to send updated proposal with revised implementation fee structure."
    ),
    "Final Decision Meeting": (
        "Executive sponsor joined for the final review — {contact_first} and their {ic_title} present. "
        "Walked through remaining open items from the contract redlines discussed last week. "
        "Addressed {pain} indemnification language and {topic} data retention clauses. "
        "CFO confirmed budget is approved; only legal sign-off remains. "
        "Rep referenced the {industry} compliance documentation shared two weeks ago to close remaining concerns. "
        "Both parties aligned on a go-live target of 30 days post-signature. "
        "Action: Legal to finalize MSA; rep to send onboarding kickoff agenda."
    ),
}

def build_meeting_notes(
    title: str, company_name: str, contact_first: str,
    industry: str, trackers: list, rng: random.Random,
    prior_email_subject: str = "", ic_title: str = "solutions engineer"
) -> str:
    # map title to template key
    key = title
    for k in MEETING_NOTES_TEMPLATES:
        if k.lower() in title.lower():
            key = k
            break
    template = MEETING_NOTES_TEMPLATES.get(key, MEETING_NOTES_TEMPLATES["Discovery Call"])
    pain = rng.choice(trackers) if trackers else "integration"
    topic = rng.choice([t for t in trackers if t != pain] or trackers or ["workflow"])
    notes = template.format(
        company=company_name, contact_first=contact_first,
        industry=industry, pain=pain, topic=topic, ic_title=ic_title,
    )
    if prior_email_subject:
        notes = f"This session built on discussions started in the email thread '{prior_email_subject}'. " + notes
    return notes

# ── generators ────────────────────────────────────────────────────────────────

def gen_companies(n: int, industries: list[str], rng: random.Random) -> list[dict]:
    rows = []
    names = rng.sample(COMPANY_NAMES, min(n, len(COMPANY_NAMES)))
    if len(names) < n:
        extras = [f"Company_{i}" for i in range(n - len(names))]
        names += extras

    for i in range(n):
        industry = rng.choice(industries)
        stage = rng.choice(["Startup", "Scaleup", "Enterprise"])
        emp = {"Startup": rng.randint(10, 150),
               "Scaleup": rng.randint(150, 1000),
               "Enterprise": rng.randint(1000, 15000)}[stage]
        rows.append({
            "company_id": make_id("co"),
            "name": names[i],
            "industry": industry,
            "employee_count": emp,
            "growth_stage": stage,
            "hq_region": rng.choice(REGIONS),
            "annual_revenue_usd": revenue_for_stage(stage, emp),
            "context_note": context_note(industry, stage),
        })
    return rows


def gen_contacts(companies: list[dict], rng: random.Random) -> list[dict]:
    rows = []
    for co in companies:
        n_contacts = rng.randint(2, 5)
        used_names = set()
        for _ in range(n_contacts):
            while True:
                fn = rng.choice(FIRST_NAMES)
                ln = rng.choice(LAST_NAMES)
                full = f"{fn} {ln}"
                if full not in used_names:
                    used_names.add(full)
                    break
            seniority = rng.choice(["IC", "Manager", "Director", "VP", "C-Level"])
            title = rng.choice(TITLES_BY_SENIORITY[seniority])
            rows.append({
                "contact_id": make_id("ct"),
                "company_id": co["company_id"],
                "full_name": full,
                "title": title,
                "seniority": seniority,
                "email": email_for(full, co["name"]),
                "relationship_note": relationship_note(title, seniority, co["industry"]),
            })
    return rows


def gen_reps(n: int, rng: random.Random) -> list[dict]:
    rows = []
    tiers = ["Top", "Good", "Average", "Underperformer"]
    targets = {"Top": (8, 12), "Good": (5, 8), "Average": (3, 5), "Underperformer": (1, 3)}
    used = set()
    for i in range(n):
        while True:
            fn = rng.choice(FIRST_NAMES)
            ln = rng.choice(LAST_NAMES)
            full = f"{fn} {ln}"
            if full not in used:
                used.add(full)
                break
        tier = tiers[i % len(tiers)]
        lo, hi = targets[tier]
        rows.append({
            "rep_id": make_id("rep"),
            "full_name": full,
            "email": rep_email(full),
            "tier": tier,
            "quarter_deals_closed_target": rng.randint(lo, hi),
        })
    return rows


def gen_deals(companies: list[dict], contacts: list[dict], reps: list[dict], rng: random.Random) -> list[dict]:
    rows = []
    contact_by_company: dict[str, list[dict]] = {}
    for c in contacts:
        contact_by_company.setdefault(c["company_id"], []).append(c)

    base_date = datetime(2024, 1, 1)

    for co in companies:
        n_deals = rng.randint(1, 3)
        co_contacts = contact_by_company.get(co["company_id"], [])
        if not co_contacts:
            continue
        for _ in range(n_deals):
            stage = rng.choice(STAGE_ORDER)
            health = rng.choice(["Positive", "Neutral", "Negative"])
            opened = base_date + timedelta(days=rng.randint(0, 180))
            cycle = rng.randint(30, 90)
            expected_close = opened + timedelta(days=cycle)

            closed_at = None
            loss_reason = None
            if stage in ["Closed-Won", "Closed-Lost"]:
                closed_at = iso(opened + timedelta(days=rng.randint(25, cycle)))
                if stage == "Closed-Lost":
                    loss_reason = rng.choice(LOSS_REASONS)

            primary_contact = rng.choice(co_contacts)
            rep = rng.choice(reps)

            rows.append({
                "deal_id": make_id("deal"),
                "company_id": co["company_id"],
                "primary_contact_id": primary_contact["contact_id"],
                "rep_id": rep["rep_id"],
                "stage": stage,
                "health": health,
                "value_usd": deal_value(co["growth_stage"], co["employee_count"]),
                "opened_at": iso(opened),
                "expected_close_at": iso(expected_close),
                "closed_at": closed_at,
                "loss_reason": loss_reason,
            })
    return rows


def gen_emails(
    deals: list[dict],
    companies: list[dict],
    contacts: list[dict],
    reps: list[dict],
    rng: random.Random,
) -> list[dict]:
    rows = []
    co_map = {c["company_id"]: c for c in companies}
    ct_map = {c["contact_id"]: c for c in contacts}
    rep_map = {r["rep_id"]: r for r in reps}
    ct_by_co: dict[str, list[dict]] = {}
    for c in contacts:
        ct_by_co.setdefault(c["company_id"], []).append(c)

    for deal in deals:
        co = co_map[deal["company_id"]]
        rep = rep_map[deal["rep_id"]]
        primary_ct = ct_map[deal["primary_contact_id"]]
        all_co_contacts = ct_by_co.get(co["company_id"], [primary_ct])
        trackers = rng.sample(INDUSTRY_TRACKERS[co["industry"]], min(5, len(INDUSTRY_TRACKERS[co["industry"]])))
        stage = deal["stage"]
        health = deal["health"]
        opened = datetime.strptime(deal["opened_at"], "%Y-%m-%dT%H:%M:%SZ")
        closed = datetime.strptime(deal["closed_at"], "%Y-%m-%dT%H:%M:%SZ") if deal["closed_at"] else None

        # volume by stage
        if stage in ["Prospecting", "Qualified"]:
            n_threads = rng.randint(1, 2)
            emails_per_thread = rng.randint(2, 4)
        elif stage in ["Demo", "Proposal"]:
            n_threads = rng.randint(2, 3)
            emails_per_thread = rng.randint(3, 5)
        else:
            n_threads = rng.randint(2, 4)
            emails_per_thread = rng.randint(3, 6)

        rep_first = rep["full_name"].split()[0]
        ct_first = primary_ct["full_name"].split()[0]
        ic_contact = next((c for c in all_co_contacts if c["seniority"] == "IC"), primary_ct)
        ic_title = ic_contact["title"]

        last_subject = ""

        for _ in range(n_threads):
            thread_id = make_id("thr")
            thread_start = opened + timedelta(hours=rng.randint(1, 48))
            prev_email_id = None
            prev_ts = thread_start

            for seq in range(emails_per_thread):
                direction = "outbound" if seq % 2 == 0 else "inbound"
                if seq == 0:
                    direction = "outbound"

                if direction == "outbound":
                    sender_id = rep["rep_id"]
                    recipient_ids = [primary_ct["contact_id"]]
                else:
                    sender_id = primary_ct["contact_id"]
                    recipient_ids = [rep["rep_id"]]

                latency_h = reply_latency(health, rng) if direction == "inbound" else rng.randint(1, 12)
                ts = prev_ts + timedelta(hours=latency_h)

                # keep within deal window
                if closed and ts > closed:
                    ts = closed - timedelta(hours=rng.randint(1, 12))

                subject = build_subject(stage, co["name"], trackers, rng)
                if seq > 0:
                    subject = "RE: " + subject

                prior_ref = f"our {last_subject}" if last_subject and seq > 0 else ""
                body = build_body(
                    direction, stage, ct_first, rep_first,
                    co["name"], co["industry"], trackers, rng,
                    prior_ref=prior_ref, ic_title=ic_title,
                )
                sentiment = pick_sentiment(health, rng)
                outcome = rng.choice(["replied", "replied", "ignored", "forwarded", "objection", "scheduling-request"])
                if stage in ["Negotiation", "Proposal"]:
                    outcome = rng.choice(["replied", "objection", "scheduling-request"])

                email_id = make_id("em")
                rows.append({
                    "email_id": email_id,
                    "deal_id": deal["deal_id"],
                    "thread_id": thread_id,
                    "direction": direction,
                    "sender_id": sender_id,
                    "recipient_ids": json.dumps([r for r in recipient_ids]),
                    "timestamp": iso(ts),
                    "subject": subject,
                    "body": body,
                    "sequence_index": seq,
                    "sentiment": sentiment,
                    "trackers": json.dumps(rng.sample(trackers, min(3, len(trackers)))),
                    "reply_latency_hours": latency_h if direction == "inbound" else None,
                    "in_reply_to_email_id": prev_email_id if seq > 0 else None,
                    "outcome": outcome,
                })
                last_subject = subject
                prev_email_id = email_id
                prev_ts = ts

    return rows


def gen_meetings(
    deals: list[dict],
    companies: list[dict],
    contacts: list[dict],
    reps: list[dict],
    emails: list[dict],
    rng: random.Random,
) -> list[dict]:
    rows = []
    co_map = {c["company_id"]: c for c in companies}
    ct_map = {c["contact_id"]: c for c in contacts}
    rep_map = {r["rep_id"]: r for r in reps}
    ct_by_co: dict[str, list[dict]] = {}
    for c in contacts:
        ct_by_co.setdefault(c["company_id"], []).append(c)

    emails_by_deal: dict[str, list[dict]] = {}
    for e in emails:
        emails_by_deal.setdefault(e["deal_id"], []).append(e)

    MEETING_SEQ = ["Discovery Call", "Product Demo", "Technical Deep Dive", "Proposal Review", "Final Decision Meeting"]
    STAGE_SEQ = ["Prospecting", "Qualified", "Demo", "Proposal", "Negotiation"]

    for deal in deals:
        co = co_map[deal["company_id"]]
        rep = rep_map[deal["rep_id"]]
        stage = deal["stage"]
        health = deal["health"]
        opened = datetime.strptime(deal["opened_at"], "%Y-%m-%dT%H:%M:%SZ")
        closed = datetime.strptime(deal["closed_at"], "%Y-%m-%dT%H:%M:%SZ") if deal["closed_at"] else None
        all_co_contacts = ct_by_co.get(co["company_id"], [])
        trackers = rng.sample(INDUSTRY_TRACKERS[co["industry"]], min(5, len(INDUSTRY_TRACKERS[co["industry"]])))

        # how many meetings based on stage progress
        stage_idx = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 2
        active_idx = min(stage_idx, len(ACTIVE_STAGES) - 1)
        n_meetings = rng.randint(max(1, active_idx), min(active_idx + 2, len(MEETING_SEQ)))

        deal_emails = emails_by_deal.get(deal["deal_id"], [])
        prior_email_subject = deal_emails[0]["subject"] if deal_emails else ""

        primary_ct = ct_map[deal["primary_contact_id"]]
        ic_contact = next((c for c in all_co_contacts if c["seniority"] == "IC"), primary_ct)
        exec_contact = next((c for c in all_co_contacts if c["seniority"] in ["VP", "C-Level"]), primary_ct)
        rep_first = rep["full_name"].split()[0]
        ct_first = primary_ct["full_name"].split()[0]
        ic_title = ic_contact["title"]

        meeting_start = opened + timedelta(days=rng.randint(2, 7))

        for m_idx in range(n_meetings):
            title = MEETING_SEQ[m_idx]
            m_stage = STAGE_SEQ[min(m_idx, len(STAGE_SEQ) - 1)]

            duration_min = rng.choice([30, 45, 60])
            sched_start = meeting_start + timedelta(days=m_idx * rng.randint(5, 10))
            sched_end = sched_start + timedelta(minutes=duration_min)

            if closed and sched_start > closed:
                sched_start = closed - timedelta(days=rng.randint(1, 3))
                sched_end = sched_start + timedelta(minutes=duration_min)

            # outcome by health
            if health == "Positive":
                outcome = rng.choices(["completed", "completed", "completed", "rescheduled", "decision-meeting"],
                                       weights=[50, 20, 15, 10, 5])[0]
            elif health == "Neutral":
                outcome = rng.choices(["completed", "rescheduled", "blocked", "no-show"],
                                       weights=[40, 30, 20, 10])[0]
            else:
                outcome = rng.choices(["rescheduled", "no-show", "completed", "blocked"],
                                       weights=[35, 25, 25, 15])[0]

            actual_start = sched_start + timedelta(minutes=rng.randint(-5, 10)) if outcome == "completed" else None
            actual_end = sched_end + timedelta(minutes=rng.randint(-5, 10)) if outcome == "completed" else None

            # attendees
            attendees = [rep["rep_id"], primary_ct["contact_id"]]
            if title == "Technical Deep Dive" and ic_contact["contact_id"] not in attendees:
                attendees.append(ic_contact["contact_id"])
            if title == "Final Decision Meeting" and exec_contact["contact_id"] not in attendees:
                attendees.append(exec_contact["contact_id"])

            sentiment = pick_sentiment(health, rng)
            notes = build_meeting_notes(
                title, co["name"], ct_first, co["industry"], trackers, rng,
                prior_email_subject=prior_email_subject if m_idx == 0 else "",
                ic_title=ic_title,
            )

            follow_ups = {
                "Discovery Call": f"Send {co['industry']} compliance overview and relevant case studies",
                "Product Demo": f"Schedule Technical Deep Dive; share {trackers[0]} documentation",
                "Technical Deep Dive": f"Resolve {trackers[1] if len(trackers) > 1 else trackers[0]} integration question; send updated architecture diagram",
                "Proposal Review": f"Update proposal with revised pricing; share DPA/BAA addendum",
                "Final Decision Meeting": f"Finalize MSA; send onboarding kickoff agenda",
            }

            rows.append({
                "meeting_id": make_id("mtg"),
                "deal_id": deal["deal_id"],
                "title": title,
                "stage_at_time": m_stage,
                "scheduled_start": iso(sched_start),
                "scheduled_end": iso(sched_end),
                "actual_start": iso(actual_start) if actual_start else None,
                "actual_end": iso(actual_end) if actual_end else None,
                "attendee_ids": json.dumps(attendees),
                "outcome": outcome,
                "notes": notes,
                "sentiment": sentiment,
                "trackers": json.dumps(rng.sample(trackers, min(3, len(trackers)))),
                "follow_up_action": follow_ups.get(title, "Send follow-up summary"),
            })

    return rows

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="ProspectIQ Demo Data Generator")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--companies", type=int, default=15)
    parser.add_argument("--industries", type=str, default="saas,healthcare,finserv,manufacturing")
    parser.add_argument("--reps", type=int, default=6)
    parser.add_argument("--out", type=str, default="output")
    parser.add_argument("--format", type=str, default="csv", choices=["csv", "json"])
    args = parser.parse_args()

    rng = random.Random(args.seed)

    # resolve industry names
    raw_industries = [i.strip().lower() for i in args.industries.split(",")]
    industries = [INDUSTRY_MAP.get(i, i) for i in raw_industries]

    os.makedirs(args.out, exist_ok=True)

    print(f"[1/6] Generating companies (n={args.companies})...")
    companies = gen_companies(args.companies, industries, rng)

    print(f"[2/6] Generating contacts...")
    contacts = gen_contacts(companies, rng)

    print(f"[3/6] Generating sales reps (n={args.reps})...")
    reps = gen_reps(args.reps, rng)

    print(f"[4/6] Generating deals...")
    deals = gen_deals(companies, contacts, reps, rng)

    print(f"[5/6] Generating emails...")
    emails = gen_emails(deals, companies, contacts, reps, rng)

    print(f"[6/6] Generating meetings...")
    meetings = gen_meetings(deals, companies, contacts, reps, emails, rng)

    # write outputs
    ext = args.format
    writer = write_csv if ext == "csv" else write_json
    datasets = {
        "companies": companies,
        "contacts": contacts,
        "sales_reps": reps,
        "deals": deals,
        "emails": emails,
        "meetings": meetings,
    }
    for name, rows in datasets.items():
        path = os.path.join(args.out, f"{name}.{ext}")
        writer(path, rows)
        print(f"  ✓ {path} ({len(rows)} rows)")

    print(f"\n✅ Done! Output in ./{args.out}/")
    print(f"   Companies: {len(companies)} | Contacts: {len(contacts)} | Reps: {len(reps)}")
    print(f"   Deals: {len(deals)} | Emails: {len(emails)} | Meetings: {len(meetings)}")


if __name__ == "__main__":
    main()
