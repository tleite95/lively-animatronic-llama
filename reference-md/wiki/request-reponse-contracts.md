# Wiki Agent I/O Contracts

Use this reference for structured interaction between the wiki expert, other agents, and wiki skills.

## General Contract Rules

Every request must identify:

- `task_type`
- `requester`
- `objective`
- `inputs`
- `constraints`
- `expected_output`

Every response must identify:

- `task_type`
- `status`
- `actions_taken`
- `pages_read`
- `pages_created_or_updated`
- `claims_reviewed_or_changed`
- `sources_reviewed`
- `verification_status`
- `open_issues`
- `recommended_next_actions`

Use `not_applicable` for fields that do not apply. Do not omit failure, uncertainty, or access limitations.

## Status Values

Use one response-level status:

| Status | Meaning |
|---|---|
| `completed` | Requested wiki operation completed without blocking issues. |
| `completed_with_warnings` | Operation completed but has unresolved gaps, uncertainty, or minor failures. |
| `partial` | Some requested work completed, but one or more required parts remain unfinished. |
| `blocked` | Work could not proceed because required input, access, policy, or tool capability is missing. |
| `refused_out_of_scope` | Request or subrequest is outside wiki expert authorization. |
| `needs_human_review` | Automated work reached an expert-judgment or governance boundary. |

## Request Contract: `wiki_read_report`

```yaml
task_type: wiki_read_report
requester: string
objective: string
query: string
scope:
  page_ids: []
  categories: []
  page_types: []
  include_unverified: true
  include_conflicting: true
required_fields:
  - page_pointers
  - claim_ids
  - citation_ids
  - verification_status
expected_output: report
```

### Response

```yaml
task_type: wiki_read_report
status: completed | completed_with_warnings | partial | blocked
answer_summary: string
pages_read:
  - page_id: string
    title: string
    path_or_link: string
    page_type: string
    verification_status: string
supporting_claims:
  - claim_id: string
    statement: string
    verification_status: string
    confidence: string
    citation_ids: []
contradictions_or_caveats: []
gaps: []
recommended_next_actions: []
```

## Request Contract: `source_ingestion`

```yaml
task_type: source_ingestion
requester: string
objective: string
source_inputs:
  - source_ref: string
    source_type: paper | review | report | dataset | website | book | other
    supplied_content: full_text | abstract | metadata_only | unknown
constraints:
  allowed_source_required: true
  target_categories: []
  target_page_ids: []
expected_output: ingestion_summary
```

### Response

```yaml
task_type: source_ingestion
status: completed | completed_with_warnings | partial | blocked | needs_human_review
source_records:
  - citation_id: string
    literature_page_id: string
    access_status: string
    allowed_source: true | false | unknown
extracted_claims:
  - claim_id: string
    statement: string
    target_page_id: string
    qualifiers: {}
    citation_ids: []
pages_created_or_updated: []
skipped_material:
  - reason: string
open_questions: []
audit_record: string
recommended_next_actions: []
```

## Request Contract: `page_creation`

```yaml
task_type: page_creation
requester: string
objective: string
entity:
  name: string
  aliases: []
  proposed_page_type: string
  proposed_category: string
source_support:
  citation_ids: []
  source_refs: []
constraints:
  check_duplicates: true
  create_index_link: true
expected_output: page_creation_summary
```

### Response

```yaml
task_type: page_creation
status: completed | completed_with_warnings | partial | blocked
created_page:
  page_id: string
  title: string
  category: string
  page_type: string
  path_or_link: string
frontmatter_valid: true | false
duplicate_check: string
claims_added: []
citations_added: []
index_updates: []
verification_status: string
audit_record: string
open_issues: []
```

## Request Contract: `page_update`

```yaml
task_type: page_update
requester: string
objective: string
target_page_id: string
change_request: string
constraints:
  preserve_ids_and_slugs: true
  require_audit: auto
expected_output: update_summary
```

### Response

```yaml
task_type: page_update
status: completed | completed_with_warnings | partial | blocked | needs_human_review
target_page:
  page_id: string
  title: string
  path_or_link: string
sections_changed: []
claims_added: []
claims_revised: []
claims_removed: []
citations_added_or_repaired: []
links_added_or_repaired: []
verification_status: string
audit_record: string
open_issues: []
```

## Request Contract: `claim_verification`

```yaml
task_type: claim_verification
requester: string
objective: string
targets:
  page_ids: []
  claim_ids: []
constraints:
  use_allowed_sources_only: true
  update_page_summary: true
expected_output: verification_report
```

### Response

```yaml
task_type: claim_verification
status: completed | completed_with_warnings | partial | blocked | needs_human_review
claims_reviewed:
  - claim_id: string
    prior_status: string
    new_status: supported | unsupported | overstated | contradicted | source_inaccessible | needs_human_review
    confidence: low | medium | high
    citation_ids_reviewed: []
    notes: string
page_level_updates:
  - page_id: string
    verification_status: unverified | partially_verified | verified | source_access_failed | claim_mismatch | needs_human_review
contradictions_detected: []
audit_record: string
open_issues: []
```

## Request Contract: `contradiction_repair`

```yaml
task_type: contradiction_repair
requester: string
objective: string
targets:
  page_ids: []
  claim_ids: []
contradiction_context: string
constraints:
  preserve_supported_claims: true
  require_audit: true
expected_output: repair_summary
```

### Response

```yaml
task_type: contradiction_repair
status: completed | completed_with_warnings | partial | blocked | needs_human_review
contradictions:
  - claim_ids: []
    contradiction_type: true_contradiction | scope_mismatch | temporal_mismatch | granularity_mismatch | terminology_mismatch | uncertainty_mismatch
    resolution: repaired | narrowed | retained_with_note | escalated | unresolved
changes_made: []
claims_revised: []
claims_marked_review_needed: []
backup_or_audit_record: string
open_issues: []
```

## Request Contract: `index_maintenance`

```yaml
task_type: index_maintenance
requester: string
objective: string
scope:
  categories: []
  page_types: []
  target_index_page_ids: []
constraints:
  navigational_only: true
expected_output: index_update_summary
```

### Response

```yaml
task_type: index_maintenance
status: completed | completed_with_warnings | partial | blocked
indices_updated:
  - page_id: string
    links_added: []
    links_removed: []
    notes: string
canonical_pages_checked: []
open_issues: []
```

## Minimal Natural-Language Response Contract

When the requester does not need YAML, use this structure:

```md
## Wiki Operation Summary

### Status
completed | completed_with_warnings | partial | blocked | refused_out_of_scope | needs_human_review

### Answer or Actions Taken
...

### Pages and Claims
...

### Sources and Verification
...

### Open Issues
...

### Recommended Next Actions
...
```
