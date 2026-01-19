# Data Model: Gmail List Enhancements

## Entity Definitions

### 1. EmailMessage

Represents a single email in the user's mailbox. Extended from existing Gmail API message metadata to include subject/title for list display.

**Fields**:

- `id` (str, required): Unique Gmail message identifier
- `threadId` (str, required): Gmail thread identifier
- `subject` (str, optional): Email subject line (extracted from headers)
  - **Default**: `"(No Subject)"` if blank or missing (FR-006)
  - **Validation**: Non-null string; may be empty string
  - **Display constraint**: Truncate/wrap to terminal width if >80 chars (FR-011)
  - **Character support**: Unicode, emoji, special characters (SC-006)
- `snippet` (str): Preview text from Gmail API (existing field)
- `labelIds` (List[str]): Gmail label identifiers applied to this message
  - **Example**: `["INBOX", "UNREAD", "CustomLabel"]`
  - **Constraint**: User-readable label names NOT provided by list API; must be mapped via separate label lookup if needed for display
- `internalDate` (int): Unix timestamp of email send time (from Gmail API)
- `from` (str, optional): Sender email address (extracted from headers if available)
- `date` (str): Formatted date string for display (derived from internalDate)

**Relationships**:

- References: `Label` (via `labelIds`)
- Ordering: Chronological by `internalDate`, newest first by default (FR-005)

**Constraints**:

- Read-only operation; no modifications allowed (FR-013)
- Subject lines must be displayable in terminal; truncate if >120 chars (FR-011)

---

### 2. Label

Represents a Gmail label (category/folder) for organizing emails.

**Fields**:

- `id` (str): Label identifier (e.g., `"INBOX"`, `"CustomLabel"`)
- `name` (str): Human-readable label name (e.g., `"Work"`, `"Personal"`)
- `type` (str): Label type (`"system"` or `"user"`)
  - **System labels**: `"INBOX"`, `"UNREAD"`, `"SENT"`, `"DRAFT"`, `"IMPORTANT"`, `"TRASH"`, `"SPAM"`, `"STARRED"`
  - **User labels**: Custom labels created by the user

**Validation**:

- Label names with special characters and spaces are supported (edge case in spec)
- Non-existent labels return helpful feedback (FR-008)

**Notes**:

- Not all labels need to be displayed; this entity is referenced for filtering and context only
- Filtering by label uses Gmail API `labelIds` parameter, NOT the search query syntax

---

### 3. ListParameters

Configuration for the Gmail list command. Encapsulates all user-provided parameters for message retrieval.

**Fields**:

- `query` (str, default: `""`): Gmail search query string (existing parameter)
  - **Examples**: `"is:unread"`, `"from:user@example.com"`, `"has:attachment"`
  - **Combined with label**: If both `query` and `label` provided, merged as `label:Work is:unread` (FR-014)
- `label` (str, optional, default: `None`): Single label filter for convenience
  - **Semantics**: Shorthand for `label:Work` in query syntax
  - **Behavior**: If specified, converted to `labelIds` parameter for Gmail API
  - **Default INBOX**: If neither `query` nor `label` specified, implicitly filters to INBOX (FR-012)
- `count` (int, default: `10`): Number of emails to return
  - **Constraint**: Non-negative integer (FR-007)
  - **Validation**: Must be >= 0 (0 is edge case; returns empty result)
  - **Mapping to API**: Maps to `maxResults` parameter in Gmail API
  - **Type**: Named `count` for CLI UX; maps to Gmail API `maxResults`
- `offset` (int, default: `0`): Starting position in result set (0-indexed)
  - **Constraint**: Non-negative integer (FR-007)
  - **Validation**: Must be >= 0
  - **Assumption**: Users understand 0-indexing (first email is position 0)
  - **Edge case**: If offset >= total_count, returns empty result with helpful message (FR-008)
  - **Mapping to API**: Implemented via multiple API calls with pagination tokens, not directly supported by Gmail API

**Validation Rules**:

