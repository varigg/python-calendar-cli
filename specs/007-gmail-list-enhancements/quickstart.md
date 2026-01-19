# Quickstart: Gmail List Enhancements

## Overview

The Gmail list feature now supports:

1. **Subject Display**: See email titles directly in the list
2. **Label Filtering**: Filter emails by Gmail label
3. **Pagination**: Control how many emails to show and where to start

## Command Syntax

```bash
gtool gmail list [OPTIONS]
```

## Basic Usage

### List Recent Emails (Default)

```bash
$ gtool gmail list
```

**Output**:

```
Found 10 message(s):

1. Subject: Team Standup Notes
   ID: 187a45b5d1a2c3d4
   Thread: thread-1
   Preview: Yesterday we reviewed Q1 goals and identified key blockers...

2. Subject: Code Review: PR #456
   ID: 187a45b5d1a2c3d5
   Thread: thread-2
   Preview: Thanks for the submission. I have a few comments on the approach...

[...]

Showing 1-10 of 147
```

- Displays first 10 emails (default count)
- Shows subjects for email identification
- Includes pagination info

### List Unread Emails

```bash
$ gtool gmail list --query 'is:unread'
```

**Output**:

```
Found 5 message(s):

1. Subject: Important: Action Required
   ID: 187a45b5d1a2c3d6
   Thread: thread-3
   Preview: We need your input on the proposal by end of week...

[...]
```

- Filters to only unread emails
- Subject-first display helps prioritize reading
- Use existing `--query` parameter with Gmail search operators

## New Features

### 1. Filter by Label

```bash
$ gtool gmail list --label Work
```

- Shows only emails with the "Work" label
- Convenient shorthand for `--query 'label:Work'`
- Use `--label Personal` for personal emails, `--label Important`, etc.

**Example**: Work-related emails starting at position 0:

```bash
$ gtool gmail list --label Work --offset 0 --count 10
```

### 2. Pagination: Control Count

```bash
$ gtool gmail list --count 20
```

- Show 20 emails instead of default 10
- Useful for getting more context in one view
- Works with any other filter

**Example**: First 20 unread emails:

```bash
$ gtool gmail list --query 'is:unread' --count 20
```

### 3. Pagination: Navigate with Offset

```bash
$ gtool gmail list --offset 30 --count 10
```

