---
name: wiki-write
description: Use this skill whenever you are modifying a markdown file in `./wiki/docs.` Only use this skill once a document has been ingested and its claims have been extracted. Provides instructions on how to store claim-level information in the wiki, how to format new pages, and how to maintain existing pages when editing.
---

# Dependent Skill Execution Rule

> [!IMPORTANT]
> Execute this skill only if the seeded wiki already exists and the canonical in-wiki reference files are available at the expected relative paths.
> Before running this skill, confirm that the shared wiki specification is available at [reference-wiki-spec.md](../../../wiki/docs/00-system/reference-wiki-spec.md), the top-level category guidance is available at [top-level-wiki-categories-reference.md](../../../wiki/docs/00-system/top-level-wiki-categories-reference.md), and the page template examples are available at [wiki-page-template-examples-by-type.md](../../../wiki/docs/00-system/wiki-page-template-examples-by-type.md).
> Treat these files as pre-existing runtime references installed by initial wiki seeding.
> Do not run, invoke, recommend, or recreate `wiki-seed` from this skill.
> If any required reference file is unavailable, stop and report the missing prerequisite.

## Required reference

Before performing this skill, read and follow [Wiki Specification Reference](../../../wiki/docs/00-system/reference-wiki-spec.md).

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

1. Read through the sidebar and determine which categories may be relevant. Order them by relevance. If it is not clear just from the sidebar, see the [Top-Level Category Reference](../../../wiki/docs/00-system/top-level-wiki-categories-reference.md) document for more information.
2. For each relevant page type, find pages of that type that may be relevant to this claim **OR** if there is no relevant page, create a new one.
3. Within each relevant page, find the best section for this information 
4. Choose the best option from the final list of sections in pages **OR** if there is no good fit, create a new section in the most relevant page.

The default action should be to edit an existing page because the wiki is most useful when information about the same concept, entity, assay, endpoint, dataset, or workflow accumulates in one place. A new page should only be created when the incoming material is about a genuinely distinct object of knowledge, when merging it into an existing page would blur scope or provenance, or when the material is likely to be revisited often enough that retrieval, synthesis, and maintenance will benefit from having a stable canonical location.

In practice, the decision should be based on identity, scope, and future reuse. If the new information clarifies or extends an existing concept, adds evidence about an already-tracked chemical or endpoint, or enriches an existing workflow or method, it belongs on the existing page with proper citation and any needed updates to evidence or contradiction sections. If the information introduces a new recurring concept, a distinct biological target, a dataset not yet represented, a new assay family, or another entity that is likely to be referenced across many future documents, then a new page is justified.

## New Section Creation Flow

A new section should be created only after the agent has determined that the target page is correct but that none of its existing sections can hold the information cleanly. The new section should be the smallest stable semantic container that fits the material, using the page template whenever possible so that sections remain predictable across similar pages. Section titles should describe enduring categories such as “Mechanistic Relevance,” “Applicability Domain,” “Conflicting Evidence,” or “Open Questions,” rather than source-specific labels that will not generalize.

Before adding the section, the agent should decide whether the information is likely to grow through future ingestion and whether the section helps retrieval, comparison, or evidence synthesis. If the content is only a sentence or two that naturally fits inside an existing section, the page should be edited without adding structural overhead. If the information reflects disagreement, uncertainty, or unresolved interpretation, the agent should prefer a dedicated section that preserves the tension explicitly rather than forcing premature synthesis into a consensus statement.

## New Page Creation Flow

A new page should be created when the incoming material is about a distinct and durable unit of knowledge that is likely to accumulate more evidence, links, or operational use over time. The agent should first select the page type, then assign a stable title, identifier, and slug, and finally instantiate the minimum required structure for that page type so the page is immediately usable by both humans and agents. The initial version does not need to be exhaustive, but it should be coherent, citable, and clearly scoped.

Each new page should begin with a concise summary of what the page is about, the key identifiers or aliases needed for retrieval, and the most important relationships to other pages in the wiki. It should then include only the sections necessary to hold the ingested material, along with citations, uncertainty notes, and cross-links to source pages, evidence pages, and indices. When a page is created from a source document, the source-specific framing should remain on the literature page, while durable normalized facts, definitions, and linked evidence should be transferred to the new canonical page so that future synthesis can occur across many documents instead of being trapped inside one source.

## Verification

When inserting a claim, retrieve existing wiki content on the same concept before writing, and where the new source disagrees with existing content - for instance, differing NOAEL-to-BMD preferences between US EPA and EFSA guidance, or differing confidence levels across reviews on a given AOP's endorsement status - preserve both positions explicitly on the page, attribute each to its source, and characterize the nature of the disagreement (methodological, jurisdictional, or genuinely unresolved in the literature) rather than silently picking one. Do not perform heavy-duty verification as part of this skill. Cross-checking and contradiction handling is treated as a standing background process rather than a one-time step, and there is a dedicated flow for verification that is not in-scope for this skill.

## Required Outputs of Writing

A successful write pass should leave behind a page that has valid frontmatter, correctly placed content, atomic claims where needed, complete citations, stable internal links, and an explicit review-notes section whenever uncertainty or conflict remains.

When editing an existing page, preserve stable claim IDs whenever possible. Create new claim IDs only for genuinely new claims or when an old claim has been split into materially different atomic claims.

## Provenance Preservation

If the incoming material comes from a paper, review, or report, ensure that a corresponding literature or source record exists so provenance is not lost, even if the normalized facts are written onto canonical concept or entity pages.

## Discoverability Maintenance

When creating a new canonical page, update the most relevant index page or leave a clearly marked TODO note on that index so the new page remains discoverable through normal wiki navigation rather than only by search.