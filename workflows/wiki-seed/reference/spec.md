# Wiki Specification Reference

This file defines the shared structural rules for all wiki pages. It is the common reference for `wiki-read`, `wiki-write`, and `wiki-verify`.

## Table of Contents

1. [Purpose and Scope](#purpose-and-scope)
2. [Page Types and Canonical Roles](#page-types-and-canonical-roles)
3. [Required Frontmatter](#required-frontmatter)
4. [Standard Page Structure](#standard-page-structure)
5. [Claim Format](#claim-format)
6. [Citation Format](#citation-format)
7. [Verification and Contradiction Metadata](#verification-and-contradiction-metadata)
8. [Links, Filenames, and Naming Rules](#links-filenames-and-naming-rules)
9. [Audit and Update Rules](#audit-and-update-rules)
10. [Minimum Page Checklist](#minimum-page-checklist)

## Purpose and Scope

This reference defines the minimum structure needed for pages to be readable by humans, retrievable by agents, and verifiable against sources. All substantive scientific content should be represented as claims with citations and clear scope. All pages should use stable frontmatter, consistent section order, and portable internal links.

This file is intentionally brief. It specifies the required shape of a page, not full workflow instructions.

## Page Types and Canonical Roles

Every page must declare a `page_type` and `entity_class` in frontmatter.

Use the following page types:

| page_type | Primary use | Canonical for |
|---|---|---|
| `concept` | Definitions and field-specific explanations | Terminology and scoped definitions |
| `chemical` | Substance pages | Chemical-specific synthesis |
| `biology` | Targets, pathways, species, tissues | Biological entities and mechanisms |
| `endpoint` | Toxicological outcomes | Endpoint definitions and evidence summaries |
| `assay` | Experimental or in silico assays | Assay definitions and interpretation |
| `dataset` | Data resources | Dataset scope, schema, and limitations |
| `model` | Computational methods and models | Method descriptions and applicability |
| `literature` | Paper, review, or report pages | Source-level summaries |
| `evidence` | Structured evidence pages | Extracted claims tied to sources |
| `workflow` | Agent or human procedures | Operational steps and decision rules |
| `index` | Navigation pages | Page discovery only; not substantive authority |
| `governance` | Policy and quality rules | Rules, standards, and review criteria |
| `agent_operation` | Task and execution records | Auditability of agent actions |

Canonicality guides conflict resolution. Index pages are not canonical for scientific claims. Evidence and source pages take precedence over summaries when the evidence is current and well-scoped.

### Top-level Wiki Structure

In addition to having a `page_type`, every page belongs to a top-level wiki category that determines its organizational location within the repository and its navigational context in Docusaurus. Top-level categories are conceptual and structural groupings of pages, while `page_type` describes the page’s semantic role, expected content, and validation rules. These two classifications often overlap, but they are not identical and should not be treated as interchangeable.

| Category | Purpose |
|---|---|
| `00-system` | Core pages describing the mission, architecture, roles, capabilities, and operating assumptions of the wiki and its agentic system. |
| `01-indices` | Navigation pages that organize and point to canonical pages without serving as the primary authority for scientific claims. |
| `02-concepts` | Pages defining field-specific concepts, terminology, and methodological ideas used across computational toxicology. |
| `03-chemicals` | Canonical pages for substances, mixtures, metabolites, and chemically centered evidence synthesis. |
| `04-biology` | Pages covering biological targets, pathways, tissues, species, and mechanistic context relevant to toxicology. |
| `05-toxicological-endpoints` | Pages describing adverse outcomes, hazard classes, and endpoint-specific evidence and interpretation. |
| `06-assays` | Pages for experimental and in silico assays, including what they measure, how results are interpreted, and known limitations. |
| `07-datasets` | Pages documenting data resources, schemas, provenance, access routes, coverage, and known caveats. |
| `08-models-and-methods` | Pages for computational models, analytical methods, and decision frameworks used in toxicology workflows. |
| `09-literature` | Source-oriented pages for papers, reviews, and reports that preserve provenance and structured source summaries. |
| `10-evidence` | Claim-centric pages, evidence tables, contradiction registers, and other structured records that support verification and synthesis. |
| `11-workflows` | Procedural pages describing repeatable human or agent workflows for ingestion, analysis, assessment, and reporting. |
| `12-agent-operations` | Operational records of agent tasks, tool calls, execution logs, and audit-relevant system actions. |
| `13-projects` | Pages organizing work around bounded initiatives, active investigations, deliverables, and project-specific context. |
| `14-quality-and-governance` | Policy pages defining evidence standards, citation rules, review criteria, and responsible-use constraints. |
| `15-glossary` | Lightweight definition pages or index-style terminology support for rapid lookup of recurring specialized terms. |

Top-level categories may have subfolders to provide more structure for groups of related pages. Create a subfolder only when a recurring group of pages within the same top-level category is large enough, distinct enough, or operationally important enough that grouping it improves retrieval, navigation, and maintenance more than it increases path complexity.

## Required Frontmatter

Every page must begin with YAML frontmatter.

### Required fields

```yaml
---
id: bisphenol-a
title: Bisphenol A
description: Chemical page for Bisphenol A with identifiers, evidence links, and endpoint summaries.
slug: /chemicals/bisphenol-a
sidebar_label: Bisphenol A
page_type: chemical
entity_class: chemical
status: draft
last_reviewed: 2026-07-21
verification_status: verified
---
```

### Required field definitions

| Field | Meaning |
|---|---|
| `id` | Stable page identifier used by agents and links |
| `title` | Human-readable page title |
| `description` | Short retrieval-friendly summary |
| `slug` | Stable URL path |
| `sidebar_label` | Short navigation label |
| `page_type` | One of the approved page types |
| `entity_class` | Domain entity class, such as `chemical`, `assay`, `dataset`, `workflow` |
| `status` | `draft`, `active`, `needs_review`, or `deprecated` |
| `last_reviewed` | ISO date of last substantive review |
| `verification_status` | See the [dedicated section](#page-level-verification-summary) on page-level verification for details |

### Recommended fields

Use these when applicable: `tags`, `aliases`, `sidebar_position`, `canonical_entity_id`, `source_priority`, `review_owner`, `backup_of`, `backups`, `kg_entity_id`.

## Standard Page Structure

Use a predictable section order. Headings may be adapted by page type, but the following pattern should be preserved.

### Core section order

1. **Overview**: Short summary of what the page covers.
2. **Scope and Notes**: Boundary conditions, exclusions, and terminology warnings.
3. **Key Claims or Definitions**: Atomic, citation-backed claims or definitions.
4. **Evidence or Details**: Source-grounded explanation, tables, or structured records.
5. **Related Pages**: Internal links to relevant concept, chemical, assay, dataset, or workflow pages.
6. **Open Questions or Review Notes**: Unresolved issues, contradictions, or review flags.
7. **References**: Full citations or links to evidence/source pages.

### Page-type guidance

- `concept` pages should define the term, explain how it is used in toxicology, and distinguish it from neighboring concepts.
- `chemical` pages should emphasize identifiers, relevant endpoints, assay evidence, mechanism links, and known limitations.
- `assay` pages should describe what the assay measures, how to interpret outputs, and common limitations.
- `dataset` pages should state data origin, schema, field meaning, access route, and known caveats.
- `literature` pages should summarize the source rather than repeating all source text.
- `evidence` pages should be structured and claim-centric.
- `workflow` and `governance` pages may contain imperative instructions, but should still cite any scientific assertions.

If it is not absolutely clear how to structure a page, refer to the [Page Template Examples](../../../wiki/docs/00-system/page-templates-examples.md) document

## Claim Format

All substantive scientific content should be represented as claims. A claim is the basic unit for verification, contradiction checking, and synthesis.

### Claim requirements

Each claim should be atomic, scoped, and traceable. Avoid combining multiple conclusions in one claim unless they directly imply each other.

### Minimum claim schema

| Field | Meaning |
|---|---|
| `claim_id` | Stable, local or global identifier |
| `page_id` | Page containing the claim |
| `claim_type` | `definition`, `fact`, `identifier`, `method`, `result`, `interpretation`, `workflow_assertion`, `summary` |
| `statement` | Plain-language claim text |
| `subject` | Main entity |
| `predicate` | Relation or asserted property |
| `object` | Related entity, value, or outcome |
| `qualifiers` | Scope conditions such as species, assay, endpoint, dose, route, time, tissue, population |
| `citations` | One or more citation IDs |
| `verification_status` | Verification outcome |
| `confidence` | `low`, `medium`, `high`, or a numeric score if used consistently |
| `depends_on` | Other claim IDs required for this claim |
| `notes` | Short clarification if needed |

### Claim example

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
```

### Claim rules

A claim must be specific enough to verify. Scope qualifiers matter. Claims about mechanisms, hazards, or assay performance **must not omit** relevant context if the source is qualified. Definitions should be domain-specific when the general definition is already common knowledge.

## Citation Format

Every substantive claim must cite at least one source, dataset, or evidence page unless it is clearly non-substantive page metadata.

### Minimum citation schema

| Field | Meaning |
|---|---|
| `citation_id` | Stable citation identifier |
| `source_type` | `review`, `paper`, `report`, `dataset`, `book`, `website`, `evidence_page` |
| `title` | Source title |
| `authors` | Author list or organization |
| `year` | Publication year |
| `container` | Journal, book, repository, or publisher |
| `doi` | DOI if available |
| `url` | Stable URL if available |
| `access_status` | `open_access`, `restricted`, `unknown` |
| `allowed_source` | `true` or `false` |
| `retrieved_on` | Date accessed |
| `pages_or_sections` | Relevant page range, figure, table, or section |
| `notes` | Short provenance or interpretation note |

### Citation example

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

### Citation rules

Citations must be complete enough for source resolution. If a claim is derived from a dataset, cite the dataset page and, when possible, the underlying publication or documentation. If a claim is synthesized from multiple sources, cite all material sources rather than only the most recent one.

## Verification and Contradiction Metadata

Claims that have completed verification must receive one of the following statuses:

| verification_status | Meaning | When to use |
|---|---|---|
| `supported` | The cited source supports the claim as written, including its scope and qualifiers. | Use when the statement matches the evidence closely enough that no meaningful narrowing or rewording is needed. |
| `unsupported` | No acceptable supporting evidence was found for the claim. | Use when the cited source does not contain the claim, the support is absent, or the available evidence is too weak to justify keeping the claim. |
| `overstated` | The source supports a narrower, weaker, or more qualified version of the claim than the page currently states. | Use when the direction of the claim is broadly right but the wording is too strong, too general, or missing important scope conditions. |
| `contradicted` | The best available evidence conflicts with the claim as written. | Use when a valid, relevant source or canonical evidence page shows that the claim is materially false or incompatible with stronger evidence. |
| `source_inaccessible` | The claim could not be fully checked because the supporting source could not be accessed under policy. | Use when the claim might be true, but the verifier cannot inspect the full supporting evidence through allowed access routes. |
| `needs_human_review` | The claim cannot be resolved confidently by automated verification alone. | Use when the claim depends on expert interpretation, competing standards, unresolved literature disagreement, or ambiguous source language. |

Use the following contradiction types when relevant: `true_contradiction`, `scope_mismatch`, `temporal_mismatch`, `granularity_mismatch`, `terminology_mismatch`, `uncertainty_mismatch`.

Contradiction checks must run only on claims that have completed claim-level verification and received a status.

## Page-level Verification Summary

In addition to claim-level verification, pages may expose a page-level verification summary so readers and agents can quickly judge trustworthiness without inspecting every claim individually. When present, this should be located in the page's YAML frontmatter. 

### Recommended page-level fields

| Field | Meaning |
|---|---|
| `verification_status` | Tag (enumerated below) summarizing the verification status of the page as a whole |
| `verification_notes` | Short free-text summary of the verification outcome |
| `verified_on` | ISO date of the most recent verification run |
| `verified_claim_count` | Number of claims marked `supported` |
| `unresolved_claim_count` | Number of claims still unresolved |

These fields summarize the page as a whole and must not replace claim-level statuses.

**Page-level Verification Statuses**

Most fields making up the verification summary are optional but this field is required. If this field is null for any reason, it should be treated as `unverified`.

| verification_status | Meaning | When to use |
|---|---|---|
| `unverified` | The page has not yet been checked in a systematic way against its cited sources. | Use for newly created or heavily revised pages before a verification pass has reviewed the substantive claims. |
| `partially_verified` | Some substantive claims on the page have been verified, but one or more claims remain unchecked or unresolved. | Use when verification has started and produced meaningful results, but the page is not yet fully reviewed end-to-end. |
| `verified` | All substantive claims currently on the page have been checked and are adequately supported by allowed, accessible sources, with any needed qualifications already applied. | Use only after a complete verification pass has finished and no unresolved claim-level issues remain that materially affect interpretation. |
| `source_access_failed` | Verification could not be completed because one or more important supporting sources could not be accessed under the current source policy. | Use when the page cannot be fully validated due to inaccessible full text, unresolved source metadata, broken links, or policy-disallowed access routes. |
| `claim_mismatch` | One or more substantive claims on the page do not match the cited evidence closely enough to be accepted as written. | Use when the page contains unsupported, overstated, contradicted, or materially mis-scoped claims that still need repair. |
| `needs_human_review` | Automated verification found ambiguity, high-impact disagreement, or a judgment call that should not be resolved autonomously. | Use when the page involves unresolved scientific conflict, regulatory nuance, safety-critical interpretation, or evidence that requires expert adjudication. |

## Literature and Derived Pages

`literature` pages may be lightweight source records containing citation metadata, scope notes, extracted-key-claim pointers, and links to canonical target pages. If a page is mainly synthetic or derivative, it should link back to the evidence-bearing or canonical pages rather than acting as the sole authority.

## Links, Filenames, and Naming Rules

Use natural-language page titles in the Markdown front matter and filesystem-safe slugs for filenames.

| Wiki Concept Name | Docusaurus Filename | Example Internal Link |
|---|---|---|
| `Bisphenol A` | `bisphenol-a.md` | `[Bisphenol A](../03-chemicals/bisphenol-a.md)` |
| `Aryl Hydrocarbon Receptor` | `aryl-hydrocarbon-receptor.md` | `[Aryl Hydrocarbon Receptor](../04-biology/targets/aryl-hydrocarbon-receptor.md)` |
| `Dose-Response Relationship` | `dose-response-relationship.md` | `[Dose-Response Relationship](../02-concepts/dose-response-relationship.md)` |
| `Tox21 Dataset` | `tox21.md` | `[Tox21](../07-datasets/tox21.md)` |
| `Literature Review Workflow` | `literature-review-workflow.md` | `[Literature Review Workflow](../11-workflows/literature-review-workflow.md)` |


Rules:

- Use lowercase `kebab-case` for folders and filenames.
- Avoid spaces, brackets, punctuation-heavy names, and special characters in filenames.
- Preserve precise scientific capitalization in `title` front matter, not in filenames.
- Use stable slugs; do not rename files casually after agents or users begin linking to them.
- Prefer relative links between pages so the wiki remains portable across deployments.
- Keep machine-readable identifiers in front matter, even when the filename is human-readable.

### Linking rules

Use relative internal Markdown links where possible.

```md
[Bisphenol A](../03-chemicals/bisphenol-a.md)
```

Link to canonical pages rather than repeating content. If a page summarizes a claim maintained elsewhere, cite or link to the evidence-bearing page.

### Naming rules

Use stable identifiers for chemicals, assays, datasets, endpoints, and workflows. Record aliases in frontmatter or a dedicated alias section when synonyms are common.

## Audit and Update Rules

Major repairs must be auditable.

### Required audit information

| Field | Meaning |
|---|---|
| `audit_id` | Stable audit record ID |
| `page_id` | Page changed |
| `changed_claims` | Claim IDs added, revised, or removed |
| `reason` | Why the change was made |
| `sources_reviewed` | Citation IDs reviewed during the change |
| `change_type` | `verification_patch`, `contradiction_repair`, `source_repair`, `rewrite`, `backup_restore` |
| `timestamp` | When the change occurred |
| `review_needed` | Whether human review is required |

When a contradiction requires large-scale repair, create a backup page or version link, preserve as many supported claims as possible, and mark the updated page `needs_review` or `needs_human_review` as appropriate.

## Minimum Page Checklist

A page is minimally compliant if all of the following are true:

- [ ] Page has valid required frontmatter.
- [ ] Page declares a `page_type` and `entity_class`.
- [ ] Page follows standard section order closely enough to remain predictable.
- [ ] Every substantive claim is atomic enough to verify.
- [ ] Every substantive claim has one or more citations.
- [ ] Citations are resolvable and allowed by source policy.
- [ ] Verified claims have a verification status.
- [ ] Contradiction checks operate on verified claims, not raw prose.
- [ ] Internal links use stable relative paths or stable slugs.
- [ ] Major repairs leave an audit trail.

If a page fails any of these checks, it should be treated as incomplete and prioritized for cleanup before advanced synthesis or contradiction repair.