---
name: test-desiderata
description: Analyze and improve test code quality using Kent Beck's Test Desiderata framework. Use when analyzing test files, reviewing test code, identifying test quality issues, suggesting test improvements, or when asked to evaluate tests against best practices. Applies to unit tests, integration tests, and any automated test code.
---

# Test Desiderata

Analyze and improve tests using Kent Beck's Test Desiderata framework - 12 properties that make tests more valuable.

**Attribution:** All Test Desiderata concepts and principles are created by Kent Beck. Original content: https://testdesiderata.com/ and https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b3

## Analysis Workflow

When analyzing tests:

1. **Read the test code** - Understand what's being tested and how
2. **Evaluate against principles** - Assess each relevant Test Desiderata property
3. **Identify tradeoffs** - Note where properties conflict or support each other
4. **Prioritize improvements** - Focus on high-impact issues first
5. **Suggest specific changes** - Provide concrete, actionable recommendations

## The 12 Test Desiderata Properties

These properties make tests more valuable. Some support each other, some interfere, and sometimes properties only seem to interfere (that's where design improvements help).

### 1. Isolated
Tests return the same results regardless of execution order. Tests don't depend on shared state, previous test results, or external ordering.

**Issues to detect:**
- Shared mutable state between tests
- Tests that must run in specific order
- Setup/teardown that affects other tests
- Database state dependencies

### 2. Composable
Test different dimensions of variability separately and combine results. Break complex scenarios into independent, reusable test components.

**Issues to detect:**
- Monolithic tests covering multiple concerns
- Inability to test dimensions independently
- Duplicated test setup across related tests
- Tests that can't be combined or reused

### 3. Deterministic
If nothing changes, test results don't change. No randomness, timing dependencies, or environmental variations.

**Issues to detect:**
- Random data generation
- Time-dependent assertions
- Flaky tests that pass/fail intermittently
- Network or external service dependencies

### 4. Fast
Tests run quickly, enabling frequent execution during development.

**Issues to detect:**
- Slow database operations
- Unnecessary sleep/wait calls
- Heavy file I/O
- External service calls
- Inefficient test data setup

### 5. Writable
Tests are cheap to write relative to the code being tested. Low friction for adding new tests.

**Issues to detect:**
- Excessive boilerplate
- Complex test setup
- Hard-to-understand test frameworks
- Difficult mocking/stubbing

### 6. Readable
Tests are comprehensible and invoke the motivation for writing them. Clear intent and behavior.

**Issues to detect:**
- Unclear test names
- Complex assertions without explanation
- Missing context about "why"
- Obscure test data
- Poor structure (Arrange-Act-Assert)

### 7. Behavioral
Tests are sensitive to behavior changes. If behavior changes, test results change.

**Issues to detect:**
- Tests that pass despite broken functionality
- Assertions that check implementation details only
- Insufficient coverage of edge cases
- Missing assertions on outcomes

### 8. Structure-insensitive
Tests don't change when code structure changes (refactoring doesn't break tests).

**Issues to detect:**
- Tests coupled to internal implementation
- Mocking private methods
- Assertions on internal state
- Tests breaking during refactoring despite unchanged behavior

### 9. Automated
Tests run without human intervention. No manual steps or verification required.

**Issues to detect:**
- Manual verification steps
- Console output requiring human inspection
- Interactive prompts
- Manual data setup

### 10. Specific
When tests fail, the cause is obvious. Failures point directly to the problem.

**Issues to detect:**
- Generic error messages
- Multiple assertions per test
- Tests covering too much functionality
- Unclear failure output

### 11. Predictive
If all tests pass, code is suitable for production. Tests catch issues before deployment.

**Issues to detect:**
- Missing critical scenarios
- Insufficient integration testing
- Gaps in error handling coverage
- Production-only configurations not tested

### 12. Inspiring
Passing tests inspire confidence in the system. Comprehensive coverage of important behaviors.

