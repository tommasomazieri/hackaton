# E0 Task Commands — run each in its own terminal

Root: `C:\Users\tomin\OneDrive\Desktop\PROGETTI\operating_proejcts\hackaton`

---

## TASK-001 — Personas

```
cd "C:\Users\tomin\OneDrive\Desktop\PROGETTI\operating_proejcts\hackaton"
claude --model claude-sonnet-4-6 "Work on TASK-001 for project 02505df5-3137-49f1-961c-e04c795eb7d6. Define personas for DC Siting Intelligence Tool. Create 3 user archetypes composited into persona Jordan (infra strategy analyst, investment analyst, head of DC development) plus buyer persona IC/CFO. For each persona document: role, goals, frustrations, tools_used_today, decision_criteria, representative quote. Deliverables: (1) artifacts/personas.json — array of persona objects with fields: id, name, role, archetype, goals, frustrations, tools_used, decision_criteria, quote. (2) artifacts/personas.md — narrative pitch-ready version. Read docs/challenge.md first for full context."
```

---

## TASK-002 — Customer Journey: Before

```
cd "C:\Users\tomin\OneDrive\Desktop\PROGETTI\operating_proejcts\hackaton"
claude --model claude-sonnet-4-6 "Work on TASK-002 for project 02505df5-3137-49f1-961c-e04c795eb7d6. Map the AS-IS customer journey for Jordan researching EU data center sites today, before our tool exists. Full journey from investment mandate to IC board presentation. For each stage document: steps, pain_points, time_cost_estimate, tools_used, emotional_state. Quantify pain: hours wasted, costs, risks. Deliverables: (1) artifacts/journey-before.json — structured journey object with stages array. (2) artifacts/journey-before.md — narrative visual map, pitch-ready. Read docs/challenge.md first for full context."
```

---

## TASK-004 — JTBD Framework

```
cd "C:\Users\tomin\OneDrive\Desktop\PROGETTI\operating_proejcts\hackaton"
claude --model claude-sonnet-4-6 "Work on TASK-004 for project 02505df5-3137-49f1-961c-e04c795eb7d6. Write 4-6 Jobs-To-Be-Done statements for user persona Jordan and buyer persona IC/CFO. Format: When [situation] I want to [motivation] so I can [outcome]. Cover functional (find optimal site fast), emotional (confidence in IC presentation), social (be seen as rigorous), financial (minimize downside risk). For each JTBD note which scoring dimension it validates. Deliverables: (1) artifacts/jtbd.json — array of objects: id, persona, situation, motivation, outcome, job_type, validates_dimension. (2) artifacts/jtbd.md — narrative pitch-ready. Read docs/challenge.md first for full context."
```

---

## TASK-005 — Market Viability

```
cd "C:\Users\tomin\OneDrive\Desktop\PROGETTI\operating_proejcts\hackaton"
claude --model claude-sonnet-4-6 "Work on TASK-005 for project 02505df5-3137-49f1-961c-e04c795eb7d6. Market viability analysis for DC Siting Intelligence Tool. Research: EU DC investment volume per year, deal sizes, advisory fee benchmarks. Build TAM/SAM/SOM estimates. Define pricing model options (per-query SaaS, subscription, enterprise). Map competitive landscape: Cushman and Wakefield DC advisory, CBRE, Green Mountain, custom Excel/consultant workflows — what each does and what gap we fill. Deliverables: (1) artifacts/market-viability.json — structured: tam_eur, sam_eur, som_eur, pricing_models array, competitors array with name/what_they_do/gap fields. (2) artifacts/market-viability.md — narrative with numbers, pitch-ready. Read docs/challenge.md first for full context."
```

---

## TASK-046 — Stakeholder Map

```
cd "C:\Users\tomin\OneDrive\Desktop\PROGETTI\operating_proejcts\hackaton"
claude --model claude-sonnet-4-6 "Work on TASK-046 for project 02505df5-3137-49f1-961c-e04c795eb7d6. Create stakeholder map for DC Siting Intelligence Tool. 7 stakeholders: IC Partner, CFO/CIO, Head of DC Development (Jordan manager), ESG Officer, Board/LP, Infrastructure PM, Legal/Compliance. For each: role, what_they_need_from_dc_siting, influence_score (1-5), interest_score (1-5), approval_trigger, block_trigger, quadrant (Manage Closely / Keep Satisfied / Keep Informed / Monitor). Deliverables: (1) artifacts/stakeholder-map.json — array of stakeholder objects with all fields. (2) artifacts/stakeholder-map.md — influence/interest grid + narrative, pitch-ready. Read docs/challenge.md first for full context."
```