- Skip first 30 emails, show next 10 (emails #31-40)
- Use 0-based indexing: offset=0 is the first email
- Useful for navigating large mailboxes

**Workflow**: Browsing emails in batches:

```bash
# First page: emails 1-10
$ gtool gmail list --offset 0 --count 10

# Second page: emails 11-20
$ gtool gmail list --offset 10 --count 10

# Third page: emails 21-30
$ gtool gmail list --offset 20 --count 10
```

## Combining Filters

### Label + Unread

```bash
$ gtool gmail list --label Work --query 'is:unread'
```

Internally converted to: `label:Work is:unread`

Shows only unread emails from the Work label.

### Label + Sender + Pagination

```bash
$ gtool gmail list --label Project --query 'from:manager@company.com' --count 15 --offset 0
```

Shows first 15 emails from the Project label sent by manager@company.com.

### Complex Query + Pagination

```bash
$ gtool gmail list --query 'has:attachment is:unread' --count 25 --offset 50
```

Shows emails 51-75 that have attachments and are unread.

## Parameter Reference

| Parameter  | Default | Description                   | Example                                                      |
| ---------- | ------- | ----------------------------- | ------------------------------------------------------------ |
| `--query`  | ""      | Gmail search query            | `'is:unread'`, `'from:user@example.com'`, `'has:attachment'` |
| `--label`  | None    | Filter by label               | `Work`, `Personal`, `Important`                              |
| `--count`  | 10      | Number of emails to show      | `5`, `20`, `50`                                              |
| `--offset` | 0       | Starting position (0-indexed) | `0`, `10`, `100`                                             |

## Gmail Search Operators (for `--query`)

```bash
# Unread
$ gtool gmail list --query 'is:unread'

# From specific sender
$ gtool gmail list --query 'from:boss@company.com'

# With attachments
$ gtool gmail list --query 'has:attachment'

# Before/after dates
$ gtool gmail list --query 'before:2026-01-01'
$ gtool gmail list --query 'after:2026-01-01'

# Subject contains text
$ gtool gmail list --query 'subject:proposal'

# Multiple conditions (AND)
$ gtool gmail list --query 'is:unread from:colleague@company.com has:attachment'

# Label search (equivalent to --label)
$ gtool gmail list --query 'label:Project'
```

See [Gmail search operators guide](https://support.google.com/mail/answer/7190?hl=en) for full list.

## Handling Edge Cases

### Email with No Subject

```
1. Subject: (No Subject)
   ID: 187a45b5d1a2c3d7
   Thread: thread-4
   Preview: This email arrived without a subject line...
```

Blank subjects display as `"(No Subject)"` for clarity.

### Long Subject Lines

```
3. Subject: Meeting Notes - Q1 Planning & Strategy Alignment...
   ID: 187a45b5d1a2c3d9
   Thread: thread-6
   Preview: Here's the summary from today's all-hands meeting...
```

Long subjects are truncated to fit terminal width with `...` suffix.

### Large Mailboxes

```bash
# Find total count of unread emails
$ gtool gmail list --query 'is:unread'
# Output: Showing 1-10 of 523

# Jump to emails 500-509
$ gtool gmail list --query 'is:unread' --offset 500 --count 10
```

Pagination info shows total count, enabling navigation through mailboxes with thousands of emails.

### Offset Beyond Total

```bash
$ gtool gmail list --offset 10000 --count 10
```

**Output**:

```
No more emails to display. Total emails: 147, requested offset: 10000
```

Clear message indicates no results available at that offset.

## Real-World Examples

### Daily Email Review Workflow

```bash
# Check unread emails
$ gtool gmail list --query 'is:unread' --count 15

# Check important messages
$ gtool gmail list --query 'is:important' --count 10

# Review work-related unread
$ gtool gmail list --label Work --query 'is:unread'
```

### Project-Based Organization

```bash
# All ProjectX emails
$ gtool gmail list --label ProjectX

# Unread ProjectX messages
$ gtool gmail list --label ProjectX --query 'is:unread'

# ProjectX emails from the lead
$ gtool gmail list --label ProjectX --query 'from:projectlead@company.com'
```

### Batch Processing

```bash
# Process emails in batches of 20
$ gtool gmail list --query 'label:ProcessMe' --offset 0 --count 20
$ gtool gmail list --query 'label:ProcessMe' --offset 20 --count 20
$ gtool gmail list --query 'label:ProcessMe' --offset 40 --count 20
# Continue until "No more emails" message
```

### Finding Specific Messages

```bash
# Emails from a specific person this month
$ gtool gmail list --query 'from:colleague@example.com after:2026-01-01'

# Unread attachments from past week
$ gtool gmail list --query 'has:attachment is:unread after:2026-01-13'

# Messages I sent to a domain
$ gtool gmail list --query 'from:me to:*.company.com'
```

## Backward Compatibility

The feature maintains full backward compatibility with existing code:

```bash
# Old syntax (still works)
$ gtool gmail list --query 'is:unread' --limit 10

# New syntax (recommended)
$ gtool gmail list --query 'is:unread' --count 10
```

Both `--limit` and `--count` work; `--limit` is treated as a legacy alias.

## Configuration Requirements

Ensure Gmail scope is enabled:

```bash
$ gtool config
# Follow prompts to enable Gmail scope if not already configured
```

The feature requires `Gmail readonly scope` to access email subjects and metadata.

## Troubleshooting

### "Gmail scope not configured"

```bash
$ gtool config
# Re-run interactive config and select Gmail permissions
```

### "Label not found"

```bash
# Check available labels by running a generic list
$ gtool gmail list

# If using custom label, verify the exact label name (case-sensitive)
$ gtool gmail list --label "My Custom Label"  # Include spaces if part of name
```

### "Invalid Gmail search query"

Ensure query uses valid Gmail search operators. Examples:

- `is:unread` ✅ Correct
- `unread` ❌ Incorrect (should be `is:unread`)
- `from: user@example.com` ❌ Incorrect (no space after `from:`)
- `from:user@example.com` ✅ Correct

### Performance: Large Offset

Requesting offset=1000 with count=10 may be slow (fetches 1010 messages). For large mailboxes, prefer using `--query` filters to reduce result set before pagination.

```bash
# Slower (fetches 1010 messages)
$ gtool gmail list --offset 1000 --count 10

# Faster (filters first, then paginates)
$ gtool gmail list --query 'label:Work' --offset 50 --count 10
```

## What's Next?

- **See Message Details**: `gtool gmail show-message <id>`
- **Delete Message**: `gtool gmail delete <id>`
- **Search Syntax**: Learn more [Gmail search operators](https://support.google.com/mail/answer/7190)
- **Labels Management**: Manage labels directly in Gmail web interface
