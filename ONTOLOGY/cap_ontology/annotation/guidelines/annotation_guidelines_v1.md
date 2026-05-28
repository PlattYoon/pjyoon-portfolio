# CAP Annotation Guidelines — v1.0

## 1. Purpose

These guidelines govern entity and relation annotation across all Climate Action Plan (CAP) documents. All annotators must read this document before beginning work. When in doubt, **defer to the schema** and flag ambiguous cases for adjudication.

---

## 2. Entity Types

### EmissionsTarget
A quantified or stated goal to reduce, limit, or eliminate greenhouse gas emissions.

**Include:**
- Percentage reductions ("reduce GHG 45% by 2030")
- Absolute targets ("reach net-zero by 2050")
- Sector-specific targets ("reduce building emissions 30%")

**Exclude:**
- Aspirational language without a number or commitment ("work toward cleaner air")
- Adaptation measures (use AdaptationMeasure instead)

---

### AdaptationMeasure
A concrete action, project, or program designed to reduce climate vulnerability or build resilience.

**Include:**
- Infrastructure projects ("install flood barriers along the riverfront")
- Programs ("urban heat island cooling centers")
- Policy interventions ("mandatory green roofs on new construction")

**Exclude:**
- Mitigation/emissions targets (use EmissionsTarget)
- General strategies without actionable content

---

### Jurisdiction
A governmental or administrative entity responsible for the CAP.

**Include:** cities, counties, states, provinces, regional authorities, tribal nations

**Exclude:** non-governmental organizations, corporations (use Stakeholder)

---

### Sector
A domain of economic or social activity covered by a target or measure.

**Examples:** transportation, buildings, energy, waste, agriculture, land use, water

---

### Deadline
A point in time by which a target or measure is to be completed.

**Include:** absolute years ("by 2040"), relative periods ("within 10 years"), phased milestones ("Phase 1: 2025")

---

### Stakeholder
An organization, agency, or group involved in implementing or overseeing the CAP.

**Examples:** EPA, state energy office, local nonprofits, utility companies, community groups

---

### BaselineYear
The reference year from which emissions reductions are measured.

---

### Metric
The unit or measurement system used to quantify emissions or progress.

**Examples:** MtCO2e, % reduction, kWh, VMT (vehicle miles traveled)

---

### FundingSource
The origin of financial resources for a measure or program.

**Examples:** federal infrastructure bill, state green bank, carbon pricing revenue, municipal bonds

---

### PolicyInstrument
A law, regulation, standard, code, or formal policy mechanism.

**Examples:** building energy code, zoning ordinance, renewable portfolio standard, carbon tax

---

## 3. Relation Types

| Relation | Head | Tail | Example |
|---|---|---|---|
| `targets` | Jurisdiction | EmissionsTarget | Pittsburgh targets net-zero by 2050 |
| `implements` | Jurisdiction | AdaptationMeasure | County implements green stormwater infra |
| `governs` | PolicyInstrument | Sector | Building code governs buildings sector |
| `reports_to` | Stakeholder | Jurisdiction | EPA reports_to federal government |
| `supersedes` | Jurisdiction | Jurisdiction | 2023 CAP supersedes 2018 CAP |
| `funded_by` | AdaptationMeasure | FundingSource | Cooling centers funded_by federal grant |
| `has_deadline` | EmissionsTarget | Deadline | Net-zero target has_deadline 2050 |
| `measured_in` | EmissionsTarget | Metric | Target measured_in MtCO2e |
| `applies_to` | AdaptationMeasure | Sector | Transit electrification applies_to transportation |

---

## 4. Span Boundaries

- Include the **minimal** text that captures the entity (exclude surrounding prepositions).
- **Correct:** `net-zero by 2050`
- **Incorrect:** `achieve net-zero by 2050` (include the verb only if it is part of a named program)

---

## 5. Confidence Scores

| Score | Meaning |
|---|---|
| 1.0 | Certain — no ambiguity |
| 0.8–0.99 | High confidence, minor hedging |
| 0.5–0.79 | Uncertain, flag for review |
| < 0.5 | Highly uncertain — must be adjudicated |

---

## 6. Adjudication Protocol

1. Flag spans/relations with confidence < 0.6 using the `notes` field.
2. Submit flagged examples to the lead annotator via the `adjudication/` folder.
3. Adjudicated decisions are recorded in `docs/adjudication_log.md` and propagate to future guidelines.

---

## 7. What NOT to Annotate

- Boilerplate legal text, table of contents, page headers/footers
- Bibliographic references and citations
- Text in figures/images (unless extracted via OCR and verified)
