---
name: wiki-read
description: Provides instructions on how to retrieve conceptual and procedural toxicology-related information from the wiki.
---

# Dependent Skill Execution Rule

> [!IMPORTANT]
> Execute this skill only if the seeded wiki already exists and the canonical in-wiki reference files are available at the expected relative paths.
> Before running this skill, confirm that the shared wiki specification is available at [reference-wiki-spec.md](../../../wiki/docs/00-system/reference-wiki-spec.md), the top-level category guidance is available at [top-level-wiki-categories-reference.md](../../../wiki/docs/00-system/top-level-wiki-categories-reference.md), and the page template examples are available at [wiki-page-template-examples-by-type.md](../../../wiki/docs/00-system/wiki-page-template-examples-by-type.md).
> Treat these files as pre-existing runtime references installed by initial wiki seeding.
> Do not run, invoke, recommend, or recreate `wiki-seed` from this skill.
> If any required reference file is unavailable, stop and report the missing prerequisite.

## Routing Instructions

Use this skill to look up:
- procedures
- workflows
- templates for report-generation
- high-level overviews of different tools, APIs, and data sources
- concepts in toxicology, biology, or chemistry

Do **not** use this skill when you need:
- factual claims about specific compounds
- chemical identifiers
- entity relationships
- assay results
- atomic claims extracted from literature

If you are still unclear on whether you should look for information in the wiki, read the full routing policy: `./routing_policy.yaml`

## Finding information in the wiki

When retrieving information from the wiki, navigate from the most general reliable location to the most specific relevant page. Prefer structured navigation over full-text search whenever possible.

### Recommended retrieval flow

1. **Clarify the information need.** First determine what kind of information you are looking for: a concept, workflow, dataset, assay, endpoint, biological entity, source summary, or another page type. This determines where you should begin.
2. **Start from the highest-value entry point.** If you do not already know the exact page, begin with the most appropriate top-level category or index page. Use index pages for navigation, not as the final authority for scientific content.
3. **Move to the canonical page.** Once you identify the relevant entity or topic, navigate to the most canonical page for that subject. Prefer concept, chemical, biology, assay, dataset, model, endpoint, evidence, or literature pages over index pages when retrieving substantive information.
4. **Use related-page links to refine context.** If the first canonical page is relevant but incomplete, follow its internal links to closely related pages such as supporting evidence pages, source pages, workflows, or neighboring concepts.
5. **Check verification and scope before relying on content.** Before using information from a page, inspect its frontmatter and citations to determine whether the content is current, verified, partially verified, or flagged for review. Pay attention to qualifiers such as species, assay system, endpoint, dose, route, time, and evidence context.
6. **Compare across pages only when needed.** If the question requires synthesis, disagreement analysis, or broader context, read across multiple relevant canonical pages and note any differences in scope, evidence quality, or verification status.
7. **Use full-text search only as a fallback.** If structured navigation fails, use full-text search restricted to `./wiki/docs`, then trace any matching result back to the most canonical page rather than relying on an isolated search hit. WARNING: Exclude the top-level categories `12-agent-operations` and `13-projects` from all default wiki navigation and full-text search. Search `12-agent-operations` only when the task explicitly requires operational records, execution traces, audit logs, or prior agent task history. Search `13-projects` only when the task explicitly requires project-specific context, deliverables, or local working notes. Do not use pages in either category as primary sources of domain facts, scientific claims, or canonical knowledge.

> **Default Search Rule:** When using wiki navigation or full-text search for domain knowledge, prioritize the canonical knowledge categories `01-indices`, `02-concepts`, `03-chemicals`, `04-biology`, `05-toxicological-endpoints`, `06-assays`, `07-datasets`, `08-models-and-methods`, `09-literature`, `10-evidence`, `11-workflows`, and `14-quality-and-governance`. Start with `01-indices` when the target page is unknown, then move to the most canonical page for the topic. Use `09-literature` for source-level provenance, `10-evidence` for claim-level support and contradiction handling, and `11-workflows` for procedural tasks. Treat these categories as the default search space unless the task explicitly requires system architecture (`00-system`), operational history (`12-agent-operations`), project-local context (`13-projects`), or lightweight terminology support (`15-glossary`).

### Navigation heuristics

- Start with an **index page** when you know the general area but not the exact page.
- Start with a **workflow page** when you are performing a task and need the next operational step.
- Start with a **concept or entity page** when you already know the likely topic but need explanation, context, or linked evidence.
- Prefer **evidence-bearing and canonical pages** over summaries when factual precision matters.

### Backtracking

If a navigation path does not lead to the needed information, note which pages or branches you already checked, then backtrack to the last useful decision point and try a different path. Do not continue exploring loosely related pages once the search direction has clearly gone off target.

## Verification of claims

When reading a wiki entry, always account for the status of that wiki page. Each wiki page contains the following frontmatter:
```yaml
status:
verification_status:
```

And may optionally also contain:
```yaml
verification_notes:
verified_on:
verified_claim_count:
unresolved_claim_count:
```

Use these fields when determining how trustworthy the information in this page is.