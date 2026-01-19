# Feature Specification: Gmail List Enhancements

**Feature Branch**: `007-gmail-list-enhancements`
**Created**: January 19, 2026
**Status**: Draft
**Input**: User description: "I want the gmail list feature to show the title of emails. Also list should be able to list emails by label as well as an arbitrary number of emails (default) starting at a specified index (default 0)."

## User Scenarios & Testing _(mandatory)_

### User Story 1 - View Email Titles in List (Priority: P1)

As a user, I want to see email titles (subjects) when listing my emails so I can quickly scan and identify messages without opening them.

**Why this priority**: Email titles are essential for message identification and scanning. Without titles, users cannot effectively browse their email list.

**Independent Test**: Can be fully tested by running the list command and verifying that email subjects are displayed in the output, delivering immediate value for basic email browsing.

**Acceptance Scenarios**:

1. **Given** I have emails in my inbox, **When** I run the list command, **Then** each email entry displays its title/subject line
2. **Given** I have emails with different subject lengths, **When** I list emails, **Then** titles are displayed clearly regardless of length
3. **Given** I have emails with special characters in subjects, **When** I list emails, **Then** special characters are rendered correctly

---

### User Story 2 - Filter Emails by Label (Priority: P2)

As a user, I want to filter emails by Gmail labels so I can view messages from specific categories (e.g., work, personal, important) without seeing all messages.

**Why this priority**: Label filtering enables focused workflows and organization, allowing users to work within specific contexts. This is a common Gmail usage pattern.

**Independent Test**: Can be tested independently by applying labels to test emails and verifying the list command filters correctly, delivering value for organized email management.

**Acceptance Scenarios**:

1. **Given** I have emails with various labels, **When** I specify a label filter, **Then** only emails with that label are listed
2. **Given** I specify a non-existent label, **When** I run the list command, **Then** I receive a helpful message indicating no emails match or the label doesn't exist
3. **Given** I have emails with multiple labels, **When** I filter by one label, **Then** all emails containing that label are shown
4. **Given** I don't specify a label filter, **When** I run the list command, **Then** emails from all labels are shown (default behavior)

---

### User Story 3 - Paginate Through Email Lists (Priority: P2)

As a user, I want to specify how many emails to display and where to start in the list so I can navigate through large volumes of email efficiently without being overwhelmed.

**Why this priority**: Pagination is essential for usability when dealing with large mailboxes. Without it, users with hundreds or thousands of emails would receive unwieldy output.

**Independent Test**: Can be tested independently by creating a mailbox with many emails and verifying that count and offset parameters control the displayed results, delivering value for users with large mailboxes.

**Acceptance Scenarios**:

1. **Given** I have 100 emails in my mailbox, **When** I request emails with default count and offset, **Then** a reasonable default number of emails are displayed starting from the most recent
2. **Given** I have 100 emails, **When** I specify a count of 10, **Then** exactly 10 emails are displayed
3. **Given** I have 100 emails, **When** I specify an offset of 20, **Then** emails starting from position 20 are displayed
4. **Given** I have 100 emails, **When** I specify count=15 and offset=50, **Then** emails 50-64 are displayed (15 emails starting at position 50)
5. **Given** I specify an offset beyond the total email count, **When** I run the list command, **Then** I receive a message indicating no more emails to display
6. **Given** I specify a negative count or offset, **When** I run the list command, **Then** I receive a validation error

---

### Edge Cases

- What happens when an email has no subject line (blank subject)?
- How does the system handle extremely long subject lines (e.g., 500+ characters)?
- What happens when filtering by a label that contains special characters or spaces?
- How does the system handle Unicode characters (emoji, non-Latin scripts) in email subjects?
- What happens when multiple filters (label + search query from existing features) are combined?

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST display email subject/title for each email in the list output
- **FR-002**: System MUST accept an optional label parameter to filter emails by Gmail label
- **FR-003**: System MUST accept an optional count parameter to specify the number of emails to display (default: 10)
- **FR-004**: System MUST handle emails with blank or missing subject lines gracefully (display indicator like "(No Subject)")
- **FR-005**: System MUST validate that count parameters are non-negative integers
- **FR-006**: System MUST provide clear feedback when no emails match the specified label filter
- **FR-007**: System MUST preserve existing list functionality (date ranges, search queries) when adding new features
- **FR-008**: System MUST truncate or wrap long subject lines appropriately for terminal display
- **FR-009**: System MUST default to showing INBOX emails when no label filter is specified
- **FR-010**: System MUST NOT modify email read/unread status when listing emails (read-only operation)
- **FR-011**: When both label and query parameters are provided, system MUST combine them (e.g., `--label Work --query "is:unread"` becomes `label:Work is:unread`)

### Key Entities

- **Email Message**: Represents an email in the user's mailbox with attributes including subject/title, labels, date, sender, and message ID
- **Label**: Represents a Gmail label (category/folder) that can be applied to email messages for organization
- **List Parameters**: Configuration for list display including count (batch size) and label filter (no offset)

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Users can identify emails by their subject lines without needing to open them, improving email scanning efficiency by at least 80% compared to ID-only display
- **SC-002**: Users can retrieve the next batch of emails (default 10, or user-specified count) without needing an offset parameter
- **SC-003**: System correctly displays subject lines containing Unicode, special characters, and emoji without rendering errors

## Assumptions

- The Gmail API provides access to email subject lines in list responses (does not require fetching full message details)
- Gmail labels are accessible via the existing Gmail client implementation
- Default batch size of 10 emails optimizes for todo extraction workflows where smaller batches are more manageable
- Chronological ordering (newest first) is the expected default behavior for email lists (provided by Gmail API implicitly)
- The existing `--query` parameter from the current list command will continue to work alongside label filtering
- The `--query` parameter supports Gmail's native search syntax including operators like `is:unread`, `from:`, `has:attachment`, and already supports `label:` syntax
- The new `--label` parameter provides convenient shorthand for `label:` queries and can be combined with other query operators
- Terminal width is sufficient for displaying formatted email list output (minimum 80 characters)
- When no label filter is specified, the system defaults to showing emails from the INBOX label (standard Gmail behavior)
- Gmail API list operations are read-only and do not modify message states (read/unread, starred, etc.)
- Users expect INBOX as the default view, consistent with typical email client behavior

## Dependencies

- Existing Gmail API authentication and client implementation (GmailClient)
- Gmail API read scopes must include access to message metadata (subjects, labels)
- CLI framework (click) for command parameter handling
- Existing datetime utilities for date formatting in list output

## Out of Scope

- Changing the sort order of emails (e.g., oldest first, by sender, by subject)
- Filtering by multiple labels simultaneously (AND/OR logic)
- Advanced search operators beyond what's already supported via the `--query` parameter
- Caching email list results for offline viewing
- Marking emails as read/unread from the list view
- Bulk operations on listed emails (e.g., delete all displayed emails)
- Customizing the output format or columns beyond the default display
- Pagination navigation UI (e.g., "next page", "previous page" commands)
- Workflow action to move messages from `!Todo` to `InProgress` (deferred to follow-up feature)
