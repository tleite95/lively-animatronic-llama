# Top-Level Wiki Categories Reference

Use this file when you need category-level placement guidance beyond the one-sentence category table in the shared wiki specification. Treat this file as the detailed routing reference for top-level page placement. Do not use it to override page-type rules in the shared specification.

## General Placement Rules

Assign every page to exactly one primary top-level category. Choose the category by the page's canonical purpose, not by every topic it mentions. Prefer the category that makes the page easiest to retrieve, verify, and maintain over time.

Do not create duplicate canonical pages across categories. If a page legitimately touches multiple domains, place it in the category that owns its main function and link to related pages in other categories.

Use top-level category and `page_type` together. Let the top-level category determine organizational location and navigation context. Let `page_type` determine semantic role, expected content, and validation rules.

## Category Routing Reference

### `00-system`

Place pages here when they define the wiki system itself. Store mission, architecture, operating assumptions, agent roles, tool affordances, repository conventions, and cross-cutting implementation decisions here. Do not place domain-scientific content here unless it is necessary to explain the system's operation.

Use this category for pages such as system overviews, architecture notes, capability descriptions, repository conventions, prompt contracts, and cross-skill coordination rules. Avoid using it as a catch-all for anything foundational; if the content is scientific rather than system-defining, route it to the scientific category that owns it.

### `01-indices`

Place pages here when their main purpose is navigation rather than authority. Use this category for master indices, category indices, link hubs, and generated or curated listings that help agents and humans find canonical pages quickly.

Do not make an index page the sole home of substantive scientific claims. If an index needs short summaries, keep them brief and point to the canonical page that owns the content.

### `02-concepts`

Place pages here when the page defines a field-specific concept, term, or methodological idea used across computational toxicology. Use this category for concepts such as hazard, risk, exposure, read-across, IVIVE, adverse outcome pathway, benchmark dose, applicability domain, and weight of evidence.

Write these pages to capture toxicology-specific meaning, distinctions from nearby concepts, and operational importance in downstream reasoning. Do not spend space on generic background that a capable LLM already knows unless the toxicology-specific usage materially differs from common knowledge.

### `03-chemicals`

Place pages here when the page is centered on a chemical entity, mixture, metabolite, or chemical class. Use this category for pages that integrate identifiers, linked endpoints, assay evidence, mechanistic relevance, dataset coverage, and open questions about a substance.

Treat chemical pages as major synthesis hubs. Do not split the same chemical's canonical identity across multiple primary pages unless there is a strong need for separate metabolite, mixture, or class pages.

### `04-biology`

Place pages here when the page is centered on a biological entity or mechanistic biological context relevant to toxicology. Use this category for receptors, enzymes, pathways, tissues, cell systems, species, developmental stages, and other biological structures that mediate or condition toxic effects.

Use this category to connect observations to mechanism. Route pages here when the biology is the primary object of explanation rather than merely supporting a chemical or endpoint page.

### `05-toxicological-endpoints`

Place pages here when the page defines, scopes, or synthesizes a toxicological outcome, hazard class, or adverse effect category. Use this category for endpoints such as hepatotoxicity, carcinogenicity, endocrine disruption, developmental toxicity, genotoxicity, and nephrotoxicity.

Use endpoint pages to define what counts as evidence for the endpoint, how it is operationalized in assays or datasets, and what important interpretation limits apply. Do not bury endpoint definitions inside unrelated chemical or assay pages when the endpoint is likely to recur.

### `06-assays`

Place pages here when the page describes an assay, test system, in silico screen, or measurement framework. Use this category for experimental assays, computational assays, challenge tasks, panel assays, docking workflows used as assay-like evidence sources, and similar measurement systems.

Explain what the assay measures, how to interpret outputs, common artifacts, and what downstream claims the assay can and cannot support. Do not treat every model as an assay; if the page is mainly about a reusable analytical method, route it to models and methods instead.

### `07-datasets`

Place pages here when they document a data resource rather than a conclusion. Use this category for databases, benchmark collections, regulatory datasets, challenge datasets, curated tables, and public resource documentation. Artifacts created locally should **not** go here.

