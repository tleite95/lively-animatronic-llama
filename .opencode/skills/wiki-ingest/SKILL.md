---
name: wiki-ingest
description: Use this skill whenever you are reading a new source to be ingested into the wiki. 
---

# Dependent Skill Execution Rule

> [!IMPORTANT]
> Execute this skill only if the seeded wiki already exists and the canonical in-wiki reference files are available at the expected relative paths.
> Before running this skill, confirm that the shared wiki specification is available at [reference-wiki-spec.md](../../../wiki/docs/00-system/reference-wiki-spec.md), the top-level category guidance is available at [top-level-wiki-categories-reference.md](../../../wiki/docs/00-system/top-level-wiki-categories-reference.md), and the page template examples are available at [wiki-page-template-examples-by-type.md](../../../wiki/docs/00-system/wiki-page-template-examples-by-type.md).
> Treat these files as pre-existing runtime references installed by initial wiki seeding.
> Do not run, invoke, recommend, or recreate `wiki-seed` from this skill.
> If any required reference file is unavailable, stop and report the missing prerequisite.

## Ingestion Strategies

Apply one of four abstract strategies depending on source structure, choosing the strategy by document type rather than by topic. If a specific ingestion strategy is directed by the user, use that regardless of its document type or structure.

**Strategy A - Structural Decomposition** applies to textbooks. Because the source already has an author-imposed hierarchy of chapters and sections, ingestion should preserve that hierarchy as the wiki's own page structure rather than re-chunking arbitrarily, so that each wiki page corresponds to a coherent conceptual unit the textbook authors intended to stand alone. Definitions embedded in the text should be lifted into a lightweight glossary layer that other pages can reference, and figures or worked examples that illustrate a mechanism should be described narratively rather than reproduced, since the wiki's role is conceptual synthesis rather than verbatim reproduction.

**Strategy B - Argument-centric Extraction** For review and survey papers. Ingestion should follow an **argument-centric extraction** approach: rather than summarizing paper-by-paper in isolation, identify the review's central claims, the state of consensus versus open debate that the review describes, and the specific sub-topics it treats as settled versus contested, then represent these as claims attached to a wiki page for the relevant concept (e.g., "IVIVE," "read-across," "AOP"). **Do not write a page about the paper itself**. The purpose of this strategy is to keep the wiki organized by concept, which is what a downstream agent will actually query, rather than by citation (a single source can be cited across several pages).

**Strategy C - Mechanism or Case Extraction** For the primary/technical papers, ingestion should follow a **mechanism-or-case extraction** approach: rather than summarizing the full paper, the agent should extract the specific finding, method, dataset, or worked example the paper is known for (DeepTox's architecture and its Tox21 Challenge result; the Li et al. paper's specific ERα/ERβ binding findings for BPA and BPAF) and attach it to the relevant concept page as a concrete illustrative case, since the value of a primary source in this corpus is precision and specificity rather than breadth.

**Strategy D - Definitional/Procedural Extraction** applies to the guidance documents (AOP handbook, ECETOC read-across report, EPA benchmark dose guidance). These documents encode formal, regulator-sanctioned definitions and decision procedures that the agent will need to cite precisely and consistently, so ingestion should prioritize extracting the canonical definition of each term exactly as the issuing body states it, tagging it with its source and version, and building a short procedural summary of the associated workflow (for example, the sequence of steps a regulator expects in a read-across justification). Because these documents are periodically revised, each extracted definition should carry a document version and date so that later ingestion of an updated guidance document triggers a review rather than a silent overwrite.

## Summarization and Key-point Extraction
Summarization and key-point extraction should be guided by the redundancy-minimization principle stated above: before writing a wiki page, the agent should first draft what a well-informed but non-specialist reader would already know about the topic, and then restrict the actual page content to what remains — field-specific terminology, quantitative conventions, the current methodological state of the art, and known limitations — so that pages stay dense with genuinely new information rather than restating general scientific background.

For the full specification on how to format an extracted claim, see the [relevant section](../../../wiki/docs/00-system/reference-wiki-spec.md#claim-format) of the wiki spec.

## Citation
Citation should be handled uniformly regardless of source type: every extracted claim on a wiki page should carry an inline reference back to its originating source and, where practical, the specific section or figure, so that a downstream agent using the wiki can trace any assertion back to a citable original and so that later contradiction-checking has something concrete to compare.

For the full specification on citation formats, see the [relevant section](../../../wiki/docs/00-system/reference-wiki-spec.md#citation-format) of the wiki spec.

## Synthesis
Finally, synthesis across sources and pages should be treated as a distinct, higher-order ingestion pass performed after individual-source ingestion rather than during it: once several sources touching a shared concept have been ingested (for example, AOP framework papers, PBPK reviews, and IVIVE reviews all bearing on next-generation risk assessment), the agent should generate a small number of synthesis pages that explicitly integrate these separately-ingested pages into a higher-level narrative of how the sub-fields relate, explicitly citing the constituent pages rather than the original sources directly, so that the wiki accumulates original synthesis — Karpathy's and de Assis's original intent for this component — rather than remaining a collection of independent per-source summaries.

## Required Outputs of Ingestion
A completed ingestion pass should produce a structured handoff for downstream writing and verification. At minimum, the handoff should include the source citation metadata, the ingestion strategy used, a list of extracted atomic claims, the recommended target page for each claim, and a short note identifying whether each claim is novel, corroborating, qualifying, or potentially conflicting with existing wiki content.

For review papers and primary papers, the agent should still create at least a lightweight literature or source record containing the citation, source scope, and extraction notes, even when durable knowledge is routed to concept, assay, endpoint, or dataset pages. This preserves provenance without turning the wiki into a paper-by-paper summary archive.

## Pre-write Cross-check
Before handing material to `wiki-write`, compare extracted claims against the most relevant canonical pages and record likely overlaps or conflicts. This is only a triage step: the ingestion pass should identify possible contradictions and scope mismatches, but final contradiction resolution belongs to verification or synthesis rather than ingestion.