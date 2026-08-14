---
name: jsonl-to-rag
description: Review raw scientific JSONL artifacts and emit a cleaned RAG-ready JSONL stream for hybrid LightRAG/wiki ingestion without deploying anything.
---

# Scientific JSONL to RAG

Use this skill only on JSONL streams produced as a result of the `pdf2jsonl` Python script.

Do not read raw PDFs. Do not run PDF conversion unless an external orchestrator explicitly invokes `pdf2jsonl` first.

This skill implements the JSONL cleaning step for the paired agent. The agent owns the communication contract, allowed and prohibited behavior, validation guidelines, output schema, and final response format. This skill provides the procedural checklist and operational guardrails for carrying out that contract.

## Configuration

At runtime, the user will provide file paths to several input artifacts. Read them as part of the operation:

- Raw JSONL chunks
- Full text export
- Quarantined chunks
- Run logs
- QA Report
- Major changes during cleanup step

Additionally, two filepaths will be provided to which you should write output:

- `final_jsonl_path` for the RAG-ready JSONL stream you produce.
- `report_filepath` for the final preparation report.

The cleaned JSONL stream is the primary output passed to the next pipeline stage. The preparation report is the secondary output used only for auditing. All other referenced files are inputs.

Create configured report and log directories if missing.

## Operational guardrails

- Validate artifact fields and semantics, not parser implementation details.
- Use neighboring chunks for context recovery.
- If available, use Markdown/plaintext formatted full-text export for context recovery. 
- Never inspect raw PDFs.
- Never emit deployable wiki pages, final LightRAG entities, final graph relationships, production loader commands, or production writes.
- Keep all outputs traceable to source chunks.
- Mark uncertain records explicitly instead of forcing them into `ready` status.
- Preserve `ingestion_strategy` when valid, and use it only to retain context or settle toss-ups during JSONL cleaning.
- Remove unknown or invalid `ingestion_strategy` values from production-bound cleaned records and note the removal in the preparation report.
- Do not quarantine records merely because strategy metadata is missing, invalid, or unknown.
- Do not create semantic candidates, final claims, concept pages, cases, procedures, or glossary entries.

## Procedure

1. Load config and raw artifact paths.
2. Validate upstream gates.
3. Review chunk quality flags, boundaries, headings, pages, citations, and quarantine reasons.
4. Use machine-readable context to classify incomplete or over-pruned chunks.
5. Rescue quarantine records only when scientific meaning is recoverable from available artifacts.
6. Use `ingestion_strategy` metadata only to preserve context or settle toss-ups.
7. Merge neighboring chunks when sentence, paragraph, table caption, equation context, or section boundaries were split incorrectly.
8. Split chunks when a chunk clearly contains multiple unrelated sections or excessive concatenated material.
9. Lightly repair formatting, whitespace, line wrapping, broken hyphenation, encoding artifacts, and obvious OCR/PDF extraction artifacts.
10. Normalize headings, page/section metadata, document identifiers, citation candidates, chunk lineage fields, and valid strategy metadata.
11. Remove unknown or invalid strategy metadata from production-bound cleaned records and track removals for the report.
12. Route unresolved, unsupported, ambiguous, low-context, bibliography/reference, boilerplate, or low-information records to exclusion or human review.
13. Emit the cleaned JSONL stream to `final_jsonl_path`.
14. Validate cleaned outputs against the paired agent validation guidelines.
15. Write the preparation report to `report_filepath`.

## Boundary repair procedure

Use this procedure when reviewing candidate output chunks. Keep repairs source-faithful and minimal, but prioritize semantic boundary completeness over preserving original split points.

1. If a chunk starts mid-sentence, mid-paragraph, with a dangling pronoun, discourse connector, lowercase continuation, orphaned citation phrase, or detached table/caption/list continuation, first attempt to repair it with the immediately preceding chunk.
2. If a chunk ends mid-sentence, mid-paragraph, with an unfinished clause, open parenthesis, trailing comma/colon, unresolved citation-bearing claim, broken list item, or separated table/caption/equation context, first attempt to repair it with the immediately following chunk.
3. If a simple merge creates an oversized or semantically mixed chunk, move only the smallest complete unit needed to restore boundaries, such as a sentence, paragraph, caption, table row, list item, or equation explanation.
4. If several adjacent chunks were split at the wrong places, merge them temporarily and then split again at complete sentence, paragraph, section, table, caption, list, or equation-context boundaries.
5. Do not repair by inventing missing content, filling table cells, paraphrasing scientific claims, or using raw PDFs.
6. If boundary integrity cannot be restored from neighboring chunks or available machine-readable full-text context, route the record to exclusion or human review according to the paired agent contract.
7. Do not emit production-bound chunks with unresolved boundary flags such as `starts_lowercase`, `ends_incomplete`, `dangling_caption`, `split_table`, `orphaned_citation`, or equivalent flags unless the defect has been repaired and the flag updated or removed.

## Cleaning checklist

For each candidate output chunk:

- Confirm the text is nonempty and source-traceable.
- Confirm the chunk does not start or end partway through a sentence, paragraph, caption, table row, list item, equation explanation, citation-bearing claim, or thought stream when neighboring context or machine-readable full-text context can repair it.
- Confirm bibliography, reference-list, boilerplate, publisher-note, copyright, acknowledgments, conflict/funding disclosures, and orphaned citation debris are excluded.
- Confirm table repairs do not invent, reorder, or semantically alter data.
- Confirm md5 `text_hash` is generated from cleaned text.
- Confirm `rag_fitness_score` is rounded to two decimals on a 0 to 1 scale.
- Confirm status is one of the paired agent's recommended statuses.
- Confirm invalid or unknown strategy metadata is removed rather than used as a quarantine reason.
- Confirm human-review items are explicitly noted.

## Validation checklist

Require:

- Cleaned JSONL stream exists and is nonempty.
- Every cleaned record has source provenance.
- Every cleaned record has nonempty text.
- Every cleaned record has a stable ID.
- No production-bound cleaned record has an unresolved incomplete-boundary or contextless-chunk quality flag. Any exception must be marked for human review and excluded from `final_jsonl_path` according to the paired agent contract.
- The production-bound cleaned stream contains zero records that are primarily reference-list, bibliography, boilerplate, publisher-note, copyright, acknowledgments, conflict-of-interest disclosure, funding disclosure, DOI-list, URL-list, journal metadata, or orphaned citation debris.
- No raw-PDF-only dependency is introduced.
- Excluded chunks are accounted for with reasons in the preparation report.
- Unknown or invalid `ingestion_strategy` values removed from cleaned records are summarized in the preparation report.
- Human-review items are explicitly noted.
- Unresolved incomplete-boundary, contextless, reference/bibliography, boilerplate, and orphaned-citation records are not emitted to the production-bound cleaned stream.
