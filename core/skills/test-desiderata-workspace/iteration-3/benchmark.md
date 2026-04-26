# Skill Benchmark: test-desiderata

**Date**: 2026-04-26T21:30:00Z
**Evals**: 1-7 (1 run per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 97% ± 5% | 75% ± 5% | +0.22 |
| Time | 78.2s | 59.8s | +18.4s |
| Tokens | 19939 | 16596 | +3343 |

## Per-Eval Results

| Eval | With Skill | Without Skill | Delta |
|------|-----------|---------------|-------|
| 1 | 100% | 77% | +0.23 |
| 2 | 100% | 77% | +0.23 |
| 3 | 100% | 69% | +0.31 |
| 4 | 100% | 82% | +0.18 |
| 5 | 92% | 77% | +0.15 |
| 6 | 100% | 75% | +0.25 |
| 7 | 87% | 67% | +0.20 |

## Iteration Comparison (vs iteration-1)

| Metric | Iteration-1 | Iteration-3 | Change |
|--------|------------|-------------|--------|
| With Skill | 97.6% | 97.0% | -0.6pp |
| Without Skill | 94.4% | 74.9% | -19.5pp |
| Delta | +0.033 | +0.221 | +18.8pp |

## Key Observations

- Tradeoff expectations are the primary differentiator: with-skill passes them consistently, without-skill never produces a Tradeoffs section
- Detection and recommendation expectations are near-parity (as expected — baseline was already strong here)
- Eval 6 (false positive): with-skill correctly identifies 1 borderline concern; without-skill over-detects with 5 issues
