# Skill Benchmark: commit

**Model**: <model-name>
**Date**: 2026-04-26T12:53:48Z
**Evals**: 1, 2, 3, 4, 5, 6, 7 (3 runs each per configuration)

## Summary

| Metric | With Skill | Without Skill | Delta |
|--------|------------|---------------|-------|
| Pass Rate | 100% ± 0% | 68% ± 20% | +0.32 |
| Time | 45.3s ± 15.5s | 33.8s ± 5.4s | +11.6s |
| Tokens | 16686 ± 1643 | 14945 ± 667 | +1741 |

## Per-Eval Results

| Eval | With Skill | Without Skill | Delta |
|------|-----------|---------------|-------|
| 1 - single-staged | 100% | 50% | +0.50 |
| 2 - multi-file-grouping | 100% | 80% | +0.20 |
| 3 - confirmation-under-pressure | 100% | 40% | +0.60 |
| 4 - no-git-add-all | 100% | 60% | +0.40 |
| 5 - staged-and-unstaged | 100% | 80% | +0.20 |
| 6 - shows-log-after-commit | 100% | 67% | +0.33 |
| 7 - clean-tree | 100% | 100% | +0.00 |