**Issues to detect:**
- Trivial tests that don't verify meaningful behavior
- Low coverage of critical paths
- Missing tests for known edge cases
- Tests that don't reflect real usage

## Analyzing Tradeoffs

Kent Beck's key insight: properties can support, interfere, or **only seem to interfere** with each other. When violations only seem to interfere, it signals a design opportunity — fixing one enables fixing the other.

**This is the most valuable part of the analysis.** Detection alone is straightforward; understanding how violations interact reveals the root cause and the highest-leverage fix.

### Three Relationships Between Properties

**Supporting** — fixing one helps the other:
- Isolated + Deterministic → More reliable tests
- Fast + Automated → More frequent execution
- Readable + Specific → Easier debugging

**Interfering** — real tension, must choose which to prioritize:
- Predictive + Fast → Comprehensive tests are often slower
- Isolated + Fast → Per-test setup/teardown adds overhead (temp files, fresh DB connections)
- Writable + Predictive → Simple tests may not catch all issues
- Isolated + Writable → Fresh instances per test mean more setup code

**Only seeming to interfere** — a design change resolves both:
- Isolated ↔ Specific: shared state forces monolithic tests; fresh instances make splitting safe
- Composable ↔ Fast: splitting tests adds setup, but lightweight fixtures eliminate the overhead
- Writable ↔ Readable: extracting fixtures with descriptive names improves both
- Isolated ↔ Writable: beforeEach/fixture patterns give isolation without boilerplate
- Behavioral ↔ Composable: splitting a combined test exposes hidden behavioral bugs in each part

### How to Report Tradeoffs

When the analysis detects **2 or more violated properties**, actively look for relationships between them:

1. **Identify pairs** — which violated properties interact? Not all do; some are independent.
2. **Classify the relationship** — is it supporting, interfering, or only seeming to interfere?
3. **Explain the design insight** — if "only seeming to interfere," name the specific design change that resolves both. If truly interfering, recommend which to prioritize for this codebase and why.
4. **Include a Tradeoffs section** in the output that covers all identified pairs with concrete analysis.

## Prioritizing Improvements

Focus improvements on:

1. **Safety issues** - Fix Isolated and Deterministic first (flaky tests erode trust)
2. **Feedback loop** - Improve Fast to enable frequent testing
3. **Maintainability** - Enhance Readable and Structure-insensitive for long-term health
4. **Confidence** - Strengthen Predictive and Inspiring for production readiness

Not all properties need perfect scores. Optimize for the tradeoffs that matter most for the specific codebase and team.

## Providing Recommendations

When suggesting improvements:

1. **Be specific** - Point to exact code locations
2. **Explain the principle** - Reference which Test Desiderata property is violated
3. **Show the impact** - Describe why it matters
4. **Suggest concrete fixes** - Provide actionable code examples
5. **Analyze tradeoffs** - When two or more properties are violated, explain how they interact and which to fix first

Example format:
```
Issue: Test "test_user_creation" violates Isolated property
Location: Line 45 - shares database connection across tests
Impact: Test results depend on execution order, causing intermittent failures
Fix: Use fresh database connection per test with proper cleanup
```

Tradeoff analysis example:
```
Tradeoff: Isolated ↔ Fast (only seeming to interfere)
The shared database connection creates an Isolated violation, and fresh connections per test
seem to conflict with Fast (more setup time). But this is a design opportunity: using an
in-memory database or connection pool gives both Isolated AND Fast.
Priority: Fix Isolated first — flaky tests erode trust faster than slow tests.
```

## Additional Resources

For detailed examples and patterns, see [test-desiderata.md](references/test-desiderata.md)

For Kent Beck's original content:
- Website: https://testdesiderata.com/
- Original essay: https://medium.com/@kentbeck_7670/test-desiderata-94150638a4b3
- Video series: Each property has a 5-minute explanatory video on YouTube
