# Toxicology Wiki Authoring Rules

Use this reference when creating, editing, or verifying environmental chemistry and computational toxicology wiki content.

## Domain Claim Scoping

Toxicological claims are always rooted in a specific context. Without this context, the claim is far less useful in practice. Therefore, every substantive toxicology claim should preserve relevant qualifiers. Add only qualifiers supported by the source.

### Common Qualifiers

| Qualifier | Use when relevant |
|---|---|
| `species` | Human, rat, mouse, zebrafish, invertebrate, bacterial strain, or other organism. |
| `strain_or_line` | Laboratory strain, cell line, engineered cell system, or assay-specific biological system. |
| `sex` | Male, female, mixed, not reported, or sex-nonspecific result. |
| `life_stage` | Embryonic, fetal, neonatal, juvenile, adult, developmental window, or reproductive stage. |
| `route` | Oral, inhalation, dermal, injection, dietary, waterborne, in vitro exposure, environmental exposure, or modeled route. |
| `dose_or_concentration` | Dose, concentration, range, units, nominal vs measured concentration, or exposure category. |
| `duration` | Acute, subchronic, chronic, time point, repeated exposure, or recovery period. |
| `tissue_or_target` | Tissue, organ, receptor, pathway, enzyme, cellular compartment, or endpoint-specific target. |
| `assay_system` | In vivo, in vitro, ex vivo, in silico, high-throughput screen, omics assay, or dataset-derived analysis. |
| `endpoint` | Toxicological outcome or adverse effect being assessed. |
| `model_or_method` | QSAR, read-across, PBPK/PBK, IVIVE/QIVIVE, docking, ML model, statistical model, or weight-of-evidence method. |
| `dataset_version` | Dataset release, snapshot date, curation version, or benchmark split. |
| `uncertainty` | Confidence limits, statistical significance, qualitative uncertainty, conflicting evidence, or source caveat. |

If a qualifier materially affects interpretation and the source does not report it, state `not reported` or add an open question instead of guessing.

## Claim Type Guidance

The following is a list of claim types and a non-exhaustive list of examples of when to use each one

- `definition` for scoped definitions of terms, endpoints, methods, or assay concepts.
- `fact` for stable entity properties such as identifiers, page relationships, dataset provenance, or source metadata.
- `identifier` for CAS numbers, PubChem CIDs, InChIKeys, assay IDs, dataset accession IDs, and regulatory identifiers.
- `method` for procedural or model claims about how an assay, model, workflow, or analysis operates.
- `result` for observed experimental results, dataset records, model outputs, and extracted source findings.
- `interpretation` for source-grounded synthesis, mechanism inference, hazard relevance, or weight-of-evidence statements.
- `workflow_assertion` for operational statements inside workflow or governance pages.
- `summary` only when a claim intentionally summarizes multiple cited claims and points to evidence-bearing records.

## Evidence Stream Distinctions

Do not merge these evidence streams without preserving labels and scope:

- Human epidemiological evidence.
- In vivo animal toxicology.
- In vitro bioactivity or mechanistic assays.
- High-throughput screening results.
- Omics or biomarker evidence.
- Environmental monitoring or exposure data.
- Chemical fate, transport, persistence, and transformation data.
- In silico predictions.
- Read-across or category-based inference.
- PBPK/PBK or IVIVE/QIVIVE modeling.
- Regulatory classifications or guideline interpretations.
- Narrative review conclusions.

When synthesizing across streams, state which streams support which conclusion and which remain uncertain.

## Overstatement Patterns to Avoid

Mark or repair a claim as `overstated` when it:

- Converts in vitro activity into in vivo hazard without bridging evidence.
- Converts association into causation without adequate support.
- Converts model prediction into observed toxicity.
- Treats one species, tissue, sex, life stage, route, dose, or time point as universal.
- Treats screening hit calls as definitive endpoint evidence.
- Ignores cytotoxicity, solubility, assay interference, metabolism, or exposure relevance.
- Treats absence from a dataset as evidence of no hazard.
- Treats a review's broad statement as if it directly supports a narrower mechanistic claim not documented in that review.
- Treats a regulatory classification as a mechanistic finding.
- Treats a chemical class property as true for every member without member-specific evidence.

## Environmental Chemistry Specific Rules

