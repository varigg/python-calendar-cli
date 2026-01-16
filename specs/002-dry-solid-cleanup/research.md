# Research: DRY/SOLID Code Cleanup

**Feature**: 002-dry-solid-cleanup  
**Date**: January 15, 2026

## Summary

This is a straightforward refactoring task. No external research was required—all decisions are based on code review findings and established best practices.

## Decisions

### 1. Which duplicate methods to remove

**Decision**: Remove the earlier definitions (lines 63-99 in config.py)  
**Rationale**: Python silently uses the last definition when duplicates exist. The later definitions (lines 215-256) are the ones actually executed and are more complete with better docstrings.  
**Alternatives considered**: Keep earlier definitions (rejected: later definitions are authoritative)

### 2. Retry implementation to keep

**Decision**: Keep `@staticmethod retry()` decorator, remove `retry_on_exception()` instance method  
**Rationale**: The `@retry` decorator is actively used by all API methods in GCalClient and GMailClient. The instance method is unused.  
**Alternatives considered**: Keep both (rejected: YAGNI - unused code should be removed)

### 3. Exception handling strategy

**Decision**: Catch `CLIError` and `google.auth.exceptions.GoogleAuthError` specifically, let other exceptions propagate  
**Rationale**: CLIError is already designed for user-friendly messages. Auth errors need special handling. Other exceptions indicate bugs that should be visible for debugging.  
**Alternatives considered**: Catch all exceptions (rejected: masks bugs); catch nothing (rejected: breaks user experience)

### 4. Abstract method pattern

**Decision**: Remove `@abstractmethod` from `_validate_config()` since it has a concrete implementation  
**Rationale**: Abstract methods should have no implementation. The current pattern forces unnecessary overrides (like GCalClient's empty override).  
**Alternatives considered**: Make it truly abstract with no body (rejected: base validation logic would need to be duplicated in every subclass)

### 5. Import organization

**Decision**: Move all function-level imports to module level  
**Rationale**: PEP8 recommends imports at module top. Function-level imports add cognitive overhead without benefit.  
**Alternatives considered**: Keep function-level imports for lazy loading (rejected: no performance benefit in this codebase)

## No Research Tasks Required

All issues identified in code review have clear, well-established solutions:

- DRY violations → Remove duplicates (keep authoritative version)
- YAGNI violations → Remove unused code
- KISS violations → Simplify abstractions
- Import patterns → Follow PEP8