Describe provenance, scope, schema, inclusion criteria, access route, update cadence, missingness, and major caveats. Keep durable claims about the field or an entity on canonical pages elsewhere and link back to the dataset page for provenance.

### `08-models-and-methods`

Place pages here when the page is about an analytical method, computational model family, decision framework, or modeling workflow component. Use this category for QSAR, PBPK, QIVIVE, read-across methods, uncertainty analysis, benchmark dose modeling, feature engineering approaches, and evaluation frameworks.

Focus on assumptions, applicability domain, required inputs, outputs, strengths, limitations, and appropriate usage. Route a page here when the method itself is the durable object of knowledge, even if it is often applied within assays or workflows.

### `09-literature`

Place pages here when the page's primary role is to preserve source-level provenance. Use this category for papers, reviews, reports, guidance documents, and other source records that need structured metadata, source scope notes, extraction summaries, and links to canonical target pages.

Keep literature pages lightweight. Use them to preserve traceability, not to become the final resting place of normalized domain knowledge. Transfer durable concepts, evidence, and synthesis to canonical pages elsewhere and link back to the source record.

### `10-evidence`

Place pages here when the page is claim-centric and structured for verification, contradiction handling, or synthesis support. Use this category for evidence tables, extracted-claim pages, contradiction registers, comparison matrices, and other machine-operable evidence artifacts.

Prefer this category when fine-grained evidence structure matters more than narrative explanation. Do not force all evidence into prose pages when a structured record is more auditable and easier to compare.

### `11-workflows`

Place pages here when the page describes a repeatable procedure carried out by a human or agent. Use this category for literature review workflows, dataset profiling workflows, chemical assessment workflows, verification workflows, report-generation flows, and tool-usage sequences.

Write these pages as reusable operational procedures with decision points, prerequisites, expected outputs, and quality checks. Do not put durable scientific definitions here unless they are strictly needed to execute the workflow and are linked to their canonical pages.

### `12-agent-operations`

Place pages here when the page records the operational activity of the agentic system. Use this category for task logs, execution traces, tool-invocation records, repair records, audit logs, run summaries, and similar operational memory.

Treat this category as the system's audit layer. Keep it focused on what the system did, why it did it, and what changed. Do not mix long-form domain synthesis into operational records.

### `13-projects`

Place pages here when the page groups work around a bounded initiative rather than a reusable domain concept. Use this category for project briefs, workspaces, deliverable trackers, active investigation hubs, and project-specific collections of linked pages.

Use project pages to coordinate work across many page types without replacing canonical pages. Keep durable scientific content on canonical domain pages and let the project page link to it.

### `14-quality-and-governance`

Place pages here when the page defines rules, standards, review criteria, acceptable evidence, citation policy, risk controls, or responsible-use constraints. Use this category for quality gates, evidence standards, source policies, human review rules, and governance checklists.

Use this category to encode what the system is allowed to do and how quality is judged. Keep these pages stable and explicit because other pages and skills will depend on them.

### `15-glossary`

Place pages here when the page is meant for lightweight term lookup rather than full concept treatment. Use this category for short definitional stubs, alias pages, terminology indices, and minimal lookup-oriented entries that support retrieval.

Use the glossary to reduce friction, not to replace richer concept pages. If a term accumulates substantial domain-specific content, promote it to a canonical concept page and leave the glossary entry as a pointer.

## Cross-Category Decision Rules

If a page could plausibly fit multiple categories, choose the category that owns the page's primary maintenance burden. If the page will mainly accumulate identifiers and evidence about a substance, place it under chemicals even if it contains biology and endpoints. If the page will mainly accumulate definitions and distinctions, place it under concepts even if it cites many assay or model examples.

Prefer canonical domain categories over projects, indices, and workflows for durable scientific content. Prefer literature for source records, evidence for structured claim artifacts, and governance for rules. Use links aggressively rather than duplicating content across categories.

## Minimal Placement Test

Before finalizing placement, answer four questions.

1. What is the page's primary object of knowledge?
2. What kind of future updates will it likely accumulate?
3. Which page family should downstream agents query first for this information?
4. Which category minimizes duplication with existing canonical pages?

If the answers do not align, revise placement before writing.