- `count` must be non-negative integer (reject negative, non-integer values)
- `offset` must be non-negative integer (reject negative, non-integer values)
- If `offset` beyond total email count, return message: `"No more emails to display. Total emails: {total}, requested offset: {offset}"` (edge case in spec)
- `query` and `label` are independently optional but can be combined

**Semantics**:

- `label` parameter is UI convenience; internally converted to `label:LabelName` and merged with `query`
- Default behavior (no parameters): Show first 10 INBOX emails sorted newest-first
- Pagination is simulated client-side by fetching `count + offset` emails and slicing results (Gmail API does not support offset)

---

### 4. ListResult

Represents the result of a list operation (returned to CLI for formatting).

**Fields**:

- `messages` (List[EmailMessage]): Ordered list of email messages
- `totalCount` (int): Total number of emails matching the query/label filter
  - **Source**: `resultSizeEstimate` from Gmail API
- `offset` (int): Requested offset (for display in pagination info)
- `count` (int): Requested count (for display in pagination info)
- `hasMore` (bool): Whether additional results exist beyond this batch
  - **Derived**: `(offset + len(messages)) < totalCount`

**Display Info**:

- Pagination message format (FR-010): `"Showing {start}-{end} of {totalCount}"`
  - **Example**: `"Showing 20-29 of 150"`
  - **Edge case**: If no results, display `"No emails match your criteria."`

---

## State Transitions

**Email Message States**: None (read-only operation per FR-013). Messages are never modified during list operations.

**List Operation Flow**:

1. User provides `ListParameters` (query, label, count, offset)
2. System converts `label` to query syntax if provided (FR-014)
3. System validates `count` and `offset` (FR-007)
4. Gmail API call executes with merged query and `maxResults` parameter
5. System fetches enough results to satisfy `offset + count` requirement
6. System slices results by `offset` and `count` to create `ListResult`
7. CLI formats `ListResult` with subjects, labels, dates, and pagination info (FR-001, FR-010)

---

## Validation Rules Summary

| Field     | Constraint                          | Error Message                                                                                    |
| --------- | ----------------------------------- | ------------------------------------------------------------------------------------------------ |
| `count`   | >= 0, integer                       | `"Count must be a non-negative integer. Got: {value}"`                                           |
| `offset`  | >= 0, integer                       | `"Offset must be a non-negative integer. Got: {value}"`                                          |
| `label`   | Non-empty string, valid Gmail label | `"Label '{label}' not found or not accessible. Run 'gtool gmail list' to see available labels."` |
| `query`   | Valid Gmail search syntax           | `"Invalid Gmail search query: {query}. See Gmail search operators for valid syntax."`            |
| `subject` | Non-null string (may be empty)      | Display as `"(No Subject)"` if blank                                                             |

---

## API Type Definitions (Python)

```python
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class EmailMessage:
    id: str
    threadId: str
    subject: str  # "(No Subject)" if blank
    snippet: str
    labelIds: List[str]
    internalDate: int
    from_: Optional[str] = None
    date: Optional[str] = None

@dataclass
class Label:
    id: str
    name: str
    type: str  # "system" or "user"

@dataclass
class ListParameters:
    query: str = ""
    label: Optional[str] = None
    count: int = 10
    offset: int = 0

@dataclass
class ListResult:
    messages: List[EmailMessage]
    totalCount: int
    offset: int
    count: int
    hasMore: bool
```

---

## Key Design Decisions

1. **Label Parameter as Convenience**: The `--label` flag is separate from `--query` for CLI usability, but internally converted to query syntax for Gmail API consistency.

2. **Client-Side Pagination**: Gmail API does not support offset; we implement pagination by fetching excess results and slicing client-side. This is reasonable for UI use cases (typical pagination is 10-50 items).

3. **Subject Extraction**: Subjects are extracted from message headers during the list call. This requires fetching `headers` format or mapping from full message metadata, not just the snippet.

4. **Default INBOX**: When no label/query specified, implicitly add `label:INBOX` filter for expected Gmail behavior (not all user labels by default).

5. **No Label Display Mapping**: List results include `labelIds` (technical IDs), not user-readable label names. Mapping to names would require additional API calls; deferred to future enhancement.
