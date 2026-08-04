# Wiki Agent Operating Workflows

Use these workflows as operational procedures. Descriptions of workflow steps are also present in skill definitions. These offer that information more explicitly and in the format of checklists. Use them when the skill alone does not provide enough definition to complete a task to a satisfactory level, or when a task is complex enough that a more fine-grained todo list is required.

Apply [`spec.md`](@{REF}:/wiki/spec.md), [`top-level-categories.md`](@{REF}:/wiki/top-level-categories.md), and [`page-templates-examples.md`](@{REF}:/wiki/page-templates-examples.md) during every write, ingest, verify, and repair operation.

## Workflow: Read and Report

### Preconditions

- A query, page ID, entity name, claim family, or task objective is provided.
- The requester expects a wiki-grounded answer, not external research.

### Procedure

1. Search for exact page IDs, titles, aliases, and canonical pages.
2. Search relevant indices only to locate canonical pages.
3. Read canonical pages, evidence pages, literature pages, and governance pages needed for the answer.
4. Extract claim IDs, statements, citations, qualifiers, and verification statuses.
5. Separate supported content, unverified content, contradictions, and open questions.
6. Return a concise report with page pointers and claim-level support.

### Quality Checks

- The answer identifies whether the wiki content is verified, partially verified, unverified, or conflicting.
- The answer does not treat index pages as scientific authority.
- All material assertions in the report are traceable to wiki pages or reported as gaps.

## Workflow: Source Ingestion

### Preconditions

- Source content and metadata is supplied as a JSONL stream.
- Source access is allowed or access status can be recorded.
- The source is relevant to the wiki's toxicology or environmental-chemistry scope.

### Procedure

1. Capture citation metadata using the citation schema in [`spec.md`](@{REF}:/wiki/spec.md).
2. Determine whether a literature page already exists.
3. Create or update a `literature` page for source-level provenance when needed.
4. Extract relevant claims as atomic statements.
5. Preserve qualifiers from the source: species, assay system, model, dose, route, duration, endpoint, exposure setting, tissue, and uncertainty.
6. Map each extracted claim to one or more target canonical pages or evidence records.
7. Create target pages only when no suitable canonical page exists.
8. Add evidence records when fine-grained claim comparison or contradiction tracking is needed.
9. Add open questions for ambiguous, unsupported, inaccessible, or expert-dependent material.
10. Create an audit record if the ingestion changes canonical pages or verification state.

### Quality Checks

- Source metadata is complete enough for resolution.
- Extracted claims do not exceed the source's scope.
- Durable knowledge is mapped out of literature notes to canonical or evidence pages.
- Skipped material and access limitations are reported.

## Workflow: New Page Creation

### Preconditions

- The entity, concept, source, dataset, assay, endpoint, method, workflow, or operation record does not already have an adequate canonical page.
- Page category and `page_type` can be assigned.

### Procedure

1. Search for existing pages by exact name, aliases, abbreviations, identifiers, and likely synonyms.
2. Choose the page's primary object of knowledge.
3. Assign exactly one top-level category using [`top-level-categories.md`](@{REF}:/wiki/top-level-categories.md).
4. Assign an approved `page_type` using [`spec.md`](@{REF}:/wiki/spec.md).
5. Select the smallest useful template from [`page-templates-examples.md`](@{REF}:/wiki/page-templates-examples.md).
6. Generate stable `id`, filename, slug, title, sidebar label, description, aliases, status, last reviewed date, and verification status.
7. Add only cited, substantive claims.
8. Add related pages and index links where useful.
9. Set page-level `verification_status` to `unverified` unless complete verification has occurred.
10. Write the page and run a compliance check.
11. Create an audit record if the page is canonical, evidence-bearing, or operation-critical.

### Quality Checks

- Required frontmatter fields exist and use valid values.
- File and slug use stable lowercase kebab-case.
- Page structure follows expected section order.
- No duplicate canonical page exists.
- Substantive claims have citations or are explicitly marked as open questions.

## Workflow: Page Update

### Preconditions

- A target page exists.
- The requested change is within wiki scope.

### Procedure

1. Read the full target page and relevant linked pages.
2. Identify affected sections, claims, citations, links, and metadata.
3. Preserve stable identifiers, slugs, and supported claims.
4. Normalize unsupported prose into claim records when needed.
5. Repair structure, citations, links, qualifiers, and related pages.
6. Move misplaced content to the correct canonical page when appropriate.
7. Update review and verification metadata only when justified.
8. Create an audit record for substantive changes.
9. Return an update summary.

### Quality Checks

- No supported claim is silently removed.
- Claims are no broader than their evidence.
- Related pages link to canonical targets.
- Major changes are auditable.

## Workflow: Claim Verification

### Preconditions

- Target claims and citations are identifiable.
- Source access status can be determined.

### Procedure

1. Read target claims and cited source records.
2. Access allowed source content through available wiki-supported routes.
3. Compare each claim's statement, subject, predicate, object, qualifiers, and implied scope with the source.
4. Assign one claim-level verification status.
5. Add confidence and notes if useful.
6. Mark claims `source_inaccessible` when source access fails.
7. Mark claims `needs_human_review` when automated verification cannot safely resolve the issue.
8. Update page-level verification summary only after reviewing the relevant claim set.
9. Record audit information for verification changes.

### Quality Checks

- Verification is based on inspected allowed sources, **not memory**.
- Claim-level statuses use the approved status vocabulary.
- Page-level status is consistent with claim-level results.
- Contradiction checking is not run on unverified raw claims.

## Workflow: Contradiction Detection and Repair

### Preconditions

- Competing claims have claim-level verification statuses.
- Relevant sources or evidence pages are accessible or access failures are recorded.

### Procedure

1. Identify the conflicting claim set.
2. Compare scope qualifiers before treating claims as incompatible.
3. Classify the contradiction type:
   - `true_contradiction`
   - `scope_mismatch`
   - `temporal_mismatch`
   - `granularity_mismatch`
   - `terminology_mismatch`
   - `uncertainty_mismatch`
   - `no_actual_contradiction`
4. Prefer narrowing or qualifying claims over deleting them.
5. Preserve supported evidence streams with explicit scope.
6. Update affected canonical and evidence pages.
7. Mark unresolved or high-impact conflicts `needs_human_review`.
8. Create an audit record.

### Quality Checks

- Claims are not called contradictory when they differ only in species, assay, dose, route, time, endpoint, model, or dataset version.
- Supported claims are retained with narrower wording when possible.
- The repair does not erase provenance.

## Workflow: Index Maintenance

### Preconditions

- A canonical page was created, moved, deprecated, or discovered to be missing from navigation.
- The relevant index page exists or should be created.

### Procedure

1. Identify the canonical page's category and page type.
2. Locate the relevant index page.
3. Add, update, or remove navigational links.
4. Keep summaries brief and non-authoritative.
5. Avoid duplicating scientific claims.
6. Verify that links are relative and stable.

### Quality Checks

- Index entries point to canonical pages.
- Index prose is navigational only.
- No index page becomes the sole source for a scientific assertion.

## Workflow: Operation Audit

### Preconditions

- A substantive operation occurred or failed in a way that affects trust, provenance, or future work.

### Procedure

1. Create or update an `agent_operation` page.
2. Record triggering request, target pages, source inputs, tools used, and dependencies.
3. Record actions taken and pages changed.
4. List affected claim IDs and citation IDs.
5. Record verification outcomes, warnings, failures, and human review needs.
6. Link to created or updated pages.

### Quality Checks

- The audit record is factual and operational.
- It does not introduce new scientific synthesis.
- It enables a later agent or human to understand what changed and why.
