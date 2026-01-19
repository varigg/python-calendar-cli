# API Contracts: Gmail List Enhancements

## Module: `src/gtool/clients/gmail.py`

### Method: `GmailClient.list_messages()`

**Existing Signature** (current implementation):

```python
def list_messages(
    self,
    query: str = "",
    limit: int = 10,
    max_results: int = None
) -> List[dict]:
    """List Gmail messages matching a query.

    Args:
        query: Gmail search query (default: all messages).
        limit: Maximum number of messages to return (new parameter).
        max_results: Maximum number of messages to return (old parameter, for compatibility).

    Returns:
        List of message dictionaries with id, threadId, snippet, labelIds, etc.
    """
```

**Enhanced Signature** (after implementation):

```python
def list_messages(
    self,
    query: str = "",
    label: Optional[str] = None,
    count: int = 10,
    offset: int = 0,
    limit: int = None,
    max_results: int = None
) -> List[dict]:
    """List Gmail messages with pagination and label filtering.

    Retrieves email messages from the user's mailbox, with support for:
    - Filtering by label or Gmail search query
    - Pagination via count (number of results) and offset (starting position)
    - Combining label and query parameters

    The query parameter supports Gmail's native search syntax:
    - "is:unread" - unread messages
    - "from:user@example.com" - messages from specific sender
    - "has:attachment" - messages with attachments
    - "label:Work" - messages with Work label

    If both label and query are provided, they are combined:
    - label="Work" + query="is:unread" → "label:Work is:unread"

    If neither label nor query provided, defaults to INBOX:
    - Implicit filter: "label:INBOX"

    Pagination is implemented client-side:
    - Fetches (count + offset) messages from Gmail API
    - Slices to [offset:offset+count] before returning
    - Note: Gmail API does not support offset natively

    Args:
        query: Gmail search query (default: ""). Supports Gmail syntax operators.
        label: Single label filter for convenience (default: None).
               If provided, converted to 'label:LabelName' in query.
               Example: label="Work" becomes part of Gmail query.
        count: Number of messages to return (default: 10).
               Must be non-negative integer. Maps to 'limit' in API terms.
               Validation: count >= 0 (reject negative).
        offset: Starting position in result set, 0-indexed (default: 0).
                Must be non-negative integer.
                Validation: offset >= 0 (reject negative).
        limit: (Deprecated) Alias for count for backward compatibility.
        max_results: (Deprecated) Legacy parameter name for count.

    Returns:
        List[dict]: Email message dictionaries with fields:
        - 'id' (str): Gmail message ID
        - 'threadId' (str): Gmail thread ID
        - 'snippet' (str): Message preview text
        - 'labelIds' (List[str]): List of label IDs applied to message
        - 'internalDate' (int): Unix timestamp of message send time
        Additional fields may include: 'headers' (dict) with 'Subject', 'From', etc.

    Raises:
        CLIError: If Gmail scope missing, authentication fails, validation fails, or API call fails.
        ValueError: If count or offset is negative or non-integer.

    Examples:
        # List first 10 unread emails
        messages = client.list_messages(query="is:unread", count=10, offset=0)

        # List emails from Work label, offset by 20
        messages = client.list_messages(label="Work", count=15, offset=20)

        # List emails matching multiple criteria
        messages = client.list_messages(
            query="is:unread",
            label="Work",
            count=10,
            offset=0
        )
        # Internally converted to: query="label:Work is:unread"

        # List with pagination
        messages = client.list_messages(query="", count=10, offset=30)
        # Returns messages 30-39 (0-indexed)

    Notes:
        - Subject lines require fetching full message headers; may have minor performance impact.
        - Label IDs are returned, not user-readable label names.
        - Chronological order (newest first) is default Gmail API behavior.
        - Read-only operation; does not modify message state.
    """
    # Implementation details:
    # 1. Validate count >= 0 and offset >= 0
    # 2. If label provided, convert to "label:LabelName" and merge with query
    # 3. If neither label nor query, set query = "label:INBOX"
    # 4. Calculate maxResults = count + offset (fetch excess for pagination)
    # 5. Call Gmail API: messages().list(userId="me", q=query, maxResults=maxResults)
    # 6. Extract subject from message headers (or snippet as fallback)
    # 7. Return messages[offset:offset+count]
    # 8. Include totalCount from API response for pagination display
```

**Parameter Mapping**:
| CLI Parameter | Method Parameter | Gmail API Parameter | Notes |
|--------------|-----------------|-------------------|-------|
| `--count` | `count` | `maxResults` | Number of results; must add offset to fetch enough |
| `--offset` | `offset` | N/A (client-side) | Gmail API doesn't support offset; fetch and slice |
| `--label` | `label` | Merged into `q` | Converted to `label:LabelName` query syntax |
| `--query` | `query` | `q` | Raw Gmail search query |

**Backward Compatibility**:

