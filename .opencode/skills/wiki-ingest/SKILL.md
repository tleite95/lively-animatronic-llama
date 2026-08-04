---
name: wiki-ingest
description: Use this skill whenever you are analyzing a new source to be ingested into the wiki. 
---

## Usage
Use this skill when you have a JSONL stream of RAG chunks and need a citation-preserving, vetted report on what edits to make to the wiki

Do not use this skill:
- When you are reading the wiki
- To process plain text, meant to be inserted verbatim into the wiki
- When doing any kinf of wiki editing / creation of wiki pages

## Ingestion Strategies

Apply one of four abstract strategies. The strategies are speific to a specific by document type rather than a topic. The JSONL chunks will contain a `strategy` field containing a single-letter identifier corresponding to one of the following strategies. In this section, read only the relevant strategy and follow the directions in that section.

**Strategy A - Structural Decomposition** applies to textbooks. Because the source already has an author-imposed hierarchy of chapters and sections, ingestion should preserve that hierarchy as the wiki's own page structure rather than re-chunking arbitrarily, so that each wiki page corresponds to a coherent conceptual unit the textbook authors intended to stand alone. Definitions embedded in the text should be lifted into a lightweight glossary layer that other pages can reference, and figures or worked examples that illustrate a mechanism should be described narratively rather than reproduced, since the wiki's role is conceptual synthesis rather than verbatim reproduction.

**Strategy B - Argument-centric Extraction** For review and survey papers. Ingestion should follow an **argument-centric extraction** approach: rather than summarizing paper-by-paper in isolation, identify the review's central claims, the state of consensus versus open debate that the review describes, and the specific sub-topics it treats as settled versus contested, then represent these as claims attached to a wiki page for the relevant concept (e.g., "IVIVE," "read-across," "AOP"). **Do not write a page about the paper itself**. The purpose of this strategy is to keep the wiki organized by concept, which is what a downstream agent will actually query, rather than by citation (a single source can be cited across several pages).

**Strategy C - Mechanism or Case Extraction** For the primary/technical papers, ingestion should follow a **mechanism-or-case extraction** approach: rather than summarizing the full paper, the agent should extract the specific finding, method, dataset, or worked example the paper is known for (DeepTox's architecture and its Tox21 Challenge result; the Li et al. paper's specific ERα/ERβ binding findings for BPA and BPAF) and attach it to the relevant concept page as a concrete illustrative case, since the value of a primary source in this corpus is precision and specificity rather than breadth.

**Strategy D - Definitional/Procedural Extraction** applies to the guidance documents (AOP handbook, ECETOC read-across report, EPA benchmark dose guidance). These documents encode formal, regulator-sanctioned definitions and decision procedures that the agent will need to cite precisely and consistently, so ingestion should prioritize extracting the canonical definition of each term exactly as the issuing body states it, tagging it with its source and version, and building a short procedural summary of the associated workflow (for example, the sequence of steps a regulator expects in a read-across justification). Because these documents are periodically revised, each extracted definition should carry a document version and date so that later ingestion of an updated guidance document triggers a review rather than a silent overwrite.

## Summarization and Key-point Extraction
Summarization and key-point extraction should be guided by the redundancy-minimization principle: before writing a wiki page, the agent should first draft what a well-informed but non-specialist reader would already know about the topic, and then restrict the actual page content to what remains — field-specific terminology, quantitative conventions, the current methodological state of the art, and known limitations — so that pages stay dense with genuinely new information rather than restating general scientific background.

## Claim extraction

A claim is a specific, self-contained statement extracted from a source document that asserts a finding, conclusion, relationship, mechanism, comparison, limitation, or interpretation that could be evaluated against evidence in the paper or external literature. In claim extraction, a good claim should preserve the source's intended meaning, avoid unnecessary background detail, and be precise enough to verify, support, contradict, or cite.
- **Well-formatted claim statement**: The study found that participants receiving the intervention had significantly lower systolic blood pressure after 12 weeks than participants in the control group.
- **Poorly-formatted claim statement**: The intervention was good and seemed to help people a lot.
- **Not a claim statement**: Table 2 reports baseline demographic characteristics of the study participants.

For the full specification on how to format an extracted claim, see the [relevant section](@{REF}:/wiki/spec.md#claim-format) of the wiki spec.

## Citation
Citation should be handled uniformly regardless of source type: every extracted claim on a wiki page should carry an inline reference back to its originating source and, where practical, the specific section or figure, so that a downstream agent using the wiki can trace any assertion back to a citable original and so that later contradiction-checking has something concrete to compare.

For the full specification on citation formats, see the [relevant section](@{REF}:/wiki/spec.md#citation-format) of the wiki spec.

## Synthesis
Finally, synthesis across sources and pages should be treated as a distinct, higher-order ingestion pass performed after individual-source ingestion rather than during it: once several sources touching a shared concept have been ingested (for example, AOP framework papers, PBPK reviews, and IVIVE reviews all bearing on next-generation risk assessment), the agent should generate a small number of synthesis pages that explicitly integrate these separately-ingested pages into a higher-level narrative of how the sub-fields relate, explicitly citing the constituent pages rather than the original sources directly, so that the wiki accumulates original synthesis — Karpathy's and de Assis's original intent for this component — rather than remaining a collection of independent per-source summaries.

## Required Outputs of Ingestion
A completed ingestion pass should produce a structured handoff for downstream writing and verification. At minimum, the handoff should include the source citation metadata, the ingestion strategy used, a list of extracted atomic claims, the recommended target page for each claim, and a short note identifying whether each claim is novel, corroborating, qualifying, or potentially conflicting with existing wiki content.

For review papers and primary papers, the agent should still create at least a lightweight literature or source record containing the citation, source scope, and extraction notes, even when durable knowledge is routed to concept, assay, endpoint, or dataset pages. This preserves provenance without turning the wiki into a paper-by-paper summary archive.

## Ingestion Summary / Tasklist

When ingesting a source:

1. Identify source type, title, authors or organization, year, venue, DOI or URL, access status, retrieved date, and allowed-source status.
2. Create or update a `literature` page when the source needs provenance preservation.
3. Extract claims only if they are relevant to environmental chemistry, computational toxicology, evidence standards, datasets, assays, models, workflows, or endpoints.
4. Preserve source language enough to avoid scope drift, but do not copy large source passages.
5. Map extracted claims to target canonical pages and evidence records.
6. Create new canonical pages only when no suitable page exists.
7. Add open questions for ambiguous, incomplete, contradictory, or expert-dependent claims.
8. Return an ingestion summary with source metadata, target pages, extracted claims, skipped material, and review needs.