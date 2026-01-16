# Feature Specification: Gmail Client Integration & Google Auth Refactoring

**Feature Branch**: `001-gmail-client-refactor`
**Created**: 2026-01-15
**Status**: Draft
**Input**: User description: "Refactor the project to support adding a gmail client and gmail related functionality to the CLI. Pay attention to opportunities for reusing existing functionality (i.e. google auth, ...)"

## User Scenarios & Testing _(mandatory)_

### User Story 1 - Initialize Gmail with Shared Google Auth (Priority: P1)

Developers add Gmail functionality to the calendarcli project by leveraging existing Google OAuth infrastructure. The refactored codebase extracts authentication and credential management into a reusable module so both Calendar and Gmail clients use the same authentication flow, token refresh logic, and scopes configuration.

**Why this priority**: This is foundational work that enables all future Gmail features. Without shared authentication infrastructure, each new Google API client will duplicate auth logic and create maintenance burden. This P1 story establishes the architectural pattern.

**Independent Test**: Can be verified by creating a new Gmail client that authenticates using the same shared auth module as the Calendar client, with no auth logic duplication.

**Acceptance Scenarios**:

1. **Given** a developer wants to add Gmail functionality, **When** they create a new Gmail client class, **Then** they can inherit or reuse authentication from the shared Google auth module without implementing OAuth flow again.
2. **Given** a user has valid Google Calendar credentials, **When** they add `gmail` scope to their configuration, **Then** the existing auth flow refreshes or updates credentials to include the new scope without requiring re-authentication.
3. **Given** multiple Google API clients are initialized, **When** credentials expire, **Then** all clients share the same token file and refresh logic so only one refresh request is made.

---

### User Story 2 - Unified Google Client Architecture (Priority: P1)

The codebase establishes a common base interface/pattern for all Google API clients (Calendar, Gmail, etc.). This enables consistent service initialization, error handling, retry logic, and configuration management across different Google APIs.

**Why this priority**: P1 because architectural consistency now prevents fragmentation later. Each new Google API client added without this foundation will have different error handling, retry strategies, and initialization patterns, making the codebase harder to maintain.

**Independent Test**: Can be verified by implementing a base Google client class or protocol that both Calendar and Gmail clients conform to, ensuring consistent behavior and contract.

**Acceptance Scenarios**:

1. **Given** a base Google client abstraction exists, **When** both Calendar and Gmail clients are initialized, **Then** both follow the same initialization contract (config injection, service building, authentication).
2. **Given** a Google API call fails with a temporary error, **When** both Calendar and Gmail clients handle the error, **Then** both use the same retry decorator and strategy without code duplication.
3. **Given** developers need to add a third Google API client (e.g., Drive, Sheets), **When** they follow the base pattern, **Then** no auth or retry logic needs to be re-implemented.

---

### User Story 3 - Gmail Client MVP Implementation (Priority: P2)

A functional Gmail client is added to the project that can list messages and basic operations (read, mark as read). The Gmail client uses the refactored shared authentication and base client patterns.

**Why this priority**: P2 because this delivers visible Gmail functionality but depends on the P1 architectural work. Once the foundation is solid, implementation is straightforward.

**Independent Test**: Can be verified by running `caltool gmail list` command to retrieve and display user's Gmail messages, confirming the client works end-to-end.

**Acceptance Scenarios**:

1. **Given** a user has authenticated and added `https://www.googleapis.com/auth/gmail.readonly` to scopes, **When** they run `caltool gmail list`, **Then** their recent Gmail messages are retrieved and displayed.
2. **Given** a user runs `caltool gmail list --limit 10`, **When** the command executes, **Then** exactly 10 messages are returned (or fewer if inbox has fewer).
3. **Given** the Gmail API returns an error (e.g., rate limit), **When** the client handles it, **Then** the error message is user-friendly and suggests remediation (wait and retry, check credentials, etc.).

---

### User Story 4 - Configuration Schema Extension for Gmail (Priority: P2)

Configuration system is extended to support Gmail-specific settings (e.g., labels, output format preferences). The `caltool config` command guides users through Gmail setup and scope selection.

**Why this priority**: P2 because users need clear configuration guidance, but the core Gmail functionality (US3) is the main value driver. Configuration can be refined iteratively.

**Independent Test**: Can be verified by running `caltool config` and confirming users can add/select Gmail-specific settings and scopes interactively.

**Acceptance Scenarios**:

1. **Given** a user runs `caltool config`, **When** prompted for scopes, **Then** they can select or add Gmail scopes (e.g., `gmail.readonly`, `gmail.modify`) alongside Calendar scopes.
2. **Given** a user has Gmail scopes configured, **When** they run `caltool config`, **Then** Gmail-specific options (e.g., labels, sync frequency) are presented and editable.
3. **Given** a user removes Gmail scopes from config, **When** they run a Gmail command, **Then** a clear error directs them to re-add scopes via `caltool config`.

---

### User Story 5 - Module Reorganization for Separation of Concerns (Priority: P1)

The project structure is reorganized to clearly separate Google authentication/credential logic, service initialization, and client implementations (Calendar, Gmail, etc.). This enables developers to understand and modify each concern independently.

