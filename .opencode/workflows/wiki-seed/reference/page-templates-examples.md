# Wiki Page Template Examples by Type

Reference this file when creating a new page or normalizing an incomplete one. Instantiate the smallest template that preserves predictable structure, claim traceability, and retrievability. Adapt section headings only when the page's `page_type` makes a section irrelevant.

## General Template Rules

Start every page with valid YAML frontmatter. Use stable identifiers and slugs. Keep section order predictable. Represent substantive scientific content as atomic claims or clearly scoped definitions. Cite every substantive claim. Link to canonical related pages instead of duplicating content.

Use the examples in this file as structural patterns, not rigid boilerplate. Keep each page minimal but immediately usable. Do not maintain empty sections.


### Minimal Claim Pattern Example

Use this pattern whenever a page needs explicit claim records.

```yaml
claim_id: clm-bpa-001
page_id: bisphenol-a
claim_type: result
statement: Bisphenol A shows estrogen receptor activity in multiple in vitro assay systems.
subject: Bisphenol A
predicate: shows_activity_in
object: estrogen receptor assays
qualifiers:
  species: human
  system: in_vitro
citations:
  - cit-001
verification_status: supported
confidence: medium
depends_on: []
notes: null
```

### Minimal Citation Pattern Example

```yaml
citation_id: cit-001
source_type: review
title: Example Review Title
authors:
  - A. Author
  - B. Author
year: 2024
container: Journal of Example Toxicology
doi: 10.1000/example
url: https://example.org/review
access_status: open_access
allowed_source: true
retrieved_on: 2026-07-21
pages_or_sections: Section 3.2
notes: Supports the in vitro receptor activity statement.
```

