---
name: wiki-verify
description: Use this skill whenever you are verifying a file in `./wiki/docs.` Provides instructions on how to verify the authenticity of the information stored in the file, check for contradictions across files, and find sources for evidence to support weak claims.
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

## Initial page setup

All seeded wiki pages should initially be treated as **draft, in need of review** until a verification flow confirms that their claims are supported by accessible, durable, and explicitly permitted sources. The verification flow should function as a linting and patching pipeline: identify claims, resolve cited sources, check source accessibility, compare page statements against the cited evidence, and either approve, flag, or patch the page.

## Verification checklist

When verifying a page:

- [ ] Ensure every substantive claim has either been classified as metadata or has been processed through the [Claim-Level Verification Flow](#claim-level-verification-flow).
- [ ] Replace, repair, or qualify any claims supported only by disallowed or inaccessible sources. See [Repair Strategy for Non-Open-Access Sources](#repair-strategy-for-non-open-access-sources) for instructions on this step.
- [ ] After claim-level verification is complete, check the page for contradictions. See [Resolving Contradictions Flow](#resolving-contradictions-flow) for instructions on this step.

## Resolving Contradictions Flow

Only resolve contradictions between verified claims. A claim counts as verified once it has completed the claim-level verification flow and has been assigned a status such as `supported`, `unsupported`, `overstated`, `contradicted`, `source_inaccessible`, or `needs_human_review`. Do not perform contradiction checking on raw, unverified text. Check contradictions in the following order:

1. Against the knowledge graph
2. Within the page itself
3. Against other pages

### Checking for contradictions against the knowledge graph

The knowledge graph should be treated as the default canonical reference layer, not as an unquestionable authority. When a wiki claim appears to contradict a graph fact, first verify that both refer to the same entity, relation, and scope. Classify the discrepancy as a true contradiction, scope mismatch, temporal mismatch, uncertainty mismatch, or terminology mismatch. Compare the provenance, confidence, and recency of the wiki claim and graph fact before making changes. If the graph fact is clearly better supported and the wiki claim has no dependent claims, replace the wiki claim, record the graph provenance, and make minimal edits for coherence. If dependent claims rely on the contradicted claim, identify the dependency set and re-evaluate each dependent claim against its cited sources before removing or revising it. If the discrepancy reflects legitimate evidence conflict or unresolved scientific uncertainty, preserve the competing claims in qualified form, summarize the disagreement, and flag the page for human review. If the contradiction affects a substantial part of the page or multiple linked pages, create a backup, reconstruct the affected claims from cited sources, update all impacted summaries and indices, and mark the result as `needs_human_review`. Every repair must leave an audit trail containing the prior text, affected claim IDs, graph assertions used, provenance, timestamps, and rationale.

### Checking for contradictions within the page itself

Claims on a page should be checked for internal consistency at the claim level rather than the sentence level. When two claims on the same page appear to conflict, first verify that they refer to the same entity, relation, and scope. Before treating them as contradictory, compare their qualifiers, including species, biological system, endpoint, dose, route, timing, and evidentiary context. Classify the discrepancy as a true contradiction, scope mismatch, temporal mismatch, uncertainty mismatch, granularity mismatch, or terminology mismatch.

If the claims are not actually contradictory, revise the page only as needed to make the distinction explicit. Prefer adding clarifying qualifiers, cross-references, or brief synthesis text over deleting content. If one claim is clearly less supported than the other based on citation quality, recency, provenance, or scope accuracy, revise or remove the weaker claim and update any dependent claims, summaries, tables, or conclusions on the page. If both claims are supported but reflect unresolved disagreement in the literature, preserve both in qualified form, add a short synthesis explaining the disagreement, and mark the page or section as `needs_human_review` if the conflict affects interpretation.

If one contradicted claim supports downstream claims on the same page, identify the dependent claims and re-check each one against its cited sources before revising or removing it. If the contradiction affects only a local subsection, repair that subsection while preserving page structure when possible. If the contradiction undermines the page’s framing, summary, or major conclusions, create a backup, reconstruct the affected section from cited sources, and mark the page as `needs_human_review`.

Every internal contradiction repair must record the affected claim IDs, the contradiction type, the citations reviewed, the rationale for the revision, and whether dependent claims were updated.

Summary paragraphs, key-takeaway sections, and infoboxes must not state stronger conclusions than the body of the page supports. If a contradiction exists between the summary and the detailed evidence, the summary must be revised first.

### Checking for contradictions against other pages

When a claim on one wiki page appears to contradict a claim on another wiki page, first verify that the two claims refer to the same entity, relation, and scope. Compare qualifiers such as species, assay system, endpoint, dose, route, timing, and evidence context before classifying the discrepancy. Classify the discrepancy as a true contradiction, scope mismatch, temporal mismatch, uncertainty mismatch, granularity mismatch, or terminology mismatch.

Do not assume that either page is automatically correct. Instead, consult the canonical page type for the claim domain, along with the cited sources on both pages. If one page is non-canonical for the disputed claim type and merely summarizes or transcludes information from a more canonical page, update the non-canonical page to match the better-supported source page and preserve any necessary qualifiers. If both pages are peer pages with independent claims, compare their citations, provenance, recency, and scope, and determine whether the contradiction is real or only apparent.

If the two claims can be reconciled by adding qualifiers or clarifying scope, revise both pages as needed so they no longer appear inconsistent. If one claim is clearly less supported, revise or remove it and update any dependent summaries, tables, indices, or backlinks. If both claims are supported but reflect unresolved disagreement in the literature, preserve both in qualified form, add reciprocal links between the pages, summarize the disagreement explicitly, and mark both pages as `needs_human_review` if the disagreement affects interpretation or downstream workflows.

If the contradiction propagates into multiple pages, create backups of the affected pages, identify the set of downstream pages that repeat or rely on the disputed claim, and repair the page set in a dependency-aware order, starting with the most canonical evidence-bearing page and then updating derivative pages. Every cross-page contradiction repair must leave an audit trail containing the affected claim IDs, pages changed, contradiction type, citations reviewed, canonicality decision, rationale for the chosen repair, and any pages flagged for human review.

When claims conflict across pages, the system should prefer the most canonical page type for that claim domain, provided that the canonical page is adequately sourced and up to date. Canonicality guides repair order and default preference, but it does not override stronger evidence on a non-canonical page. If a non-canonical page contains better-supported or newer evidence, the canonical page must be updated rather than forcing the derivative page to conform to outdated content.

## Claim-Level Verification Flow

1. **Extract claims:** Split each page into atomic scientific claims, definitions, identifiers, workflow assertions, and source-dependent statements.
Each claim must be associated with:
- a unique claim ID
- source citations
- scope qualifiers such as species, tissue, assay, endpoint, dose, route, time, and population
- confidence or evidence strength
- status such as draft, supported, uncertain, needs_review
2. **Map claims to citations:** Require every substantive claim to cite at least one source, dataset, or evidence page.
3. **Resolve sources:** Check DOI, URL, title, publication year, authors, and repository location.
4. **Check access:** Confirm that the full supporting source is available under the open-access policy. Refer to the [Allowed Source Policy](#allowed-source-policy) to verify sources are allowed.
5. **Compare evidence:** Verify that the source actually supports the claim, including organism, endpoint, assay, dose/exposure context, and uncertainty.
6. **Classify outcome:** Mark each claim as `supported`, `unsupported`, `overstated`, `contradicted`, `source_inaccessible`, or `needs_human_review`.
7. **Patch page:** Apply minimal edits that preserve useful structure while removing or qualifying unsupported content.
8. **Write audit record:** Store the verification result, source decisions, patches applied, and remaining open questions.

## Fallback When No Knowledge Graph Is Available

If no knowledge graph is available, skip the graph-comparison phase and proceed with within-page and cross-page contradiction checks using canonical wiki pages and cited sources. The absence of a graph should not block verification.

## Allowed Source Policy

The default verification policy should be **open-access only** unless a human explicitly opts into licensed institutional access. Allowed sources should include:

1. **Open-access journal articles** with full text available from the publisher, PubMed Central, Europe PMC, arXiv, bioRxiv, medRxiv, ChemRxiv, or other legitimate repositories.
2. **Government and intergovernmental sources**, including EPA, FDA, NIH, NTP, OECD, ECHA, EFSA, WHO, IARC, and comparable public regulatory bodies.
3. **Public databases and documentation**, including EPA CompTox Chemicals Dashboard, ToxCast/Tox21 documentation, PubChem, ChEMBL, UniProt, Gene Ontology, CTD, and public assay/dataset documentation.
4. **Open technical reports, standards, and guidance documents** that are freely accessible without login, subscription, or institutional proxy.
5. **Open-source software documentation and repositories** for models, workflows, or computational methods, when relevant.

Disallowed by default:

- Paywalled articles where the agent can only access the abstract.
- Sources requiring UW/library login, subscription access, or institutional proxy.
- Unauthorized copies on file-sharing sites.
- Citation-only references that cannot be resolved to accessible content.
- Claims sourced only to model memory.

## Repair Strategy for Non-Open-Access Sources

When a cited source is not open-access, the agent should not silently retain it as support. Instead, it should apply the following sequence:

1. **Find an open version of the same work:** Check PubMed Central, Europe PMC, publisher OA status, preprint servers, author manuscripts, and institutional repositories.
2. **Replace with an equivalent open source:** If the exact source is unavailable, find an open review, regulatory report, database entry, or primary study supporting the same claim.
3. **Downgrade the claim if needed:** If only weaker evidence is available, revise language from definitive to qualified, e.g. “has been reported to” or “is associated with evidence for.”
4. **Move unresolved support to a review queue:** If no acceptable source exists, retain the page structure but remove or mark the claim as `citation_needed` or `needs_human_review`.
5. **Preserve provenance:** Record the original non-open citation in an audit log as `rejected_source_non_open_access`, but do not use it as active evidence.

## Page-level Verification Updates

After claim-level verification is complete, update the page-level summary fields so downstream readers can interpret the page without replaying the verification process. Set `verification_status` to reflect the aggregate outcome, update `verification_notes` with a brief summary of unresolved issues, and refresh `last_reviewed` and `verified_on` with the current ISO date.

Use page `status` for lifecycle state rather than claim truth. In general, pages that are usable but still contain unresolved issues should be marked `needs_review`; pages that are current and operational may be marked `active`; superseded pages should be marked `deprecated`.

## Minimal Verification Record

Each verified claim should leave a compact machine-readable record containing at least: `claim_id`, `citations_checked`, `outcome`, `contradiction_type` if any, `patch_action`, and `review_flag`.

## Verification Output Artifacts

Each verification run must produce:

- Updated page front matter.
- A claim verification table.
- A source accessibility table.
- A patch summary.
- A machine-readable audit log entry.
- A human-review queue for unresolved or high-impact claims.