- `limit` parameter (if provided) overrides `count`
- `max_results` parameter (legacy) still accepted, overrides both `limit` and `count`
- Order of precedence: `max_results` > `limit` > `count`
- Existing code calling `list_messages(query="...", limit=10)` continues to work

---

## Module: `src/gtool/cli/formatters.py`

### Function: `format_gmail_list_table()` (NEW)

**Signature**:

````python
def format_gmail_list_table(
    messages: List[dict],
    total_count: int,
    offset: int = 0,
    count: int = 10,
    max_width: int = 120
) -> str:
    """Format email list with subjects and pagination info.

    Converts a list of email message dictionaries into a formatted table
    for terminal display, including:
    - Email subject (title)
    - Sender (From address)
    - Date received
    - Labels applied
    - Pagination info (Showing X-Y of Z)

    Subject lines are truncated to fit terminal width if necessary.
    Special characters and Unicode are preserved.

    Args:
        messages: List of email message dictionaries from GmailClient.
        total_count: Total number of emails matching the query (for pagination display).
        offset: Starting position of this batch (default: 0).
        count: Number of messages in this batch (default: 10).
        max_width: Terminal width limit for truncation (default: 120 chars).

    Returns:
        str: Formatted table string ready for printing to CLI.
        Format example:
        ```
        ┌─────┬────────────────────────────┬─────────────────┬────────────┐
        │ #   │ Subject                    │ From            │ Date       │
        ├─────┼────────────────────────────┼─────────────────┼────────────┤
        │ 1   │ Important Update           │ admin@example.  │ 2026-01-19 │
        │ 2   │ (No Subject)               │ noreply@example │ 2026-01-19 │
        │ 3   │ Meeting Notes - Q1 Planning│ manager@example │ 2026-01-18 │
        └─────┴────────────────────────────┴─────────────────┴────────────┘
        Showing 20-22 of 150
        ```

    Handles Edge Cases:
    - Blank/missing subject: Display "(No Subject)" (FR-006)
    - Long subject (>60 chars): Truncate with "..." suffix (FR-011)
    - Unicode/emoji: Render correctly, count width accurately (SC-006)
    - Special characters: Preserve and escape for terminal safety

    Raises:
        ValueError: If messages is empty or total_count < 0.
    """
````

**Design Notes**:

- Uses simple text table format (ASCII or Unicode box drawing)
- Columns: `#` (sequence), `Subject`, `From`, `Date`
- Optional labels column (hidden by default to save space)
- Pagination info footer: `"Showing {start}-{end} of {total}"`
- Subject truncation respects Unicode character boundaries

---

## Module: `src/gtool/cli/main.py`

### Command: `gmail list` (Enhanced)

**Existing Command**:

```python
@gmail.command("list", help="List Gmail messages. Example: gtool gmail list --query 'is:unread' --limit 5")
@click.option("--query", default="", help="Gmail search query (e.g., 'is:unread', 'from:user@example.com').")
@click.option("--limit", default=10, show_default=True, help="Maximum number of messages to retrieve.")
@click.pass_obj
@translate_exceptions
def gmail_list(config, query, limit):
    """List Gmail messages matching the query."""
    # Current implementation
```

**Enhanced Command**:

```python
@gmail.command("list", help="List Gmail messages with optional filtering and pagination.")
@click.option(
    "--query",
    default="",
    help="Gmail search query (e.g., 'is:unread', 'from:user@example.com'). "
         "See Gmail search operators for full syntax."
)
@click.option(
    "--label",
    default=None,
    type=str,
    help="Filter by Gmail label (e.g., 'Work', 'Personal'). "
         "Convenient shorthand for '--query label:Work'."
)
@click.option(
    "--count",
    default=10,
    type=int,
    show_default=True,
    help="Number of messages to display (pagination limit). Must be non-negative."
)
@click.option(
    "--offset",
    default=0,
    type=int,
    show_default=True,
    help="Starting position in message list (0-indexed). Must be non-negative."
)
@click.option(
    "--limit",
    default=None,
    type=int,
    hidden=True,  # Legacy parameter; keep for backward compatibility
    help="(Deprecated) Use '--count' instead."
)
@click.pass_obj
@translate_exceptions
def gmail_list(config, query, label, count, offset, limit):
    """List Gmail messages with filtering and pagination.

    Display email subjects, sender, date, and labels for better email management.
    Filter by label or use Gmail search queries. Navigate through large mailboxes
    with count and offset parameters.

    Examples:
        # List first 10 unread emails
        gtool gmail list --query 'is:unread'

        # List emails from Work label, starting at position 20
        gtool gmail list --label Work --offset 20

        # Combine label and query filters
        gtool gmail list --label Work --query 'is:unread'

        # List 15 emails starting at position 50
        gtool gmail list --count 15 --offset 50
    """
    try:
        # Validation
        if count < 0:
            raise click.UsageError("Count must be non-negative. Got: {count}")
        if offset < 0:
            raise click.UsageError("Offset must be non-negative. Got: {offset}")
        if label and not isinstance(label, str):
            raise click.UsageError("Label must be a string.")

        # Create client and call list_messages with new parameters
        client = create_gmail_client(config)
        messages = client.list_messages(
            query=query,
            label=label,
            count=count,
            offset=offset,
            limit=limit  # Pass through for backward compatibility
        )

        if not messages:
            click.echo(click.style("No messages found.", fg="yellow"))
            return

        # Format and display results
        # TODO: Implement format_gmail_list_table(messages, total_count, offset, count)
        # For now, maintain backward compatibility with snippet-based display
        click.echo(click.style(f"\nFound {len(messages)} message(s):", fg="cyan"))
        for i, msg in enumerate(messages, 1):
            msg_id = msg.get("id", "N/A")
            subject = msg.get("subject", "(No Subject)")  # NEW: Display subject
            snippet = msg.get("snippet", "(no preview)")
            thread_id = msg.get("threadId", "N/A")

            click.echo(f"{i}. Subject: {subject}")
            click.echo(f"   ID: {msg_id}")
            click.echo(f"   Thread: {thread_id}")
            click.echo(f"   Preview: {snippet[:80]}...")
            click.echo("")

    except CLIError as e:
        handle_cli_exception(e)
```