**Why this priority**: P1 because this architectural clarity is non-negotiable per the constitution (Principle I: Separation of Concerns). Without clear separation, adding Gmail client will muddy the Calendar client code and make future Google APIs harder to integrate.

**Independent Test**: Can be verified by examining the module structure and confirming that auth, service, and client code are isolated with clear contracts between them.

**Acceptance Scenarios**:

1. **Given** the new module structure, **When** a developer opens `src/caltool/auth.py` (or similar), **Then** they find ONLY authentication and credential management logic (no Calendar or Gmail API calls).
2. **Given** a developer wants to understand how the Gmail client works, **When** they examine `src/caltool/gmail_client.py`, **Then** they see only Gmail-specific API methods, not OAuth or service initialization details.
3. **Given** the project has N Google API clients, **When** a breaking change happens in Google OAuth library, **Then** only one module (`src/caltool/auth.py` or `google_auth.py`) needs updating.

---

### Edge Cases

- What happens when a user has only Calendar scope but attempts to run a Gmail command? (Error message directing them to add Gmail scopes)
- What happens when credentials file exists but token file is missing? (Auth flow should handle gracefully)
- What happens when a user switches from one Google account to another? (Token file management and re-auth flow)
- What happens when an API scope is revoked by the user in Google Account settings? (Error handling and guidance to re-authenticate)
- What happens if the project is used offline or without internet? (Graceful degradation and clear error messages)

## Requirements _(mandatory)_

### Functional Requirements

- **FR-001**: System MUST extract authentication and credential management into a dedicated module separate from client implementations
- **FR-002**: System MUST support multiple Google API scopes (Calendar, Gmail) managed via configuration
- **FR-003**: System MUST provide a base client abstraction or protocol that all Google API clients (Calendar, Gmail, etc.) conform to
- **FR-004**: System MUST implement a Gmail client that can authenticate, list messages, and handle basic Gmail operations
- **FR-005**: System MUST reuse existing retry logic decorator and error handling patterns for all Google API clients
- **FR-006**: System MUST allow configuration of Gmail-specific settings (labels, output format) via `caltool config` command
- **FR-007**: System MUST maintain backward compatibility with existing Calendar functionality during refactoring
- **FR-008**: System MUST provide user-friendly error messages that distinguish between authentication, authorization, and transient API errors
- **FR-009**: System MUST support scope-based feature availability (if user lacks Gmail scope, Gmail commands display clear guidance)
- **FR-010**: System MUST share a single token file and refresh mechanism across all Google API clients to avoid unnecessary re-authentication

### Key Entities

- **GoogleAuth**: Core authentication handler managing OAuth flow, credential persistence, token refresh, and scope management
- **GoogleAPIClient** (abstract/base): Common interface for all Google API clients defining initialization contract, error handling, and service building patterns
- **GCalClient**: Existing Calendar client refactored to inherit from or delegate to GoogleAPIClient base
- **GMailClient**: New Gmail client following GoogleAPIClient pattern for message management
- **Config**: Extended to support Gmail-specific settings and scope management
- **Scope**: Represents a Google API scope (e.g., `https://www.googleapis.com/auth/gmail.readonly`) with metadata about which client uses it

## Success Criteria _(mandatory)_

### Measurable Outcomes

- **SC-001**: Zero code duplication in authentication logic between Calendar and Gmail clients (100% of auth code centralized in one module)
- **SC-002**: All existing Calendar functionality works identically before and after refactoring (backward compatibility verified by all existing tests passing)
- **SC-003**: New Gmail client can authenticate and retrieve messages in under 2 seconds after initial setup (performance acceptable)
- **SC-004**: All new code includes type hints and docstrings per PEP8 standards (100% code coverage for new modules)
- **SC-005**: Test coverage for new Gmail client and auth module is 80% or higher
- **SC-006**: Developer can add a third Google API client (e.g., Drive) in under 2 hours by following the established patterns
- **SC-007**: Users can set up Gmail integration via `caltool config` without documentation (UX clarity metric)
- **SC-008**: Error messages from Gmail failures clearly indicate root cause (auth, scope, quota, transient) in 100% of cases

## Assumptions

- Users will have a single Google account for both Calendar and Gmail (single credentials file scenario; multi-account support deferred to P3)
- Gmail scope additions do not require full re-authentication if other scopes are already valid (incremental scope authorization supported by Google OAuth)
- Existing `GCalClient` can be refactored with minimal behavior change (no breaking API changes for Calendar users)
- The project will continue to use `google-auth-oauthlib`, `google-auth`, and `google-api-python-client` libraries
- Configuration validation logic can be extended to support Gmail settings without major architectural changes

## Dependencies & Constraints

- **External Dependencies**: Google Calendar API (v3) and Gmail API (v1) via existing google-api-python-client library
- **Internal Dependencies**: Refactoring touches `config.py`, `gcal_client.py`, `cli.py`, and `errors.py`; all existing tests must pass post-refactoring
- **Scope Constraint**: Initial Gmail client supports read-only operations; write operations (send, draft) deferred to future P2/P3 stories
- **Backward Compatibility**: Must not break existing Calendar CLI commands or configuration format