## Table of Contents
1. [concept](#concept)
2. [chemical](#chemical)
3. [biology](#biology)
4. [endpoint](#endpoint)
5. [assay](#assay)
6. [dataset](#dataset)
7. [model](#model)
8. [literature](#literature)
9. [evidence](#evidence)
10. [workflow](#workflow)
11. [index](#index)
12. [governance](#governance)
13. [agent operation](#agent_operation)

## `concept`

Use this template for field-specific concepts, terms, and methodological ideas.

```md
---
id: adverse-outcome-pathway
title: Adverse Outcome Pathway
description: Concept page defining adverse outcome pathways and their role in computational toxicology.
slug: /concepts/adverse-outcome-pathway
sidebar_label: Adverse Outcome Pathway
page_type: concept
entity_class: concept
status: draft
last_reviewed: 2026-07-21
---

## Overview

Define the concept in toxicology-specific terms.

## Scope and Notes

State what the term includes, excludes, and is commonly confused with.

## Key Definitions

- Claim or definition with citation.
- Claim or definition with citation.

## Operational Relevance

Explain how the concept is used in assays, datasets, models, workflows, or interpretation.

## Related Pages

Link to neighboring concepts, methods, assays, or endpoints.

## Open Questions or Review Notes

Record ambiguity, edge cases, or incomplete coverage.

## References
```

Use concept pages to encode distinctions, interpretation rules, and field-specific meaning. Do not restate generic science unless the toxicology-specific usage changes the meaning.

## `chemical`

Use this template for substances, mixtures, metabolites, and chemical classes.

```md
---
id: bisphenol-a
title: Bisphenol A
description: Chemical page for Bisphenol A with identifiers, endpoint links, and evidence summaries.
slug: /chemicals/bisphenol-a
sidebar_label: Bisphenol A
page_type: chemical
entity_class: chemical
status: draft
last_reviewed: 2026-07-21
aliases:
  - BPA
---

## Overview

State what the substance is and why it matters in the wiki.

## Scope and Notes

State whether the page covers the parent compound, metabolites, mixtures, or a broader class.

## Identifiers

List major identifiers such as CAS, PubChem CID, InChIKey, and common aliases.

## Key Claims

- Atomic, cited claims about mechanisms, endpoints, assay activity, or dataset presence.

## Mechanistic Relevance

Summarize important linked targets, pathways, or biological context.

## Linked Endpoints and Assays

Link to endpoint and assay pages with short scoped notes.

## Data Resources

Link to dataset pages, **not the datasets themselves**. Note important coverage or caveats.

## Open Questions or Review Notes

Record contradictions, unresolved interpretation, or missing evidence.

## References
```

Use chemical pages as integration hubs. Keep claims scoped by species, assay system, endpoint, dose, and evidence stream and context where relevant.

## `biology`

Use this template for receptors, enzymes, pathways, tissues, species, and other biological entities.

```md
---
id: aryl-hydrocarbon-receptor
title: Aryl Hydrocarbon Receptor
description: Biology page for the aryl hydrocarbon receptor and its toxicological relevance.
slug: /biology/targets/aryl-hydrocarbon-receptor
sidebar_label: AHR
page_type: biology
entity_class: target
status: draft
last_reviewed: 2026-07-21
aliases:
  - AHR
  - AhR
---

## Overview

Define the biological entity and its toxicological relevance.

## Scope and Notes

State species or nomenclature cautions and nearby entities that should not be conflated.

## Key Claims

- Atomic, cited claims about function, pathway role, or toxicological relevance.

## Mechanistic Context

Explain the entity's role in linked pathways, chemicals, assays, or endpoints.

## Related Pages

Link to chemicals, assays, endpoints, and datasets.

## Open Questions or Review Notes

## References
```

Use biology pages to supply applicable mechanisms and relevant context. Do not use them as generic molecular biology primers.

## `endpoint`

Use this template for toxicological outcomes and hazard classes.

```md
---
id: hepatotoxicity
title: Hepatotoxicity
description: Endpoint page defining hepatotoxicity and summarizing relevant evidence types.
slug: /endpoints/hepatotoxicity
sidebar_label: Hepatotoxicity
page_type: endpoint
entity_class: endpoint
status: draft
last_reviewed: 2026-07-21
---

## Overview

Define the endpoint and why it matters.

## Scope and Notes

State inclusion boundaries, important subclasses, and common confusions.

## Key Definitions and Claims

- Definition or evidence-oriented claim with citation.

## Evidence Types

Describe what kinds of assays, datasets, biological markers, or source types bear on the endpoint.

## Interpretation Notes

Explain important caveats, thresholds, or scope limits.

## Related Pages

Link to assays, biology, chemicals, and workflows.

## Open Questions or Review Notes

## References
```

Use endpoint pages to anchor what counts as evidence and how the endpoint is operationalized.

## `assay`

Use this template for experimental or in silico assays.

```md
---
id: ames-test
title: Ames Test
description: Assay page for the Ames test, including measured signal, interpretation, and limitations.
slug: /assays/ames-test
sidebar_label: Ames Test
page_type: assay
entity_class: assay
agent_access: results_available_in_dataset
access_route:
  - "[ToxCast](07-datasets/toxcast.md)"
status: draft
last_reviewed: 2026-07-21
---

## Overview

State what the assay is and what it measures.

## Scope and Notes

State assay family, major variants, and limits of coverage.

## Measured Signal

Describe the assay output and what it is intended to indicate.

## Interpretation

State what positive, negative, or ambiguous results can and cannot support.

## Limitations and Artifacts

Record known confounders, false positive or false negative issues, and scope limits.

## Related Pages

Link to endpoints, datasets, and methods.

## Open Questions or Review Notes

## References
```

Add assay access metadata when the page must support planning or tool routing. Use `agent_access` as a controlled frontmatter field to record what level of direct interaction the agentic system has with the assay, and use optional companion fields such as `access_route`, `access_notes`, `linked_workflow`, or `result_sources` only when they add concrete operational value. Restrict `agent_access` to the following values: 
- `no_access` — the system cannot run the assay and does not have direct results access.
- `results_available_in_dataset` — the system cannot run the assay itself but can inspect assay outputs from one or more datasets.
- `can_perform` — the system can execute the assay directly through available tools or workflows.
- `restricted_access` — the assay is theoretically available but blocked by permissions, credentials, licensing, or environment constraints.
- `human_only` — the assay requires human-operated lab or expert steps that the agent cannot autonomously perform.

Use assay pages to prevent overinterpretation of assay outputs.

## `dataset`

Use this template for public data resources and benchmark collections.

```md
---
id: toxcast
title: ToxCast
description: Dataset page for ToxCast, including scope, schema notes, and toxicology relevance.
slug: /datasets/toxcast
sidebar_label: ToxCast
page_type: dataset
entity_class: dataset
status: draft
last_reviewed: 2026-07-21
---

## Overview

State what the dataset is and why it matters.

## Scope and Coverage

Describe entity coverage, assay or endpoint coverage, and notable exclusions.

## Schema and Access Notes

Summarize major fields, access routes, identifiers, and update cadence.

## Key Caveats

Record missingness, bias, normalization issues, and interpretation limits.

## Related Pages

Link to assays, endpoints, methods, and workflows.

## Open Questions or Review Notes

## References
```

Use dataset pages to document provenance and structure, not to host derived conclusions. Do not include instructions on how to access a dataset, link to the relevant workflow for that information.

## `model`

Use this template for computational models, analytical methods, and decision frameworks.

```md
---
id: qsar-models
title: QSAR Models
description: Model page for QSAR methods used in computational toxicology.
slug: /models/qsar-models
sidebar_label: QSAR Models
page_type: model
entity_class: method
status: draft
last_reviewed: 2026-07-21
---

## Overview

State what the method is and what problem it solves.

## Scope and Notes

State major subclasses, assumptions, and common confusions.

## Inputs and Outputs

Describe what the method consumes and produces.

## Applicability Domain

State where the method is appropriate and where it is not.

## Strengths and Limitations

Record validation concerns, uncertainty, and interpretation limits.

## Related Pages

Link to datasets, workflows, assays, and concepts.

## Open Questions or Review Notes

## References
```

Use model pages to capture assumptions and applicability boundaries explicitly.

## `literature`

Use this template for source-level provenance pages.

```md
---
id: example-review-2024
title: Example Review (2024)
description: Literature page preserving source metadata, scope, and extraction notes.
slug: /literature/example-review-2024
sidebar_label: Example Review (2024)
page_type: literature
entity_class: source
status: draft
last_reviewed: 2026-07-21
---

## Overview

State what the source covers and why it is relevant.

## Citation Metadata

Record authors, year, venue, DOI, URL, and access status.

## Scope and Source Notes

Summarize source type, topic boundaries, and important framing.

## Extracted Key Claims

List concise extracted claims or claim pointers.

## Target Pages

Link to canonical pages that received normalized content from this source.

## Open Questions or Review Notes

## References
```

Keep literature pages lightweight and provenance-oriented. Do not trap durable knowledge only here.

## `evidence`

Use this template for structured evidence artifacts.

```md
---
id: evidence-bpa-estrogen-receptor
title: Evidence Table for Bisphenol A and Estrogen Receptor Activity
description: Structured evidence page for claims about Bisphenol A and estrogen receptor activity.
slug: /evidence/evidence-bpa-estrogen-receptor
sidebar_label: BPA ER Evidence
page_type: evidence
entity_class: evidence_record
status: draft
last_reviewed: 2026-07-21
---

## Overview

State the claim family or comparison question the page covers.

## Evidence Table

Provide structured rows for claim, source, scope qualifiers, outcome, and notes.

## Contradictions and Scope Mismatches

Record any explicit disagreements and classify them.

## Synthesis Notes

Summarize the current balance of evidence without overstating certainty.

## Related Pages

Link to chemicals, endpoints, biology, assays, datasets, and literature pages.

## References
```

Prefer this page type when machine-operable evidence tracking matters more than narrative explanation. Do not place evidence artifacts here. Summarize and collate multiple streams of evidence. Link to raw evidence artifacts.

## `workflow`

Use this template for repeatable agent procedures.

```md
---
id: literature-review-workflow
title: Literature Review Workflow
description: Workflow page describing the repeatable literature review process for the wiki.
slug: /workflows/literature-review-workflow
sidebar_label: Literature Review Workflow
page_type: workflow
entity_class: workflow
status: draft
last_reviewed: 2026-07-21
---

## Overview

State the workflow goal and expected output.

## Preconditions

State required inputs, permissions, and dependent pages or tools.

## Procedure

Describe the major steps in imperative form.

## Decision Points

State the main forks, thresholds, and escalation rules.

## Outputs

State what files, pages, records, or artifacts the workflow should produce.

## Quality Checks

State what must be true before the workflow is considered complete.

## Related Pages

Link to governance pages, templates, and target page families.
```

Use workflow pages for reusable operations, not for storing domain facts. Workflows may be atomic (e.g. instructions on using a specific API) or they can reference other workflows (e.g. a general workflow on testing carcinogenicity of a small molecule)

## `index`

Use this template for navigational pages.

```md
---
id: chemical-index
title: Chemical Index
description: Index page listing canonical chemical pages and key subgroups.
slug: /indices/chemical-index
sidebar_label: Chemical Index
page_type: index
entity_class: index
status: draft
last_reviewed: 2026-07-21
---

## Overview

State what the index helps users find.

## Index Contents

List pages by subgroup, alphabet, or another stable structure.

## Navigation Notes

Explain how to use the index and where to go for canonical content.

## Related Pages

Link to neighboring indices or master index pages.
```

Keep index pages navigational. Do not rely on them as canonical scientific authority. Index pages should serve as an endpoint when the Docusaurus sidebar is too broad. They should contain information purely to the end of aiding navigation.

## `governance`

Use this template for quality and policy pages.

```md
---
id: evidence-standards
title: Evidence Standards
description: Governance page defining evidence-quality requirements for wiki content.
slug: /quality/evidence-standards
sidebar_label: Evidence Standards
page_type: governance
entity_class: governance_rule
status: draft
last_reviewed: 2026-07-21
---

## Overview

State the rule set and what it governs.

## Policy

Write the governing rules in explicit normative language.

## Exceptions and Escalation

State when human review or override is required.

## Related Pages

Link to workflows, templates, and other governance pages.
```

Use governance pages to encode system rules clearly and unambiguously.

## `agent_operation`

Use this template for operational logs and audit records.

```md
---
id: task-run-2026-07-21-001
title: Task Run 2026-07-21 001
description: Agent operation record for a single task or repair run.
slug: /agent-operations/task-run-2026-07-21-001
sidebar_label: Task Run 001
page_type: agent_operation
entity_class: operation_record
status: draft
last_reviewed: 2026-07-21
---

## Overview

State what operation was performed and why.

## Inputs

Record the triggering request, source pages, tools, or dependencies.

## Actions Taken

Record the main steps executed.

## Outputs and Changes

List pages changed, claims affected, and artifacts produced.

## Review Notes

Record warnings, failures, or escalation needs.
```

Use agent-operation pages as audit memory. Keep them factual and operational.