For chemical fate, transport, exposure, and environmental chemistry pages:

- Distinguish parent compounds, metabolites, degradation products, impurities, mixtures, and commercial formulations.
- Preserve medium and matrix: air, water, soil, sediment, dust, food, biota, wastewater, or biological sample.
- Preserve measured vs modeled values.
- Preserve environmental conditions when relevant: pH, temperature, salinity, organic carbon, light exposure, microbial context, and redox conditions.
- Do not generalize persistence, bioaccumulation, partitioning, or transformation across media without support.
- Link chemical pages to datasets and evidence pages rather than embedding large raw data tables.

## Computational Toxicology Specific Rules

For models, methods, datasets, and in silico results:

- State inputs, outputs, applicability domain, validation setting, endpoint definition, and training or reference data when known.
- Distinguish training performance, internal validation, external validation, and prospective performance.
- Preserve dataset version, curation rules, split strategy, endpoint labels, and missingness caveats when available.
- Do not treat a model score as a biological observation.
- Do not treat out-of-domain predictions as reliable without explicit support.
- Do not compare model outputs from different label definitions without noting the mismatch.
- Link to model and dataset pages for method and provenance details.

## Assay Interpretation Rules

For assay pages and assay-derived claims:

- State what signal is measured and what endpoint or mechanism it is intended to inform.
- Preserve assay format, biological system, readout, concentration range, and hit-calling or activity threshold when available.
- Record known artifacts and confounders such as cytotoxicity, autofluorescence, solubility limits, volatility, metabolic competence, and assay interference.
- Do not infer apical toxicity from assay activity unless the source provides a supported bridge.
- Use `agent_access` metadata on assay pages when operational routing depends on whether results are available, restricted, human-only, or executable.

## Endpoint Authoring Rules

Endpoint pages should define:

- What counts as evidence for the endpoint.
- Common assays, biomarkers, and evidence streams.
- Major subclasses or related endpoints.
- Interpretation limits and common scope mismatches.
- Links to chemicals, biological mechanisms, assays, datasets, models, and workflows.

Do not bury reusable endpoint definitions inside chemical, literature, or project pages.

## Chemical Page Authoring Rules

Chemical pages should function as synthesis hubs.

Include when available and relevant:

- Canonical name and aliases.
- CAS RN, PubChem CID, InChIKey, SMILES, DTXSID, or other stable identifiers.
- Parent/metabolite/mixture/class scope.
- Linked endpoints and assays.
- Mechanistic relevance.
- Dataset coverage.
- Evidence pages and literature pages.
- Contradictions, caveats, and open questions.

Do not make a chemical page the only location for source-level evidence or detailed evidence tables. Link out to evidence and literature pages.

## Literature Page Authoring Rules

Literature pages preserve source provenance.

They should include:

- Citation metadata.
- Access status.
- Scope and source notes.
- Extracted key claims or pointers.
- Target pages receiving normalized content.
- Open questions or limitations.

Do not let durable domain knowledge remain only on a literature page. Normalize it to canonical pages or evidence records when useful.

## Evidence Page Authoring Rules

Use evidence pages when:

- Multiple claims or sources need comparison.
- A contradiction register is needed.
- Machine-operable evidence structure is more useful than prose.
- Verification, synthesis, or future updates depend on fine-grained records.

Evidence pages should preserve claim, source, qualifiers, outcome, verification status, contradiction type, synthesis notes, and related pages.

## Required Escalations

Mark `needs_human_review` when any of the following apply:

- Evidence conflict cannot be resolved by scope or source type.
- Claim affects regulatory, clinical, public-health, environmental safety, or risk-management interpretation.
- Source language is ambiguous or requires expert domain judgment.
- The source is inaccessible but central to a high-impact claim.
- The operation would remove substantial cited scientific content.
- Model or dataset limitations materially affect downstream decisions.
- The page contains possible source misuse, citation laundering, circular support, or unsupported synthesis.

## Minimal Toxicology Claim Checklist

Before accepting a claim, verify:

- The claim is atomic.
- The source supports the claim as written.
- Material qualifiers are present.
- The evidence stream is identified.
- The claim type is correct.
- Citations are resolvable and allowed.
- Verification status matches the evidence.
- Related canonical pages are linked where useful.
- Open questions are recorded instead of guessed.
