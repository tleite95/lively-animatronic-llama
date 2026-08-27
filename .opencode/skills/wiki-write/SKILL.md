---
name: wiki-write
description: Use this skill whenever you are modifying a markdown file in `@{ROOT}:/wiki/docs`. Only use this skill once a document has been ingested and its claims have been extracted. Provides instructions on how to store claim-level information in the wiki, how to format new pages, and how to maintain existing pages when editing.
---

## Required reference

Before performing this skill, read and follow [Wiki Specification Reference](@{REF}:/wiki/spec.md).

Use that reference for:
- required frontmatter
- page structure
- claim format
- citation format
- verification statuses
- linking and naming rules

If this skill conflicts with the shared reference, follow this skill only where it states a task-specific exception explicitly.

## When to Create or Edit a Wiki Page

You should prefer to place information in an existing page rather than creating a new page. When determining where to place new information, a top-down approach should be taken:

1. Read through the sidebar and determine which categories may be relevant. Order them by relevance. If it is not clear just from the sidebar, see the [Top-Level Category Reference](@{REF}:/wiki/top-level-categories.md) document for more information.
2. For each relevant page type, find pages of that type that may be relevant to this claim **OR** if there is no relevant page, create a new one.
3. Within each relevant page, find the best section for this information 
4. Choose the best option from the final list of sections in pages **OR** if there is no good fit, create a new section in the most relevant page.

The default action should be to edit an existing page because the wiki is most useful when information about the same concept, entity, assay, endpoint, dataset, or workflow accumulates in one place. When checking if a page already exists, do not invent a file name and then check for that specifically. Instead, enumerate pages in the relevant categories and check each for candidates of already-existing pages with this information. A new page should only be created when the incoming material is about a genuinely distinct object of knowledge, when merging it into an existing page would blur scope or provenance, or when the material is likely to be revisited often enough that retrieval, synthesis, and maintenance will benefit from having a stable canonical location.

In practice, the decision should be based on identity, scope, and future reuse. If the new information clarifies or extends an existing concept, adds evidence about an already-tracked chemical or endpoint, or enriches an existing workflow or method, it belongs on the existing page with proper citation and any needed updates to evidence or contradiction sections. If the information introduces a new recurring concept, a distinct biological target, a dataset not yet represented, a new assay family, or another entity that is likely to be referenced across many future documents, then a new page is justified.

## New Section Creation Flow

A new section should be created only after the agent has determined that the target page is correct but that none of its existing sections can hold the information cleanly. The new section should be the smallest stable semantic container that fits the material, using the page template whenever possible so that sections remain predictable across similar pages. Section titles should describe enduring categories such as “Mechanistic Relevance,” “Applicability Domain,” “Conflicting Evidence,” or “Open Questions,” rather than source-specific labels that will not generalize.

Before adding the section, the agent should decide whether the information is likely to grow through future ingestion and whether the section helps retrieval, comparison, or evidence synthesis. If the content is only a sentence or two that naturally fits inside an existing section, the page should be edited without adding structural overhead. If the information reflects disagreement, uncertainty, or unresolved interpretation, the agent should prefer a dedicated section that preserves the tension explicitly rather than forcing premature synthesis into a consensus statement.

## New Page Creation Flow

A new page should be created when the incoming material is about a distinct and durable unit of knowledge that is likely to accumulate more evidence, links, or operational use over time. When making a new page, do the following in order:
- [ ] Select the page type
- [ ] Assign a stable title, identifier, and slug
- [ ] Instantiate the minimum required structure for that page type so the page is immediately usable. The initial version does not need to be exhaustive, but it should be coherent, citable, and clearly scoped. Make sure you use the relevant template from the [Template Example Document](@{REF}:/wiki/page-templates-examples.md)

Each new page should begin with a concise summary of what the page is about, the key identifiers or aliases needed for retrieval, and the most important relationships to other pages in the wiki. It should then include non-stup content only the sections necessary to hold the ingested material, along with citations, uncertainty notes, and cross-links to source pages, evidence pages, and indices. When a page is created from a source document, the source-specific framing should remain on the literature page, while facts, definitions, and linked evidence should be transferred to the new canonical page so that future synthesis can occur across many documents instead of being trapped inside one source.

## Verification

When inserting a claim, retrieve existing wiki content on the same concept before writing, and where the new source disagrees with existing content - for instance, differing NOAEL-to-BMD preferences between US EPA and EFSA guidance, or differing confidence levels across reviews on a given AOP's endorsement status - preserve both positions explicitly on the page, attribute each to its source, and characterize the nature of the disagreement (methodological, jurisdictional, or genuinely unresolved in the literature) rather than silently picking one. Do not perform heavy-duty verification as part of this skill. Cross-checking and contradiction handling is treated as a standing background process rather than a one-time step, and there is a dedicated flow for verification that is not in-scope for this skill.

## Required Outputs of Writing

A successful write pass should leave behind a page that has valid frontmatter, correctly placed content, atomic claims where needed, complete citations, stable internal links, and an explicit review-notes section whenever uncertainty or conflict remains.

When editing an existing page, preserve stable claim IDs whenever possible. Create new claim IDs only for genuinely new claims or when an old claim has been split into materially different atomic claims.

## Provenance Preservation

If the incoming material comes from a paper, review, or report, ensure that a corresponding literature or source record exists so provenance is not lost, even if the normalized facts are written onto canonical concept or entity pages.

## Discoverability Maintenance

When creating a new canonical page, update the most relevant index page or leave a clearly marked TODO note on that index so the new page remains discoverable through normal wiki navigation rather than only by search.

## Human Readability

A substantive page should satisfy two checks:
1. A human reader can identify the page purpose, scope, key claims, verification state, and open issues from headings and prose before inspecting structured records.
2. Structured claim, citation, or audit blocks are paired with concise readable statements, tables, or summaries that explain their significance.

## Operation Rules Summaries / Tasklists

### Page Creation Rules

Before creating a page:

1. Search for existing canonical pages, aliases, near-duplicates, source records, evidence records, and indices.
2. Determine the page's primary object of knowledge.
3. Assign exactly one top-level category.
4. Assign one approved `page_type`.
5. Select the smallest compliant template from `page-templates-examples.md`.
6. Create valid YAML frontmatter with required fields.
7. Use lowercase kebab-case for filenames, IDs, and slugs where appropriate.
8. Include aliases for common synonyms, acronyms, chemical names, regulatory labels, or spelling variants.
9. Add atomic claims only when supported by citations.
10. Add related pages using relative links.
11. Set page-level `verification_status` to `unverified` unless a complete verification pass has been completed.

Prefer updating a canonical page over creating a duplicate. If a term is lightweight, create or update a glossary page or index pointer instead of a full concept page.

### Page Update Rules

When updating a page:

- Preserve stable IDs, slugs, and existing valid links unless a repair requires migration.
- Preserve supported claims when repairing unsupported or contradicted content.
- Do not remove uncertain content silently; narrow it, mark it, move it, or create review notes.
- Update `last_reviewed` only after substantive review.
- Update verification fields only when verification actually occurred.
- Add audit records for major repairs, contradiction handling, source repairs, rewrites, and backup restores.
- If a broad rewrite is needed, minimize disruption to stable internal links.