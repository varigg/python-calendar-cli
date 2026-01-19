# Next Feature: Gmail Todo Workflow Automation (LLM-Driven)

**Created**: January 19, 2026
**Related Spec**: `specs/007-gmail-list-enhancements/spec.md`

## Purpose

Capture follow-on requirements discussed during spec 007 that are **out of scope** for Gmail list enhancements.
This next feature focuses on an LLM-driven workflow:

- Agent checks Gmail for messages labeled `!Todo`
- Agent extracts a todo item
- Agent transitions the email to `InProgress` and archives it (remove `INBOX`)
- Todo item stores a stable link back to the email

## Why This Is Out of Scope for Spec 007

Spec 007 is about **read-only listing improvements** (subject/title display, label filtering, pagination). The workflow discussed requires **write operations** (label modification / archiving) and new commands designed to reduce agent usage errors.

## Proposed User / Agent Workflow

1. List candidate emails:
   - “Show me the first 10 emails labeled `!Todo`.”
2. For each email:
   - Extract a todo description via LLM from subject/snippet/body.
   - Create a todo item containing a stable Gmail link.
3. Apply workflow transition:
   - Remove `!Todo`
   - Remove `INBOX` (archive)
   - Add `InProgress`

## Gmail Operations Needed (Not Yet Implemented)

Current client operations implemented today:

- `list_messages(query, limit)`
- `get_message(message_id, format_)`
- `delete_message(message_id)`

Additional operations required for the workflow:

### Label Discovery & Management

- List labels (name ↔ id mapping): `list_labels()`
- Lookup by name: `get_label_by_name(name)`
- Ensure label exists (create if missing): `ensure_label(name)` (or `create_label(name)` + logic)

### Message State Transitions

- Modify labels for a message (atomic add/remove):
  - `modify_message_labels(message_id, add_label_ids, remove_label_ids)`
- Optional for efficiency:
  - `batch_modify_message_labels(message_ids, add_label_ids, remove_label_ids)`

### Optional Convenience Operations

- Mark read (often used once “processed”): remove `UNREAD` label
- Bulk processing (start N items)

## Scope Decisions / Constraints

### Archiving Behavior

When moving `!Todo` → `InProgress`, the message should be **removed from Inbox**.
This means: remove the system `INBOX` label.

### OAuth Scopes

- Listing is compatible with read-only Gmail scope.
- Label modification / archiving requires Gmail **modify** scope.

## Stable Links Back to Gmail

Todo items should include a link that still works after archiving.

Recommendation:

- Prefer linking by `threadId` using the `#all/` view:
  - `https://mail.google.com/mail/u/0/#all/<threadId>`

Store both:

- `message_id` (for API calls)
- `thread_id` (for stable human link)

## UX / CLI Proposal: Single Workflow-Safe Command

To reduce agent usage errors, provide a single command or flag that encodes the exact workflow transition:

Example command:

- `gtool gmail todo start <message_id>`

Semantics:

- Remove `INBOX`
- Remove `!Todo`
- Add `InProgress`

Properties:

- Idempotent: running twice should not break state
- Clear failures: if Gmail modify scope is missing, return actionable guidance

## Output Format Proposal (Agent-Friendly)

Because the workflow is LLM-driven, outputs should be reliably machine-readable.

### Recommendation: Add `--format json` (or default JSON for agent mode)

#### `gtool gmail list` JSON shape

Return an object like:

- `query`: effective query used (after combining label + query)
- `count`: number requested
- `offset`: starting offset
- `messages`: list of message items

Each message item should include:

- `message_id`
- `thread_id`
- `subject`
- `from`
- `date`
- `snippet`
- `label_ids` or `label_names` (optional but helpful)
- `open_url` (computed, `#all/<threadId>`)

#### `gtool gmail todo start` JSON shape

Return an object like:

- `message_id`
- `thread_id`
- `archived`: true
- `removed_labels`: ["INBOX", "!Todo"] (names or ids)
- `added_labels`: ["InProgress"]
- `open_url`: `https://mail.google.com/mail/u/0/#all/<threadId>`

### Non-JSON / Human Output

Keep existing human-friendly output, but ensure:

- `--format json` disables colors and extra text
- JSON output is a single JSON object on stdout

## Open Questions

- Should `InProgress` be auto-created if missing, or fail unless user opts in?
- Should processing also mark messages as read (remove `UNREAD`)?
- Should we transition by message id or thread id (single email vs entire conversation)?

## “Implement Later” Prompt

Use this prompt later to implement the next feature:

"Implement an LLM-driven Gmail todo workflow in this repo.

Add Gmail client operations to support label discovery, label creation/ensuring, and message label modification:

- list_labels, get_label_by_name, ensure_label (or create_label)
- modify_message_labels (and optionally batch_modify_message_labels)

Add a new CLI command:

- `gtool gmail todo start <message_id>`
- It must remove labels: INBOX and !Todo
- It must add label: InProgress
- It must be idempotent
- It must require Gmail modify scope and produce a helpful error if only readonly is configured

Add stable Gmail links:

- Compute `open_url` using thread id: `https://mail.google.com/mail/u/0/#all/<threadId>`
- Ensure list and todo-start outputs include message_id + thread_id

Add agent-friendly output:

- Add `--format json` to `gtool gmail list` and `gtool gmail todo start`
- JSON output must be a single object to stdout, no color/no extra prose

Update tests:

- Unit tests for new GmailClient methods using mocked Gmail service
- CLI tests verifying correct add/remove label calls for todo-start

Constraints:

- Default list count remains 10
- Listing must not change message state"
