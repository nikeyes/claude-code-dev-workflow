---
name: bugmagnet
description: Lightweight bug discovery and test coverage analysis for a code module. Use when the user asks to find bugs, analyze test coverage, write edge case tests, or do exploratory testing on a file. Triggers on "bugmagnet", "find bugs in", "test coverage gaps", "edge cases for", or "exploratory testing on <file>".
---

# BugMagnet

Analyze a code module, write comprehensive edge-case tests, and document discovered bugs.

**Attribution:** Adapted from [BugMagnet AI Assistant](https://github.com/gojko/bugmagnet-ai-assistant) by [Gojko Adzic](https://gojko.net) (MIT License).

## Usage
```
/bugmagnet <implementation-file-path>
```

## Workflow

1. Read the implementation file and its existing tests
2. Identify untested edge cases, boundary conditions, and error paths
3. Write tests — run each one immediately after writing
4. When a test reveals a bug, document it as a skipped test (see format below), then explore nearby: bugs cluster together
5. Summarize findings

Do NOT modify the implementation file. Only write tests.

## Bug Documentation Format

When a test reveals unexpected behavior, create a skipped test using the framework's skip mechanism with "- BUG" in the test name:

```
test.skip('normalizeEmail crashes on input without @ - BUG', () => {
    /*
     * ROOT CAUSE: destructuring email.split("@") fails when no @ present
     * CODE LOCATION: src/validator.ts:49
     * PROPOSED FIX: guard with if (!email.includes("@")) before split
     * EXPECTED: throws or returns input unchanged
     * ACTUAL: TypeError: Cannot read properties of undefined
     */
    expect(() => normalizeEmail("nodomain")).not.toThrow();
});
```

Every skipped BUG test must include: ROOT CAUSE, CODE LOCATION, PROPOSED FIX, EXPECTED vs ACTUAL.

## Summary Format

After all tests are written, provide:

```
## Test Coverage Summary

**Tests Added:** N total
- Category 1 (X tests)
- Category 2 (Y tests)

**Results:** X passing, Y skipped (bugs)

**Bugs Discovered:**
1. Bug name — file:line
   - Root cause: ...
   - Proposed fix: ...
```