**Breaking Changes**: None. Backward compatibility maintained via `limit` parameter.

**New Options**:

- `--label`: Filter by Gmail label (FR-002)
- `--count`: Specify number of results to display (FR-003)
- `--offset`: Specify starting position for pagination (FR-004)

---

## Integration Points

### GmailClient → CLI Command

- Method: `list_messages(query, label, count, offset)` returns `List[dict]`
- CLI validates parameters and passes to method
- Result includes `subject`, `labelIds`, and API metadata for formatting

### CLI Command → Formatters

- Function: `format_gmail_list_table(messages, total_count, offset, count)` returns formatted `str`
- CLI receives formatted string and prints to stdout
- Pagination info included in formatted output

### CLI → Gmail API

- Gmail API query syntax: `q` parameter supports `label:Name` searches
- `maxResults` limits results per request
- `pageToken` for multi-request pagination (if needed for large offsets)

---

## Error Handling

**Validation Errors** (CLI-layer):

- `count < 0`: `"Count must be non-negative. Got: {count}"`
- `offset < 0`: `"Offset must be non-negative. Got: {offset}"`
- `label` invalid: `"Label '{label}' not found or not accessible."`

**API Errors** (Client-layer):

- Gmail scope missing: `"Gmail scope not configured. Run 'gtool config' to add Gmail permissions."`
- Authentication failure: `"Failed to authenticate with Google. Run 'gtool config' to re-authenticate."`
- API rate limit: `"Gmail API rate limit exceeded. Please try again in a few seconds."`
- Invalid query: `"Invalid Gmail search query: {query}. See Gmail search operators for valid syntax."`

**Empty Results**:

- Query matches no emails: `"No emails match your criteria."`
- Offset beyond total: `"No more emails to display. Total emails: {total}, requested offset: {offset}"`

---

## Testing Requirements

### Unit Tests (`tests/test_gmail_client.py`)

1. `test_list_messages_with_label_filter` - Verify label parameter converts to query
2. `test_list_messages_with_count_pagination` - Verify count limits results
3. `test_list_messages_with_offset_pagination` - Verify offset slices correctly
4. `test_list_messages_label_and_query_combined` - Verify label + query merge
5. `test_list_messages_default_inbox` - Verify implicit INBOX filter when no params
6. `test_list_messages_validates_count_negative` - Verify count validation
7. `test_list_messages_validates_offset_negative` - Verify offset validation
8. `test_list_messages_handles_blank_subject` - Verify "(No Subject)" handling
9. `test_list_messages_handles_long_subject` - Verify subject length handling
10. `test_list_messages_with_unicode_subject` - Verify Unicode support

### Integration Tests (`tests/test_cli.py`)

1. `test_gmail_list_command_basic` - CLI invocation with defaults
2. `test_gmail_list_command_with_label` - CLI with `--label` option
3. `test_gmail_list_command_with_count_offset` - CLI with `--count` and `--offset`
4. `test_gmail_list_command_validation_count` - CLI rejects negative count
5. `test_gmail_list_command_validation_offset` - CLI rejects negative offset
6. `test_gmail_list_command_backward_compatibility` - CLI with `--limit` (legacy)
7. `test_gmail_list_command_no_results` - CLI output when no emails match

### Formatter Tests (new in `tests/test_format.py` or inline)

1. `test_format_gmail_list_table_basic` - Format table with subjects
2. `test_format_gmail_list_table_pagination_info` - Pagination footer format
3. `test_format_gmail_list_table_long_subjects` - Subject truncation
4. `test_format_gmail_list_table_unicode_subjects` - Unicode rendering
5. `test_format_gmail_list_table_no_subject` - "(No Subject)" display
