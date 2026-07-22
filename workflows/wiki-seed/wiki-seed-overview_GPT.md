# Wiki Seeding Guide for Agentic Computational Toxicology

This high-level overview is the short operating guide for agents seeding the computational toxicology wiki. Use it first, and open the detailed outline only when exact page lists, Docusaurus conventions, or completion checks are required.

Detailed reference: [wiki-seed-outline_GPT.md](wiki-seed-outline_GPT.md).

---

# High-Level Overview for Agents

## 1. Mission

Your task is to seed a Docusaurus-compatible LLM research wiki with enough field-specific computational toxicology knowledge to support retrieval, routing, early synthesis, relevance judgment, and future autonomous workflows. The wiki should help an agent understand toxicological literature, decide whether newly encountered information is pertinent, and place that information into the correct page, index, workflow, or evidence structure.

Do **not** use this document as a source-ingestion procedure. If you are ingesting sources, use the dedicated ingestion skill or ingestion workflow. This document tells you **what to seed, where it belongs, and how complete it must be**.

For exact objectives and scope, see [D1. Seeding Objective and Scope](wiki-seed-outline_GPT.md#d1-seeding-objective-and-scope). For the source-ingestion boundary, see [D4. What to Defer](wiki-seed-outline_GPT.md#d4-what-to-defer).

## 2. Agent Execution Contract

When seeding the wiki, act in this order. First, create or verify the Docusaurus folder structure and category files. Second, create the required index and governance pages. Third, seed the core interpretive concepts, methods, datasets, assays, endpoints, biology pages, workflows, and sentinel chemicals. Fourth, cross-link pages so that multi-hop retrieval works. Fifth, validate the build and run completion checks.

When deciding what to write, prefer concise, field-specific content over broad textbook exposition. A page is useful when it captures toxicology-specific usage, interpretation constraints, applicability limits, evidence caveats, regulatory or computational relevance, and links to related entities. A page is not useful if it only repeats generic knowledge that a capable model already knows.

For detailed page creation requirements, see [D5. Page Creation and Update Rules](wiki-seed-outline_GPT.md#d5-page-creation-and-update-rules). For the completion gate, see [D14. Completion Checklist](wiki-seed-outline_GPT.md#d14-completion-checklist).

## 3. Progressive Disclosure Rule

Use the smallest part of this document that is sufficient for the current task. If you are planning the seed, use this overview plus [D2. Seeding Priorities](wiki-seed-outline_GPT.md#d2-seeding-priorities). If you are creating files, use [D6. Docusaurus Structure and Logistics](wiki-seed-outline_GPT.md#d6-docusaurus-structure-and-logistics). If you are deciding whether a page belongs in the first build, use [D3. What to Seed First](wiki-seed-outline_GPT.md#d3-what-to-seed-first) and [D11. Initial Minimum Viable Wiki Build](wiki-seed-outline_GPT.md#d11-initial-minimum-viable-wiki-build). If you are checking whether seeding is done, use [D14. Completion Checklist](wiki-seed-outline_GPT.md#d14-completion-checklist).

Do not load or reason over every page list unless the current step requires exact filenames or coverage verification.

## 4. Seeding Priorities

Seed in this priority order unless a project-specific need overrides it.

1. Cross-cutting concepts that control interpretation across toxicology.
2. Core methods and frameworks used repeatedly by computational toxicology workflows.
3. Major datasets, assay families, and evidence resources.
4. A small set of sentinel chemicals and endpoints that exercise the full workflow.
5. Governance, quality, and workflow pages needed for reliable operation.
6. Additional breadth only after the above layers support navigation, synthesis, and verification.

The detailed priority rationale is in [D2. Seeding Priorities](wiki-seed-outline_GPT.md#d2-seeding-priorities). The exact first-build page list is in [D11. Initial Minimum Viable Wiki Build](wiki-seed-outline_GPT.md#d11-initial-minimum-viable-wiki-build).

## 5. What Counts as Good Seed Content

Good seed content is short, precise, linked, and operational. It should explain how a concept, method, assay, endpoint, dataset, chemical, or workflow is used in computational toxicology. It should include scope boundaries, common confusions, interpretation caveats, and links to neighboring pages.

Every seeded canonical page should have valid front matter, a clear scope, a short overview, at least one useful toxicology-specific definition or claim, at least one citation path when a claim depends on factual support, and links to the most relevant related pages. If coverage is partial, leave an explicit review note.

For the minimum page standard, see [D5.5 Minimal Completion Standard](wiki-seed-outline_GPT.md#d55-minimal-completion-standard-for-a-seeded-page).

## 6. Redundancy-Minimization Rule

Before creating or expanding a page, ask: “What would a strong model already know, and what does it not reliably know without a curated computational toxicology reference?” Seed the second category. Avoid generic background on molecules, cells, statistics, or biology unless the page explains computational toxicology-specific usage, edge cases, regulatory interpretation, model limitations, dataset conventions, or evidence-integration concerns.

For the full rule, see [D5.2 Redundancy-Minimization Rule](wiki-seed-outline_GPT.md#d52-redundancy-minimization-rule).

## 7. Citation, Evidence, and Contradiction Rule

Substantive scientific claims should be cited or routed to a source or evidence page that can support later verification. Do not bury evidence-bearing claims only in prose. If a topic has conflicting findings, preserve the contradiction rather than resolving it prematurely. Create or update an evidence claim page, contradiction register entry, or review note when needed.

For citation and provenance expectations, see [D14.4 Citation and Provenance Readiness](wiki-seed-outline_GPT.md#d144-citation-and-provenance-readiness). For evidence pages, see [D7.9 Evidence Pages](wiki-seed-outline_GPT.md#d79-evidence-pages).

## 8. Cross-Linking Rule

Each canonical page should link to the most relevant neighboring pages in at least one other top-level category. Concepts should link to relevant methods, assays, datasets, endpoints, workflows, or chemicals. Chemical pages should link to relevant endpoints, assays, datasets, biology, and evidence pages. Endpoint pages should link to relevant assays, biology, chemicals, and evidence types.

The goal is not to link every mention. The goal is to support meaningful multi-hop retrieval.

For detailed linking rules, see [D5.4 Cross-Linking Rules](wiki-seed-outline_GPT.md#d54-cross-linking-rules).

## 9. Docusaurus Rule

The wiki must be implemented under `./wiki/docs/` using lowercase kebab-case folders and filenames, Markdown or MDX pages, `_category_.json` files, stable front matter, relative links, and Mermaid support for diagrams. Treat `10-evidence` as the canonical evidence folder name. If older notes refer to `10_evidence`, normalize to `10-evidence`.

For exact layout and build validation, see [D6. Docusaurus Structure and Logistics](wiki-seed-outline_GPT.md#d6-docusaurus-structure-and-logistics).

## 10. When to Stop the Initial Seed

Stop the first seed when the wiki has a coherent, cross-linked spine across concepts, methods, datasets, assays, endpoints, biology, workflows, governance, and sentinel chemicals. The seeded corpus should materially improve technical definition lookup and relevance judgment while minimizing redundancy with general model knowledge. It should be ready for incremental expansion, verification, contradiction checking, and synthesis without structural rework.

For formal stop conditions, see [D14.9 Completion Gate](wiki-seed-outline_GPT.md#d149-completion-gate).

---
