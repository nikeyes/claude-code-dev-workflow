# Test-Desiderata Skill — Iteration 1 Benchmark

## Summary

| Configuration | Mean Pass Rate | Total Assertions | Mean Tokens |
|---|---|---|---|
| with_skill | **97.6%** | 70/72 | 22,510 |
| without_skill | 94.4% | 68/72 | 18,336 |
| **delta** | **+3.2pp** | +2 | +22.8% overhead |

## Per-Eval Results

| # | Eval | Difficulty | with_skill | without_skill | Delta | Token overhead |
|---|------|-----------|-----------|--------------|-------|----------------|
| 1 | Python BankAccount | easy | 10/10 (100%) | 10/10 (100%) | 0 | +4,531 |
| 2 | TypeScript OrderService | easy | 10/10 (100%) | 10/10 (100%) | 0 | +3,685 |
| 3 | Go Inventory | easy | 10/10 (100%) | 9/10 (90%) | +10pp | +4,605 |
| 4 | Python NotificationService | medium | 10/11 (91%) | 10/11 (91%) | 0 | +4,358 |
| 5 | TypeScript LRUCache | medium | 10/10 (100%) | 10/10 (100%) | 0 | +3,548 |
| 6 | Python AuthService (false positive) | hard | 8/8 (100%) | 7/8 (88%) | +12pp | +5,241 |
| 7 | Python DataPipeline (tradeoffs) | hard | 12/13 (92%) | 12/13 (92%) | 0 | +3,250 |

## Key Findings

### Where skill adds value
- **Eval 6 (false positive):** skill scores 100% vs baseline 88%. The skill correctly avoided manufacturing violations and gave a concrete boundary test suggestion, where the baseline stopped at identifying the gap without prescribing the fix.
- **Eval 3 (Go Inventory):** skill 100% vs baseline 90%. Baseline failed to suggest `t.Logf` as the replacement for `fmt.Printf` — it suggested removal only.

### Where skill adds no value  
- **Evals 1, 2, 4, 5, 7:** identical scores. The baseline model already detects all violations correctly and provides good recommendations without the skill.

### Cost analysis
- The skill costs +22.8% more tokens on average (~4,200 extra tokens per run).
- The +3.2pp delta over 5 evals is marginal — only 2 assertions out of 72 were captured exclusively by the skill.

## Analyst Observations

1. **Skill is not discriminating on detection.** Both configurations detect essentially all violations. The evaluation framework confirms the baseline model knows the Test Desiderata framework well and doesn't need the skill for detection.

2. **Skill adds marginal value on format/calibration.** The 2-assertion gap is from: (a) the false-positive eval where with_skill gave a more specific boundary test suggestion, and (b) the Go eval where without_skill recommended removal rather than `t.Logf`. Neither is a strong signal.

3. **The `t.Logf` assertion is overly prescriptive** (graders noted this). Removal is arguably the better fix. The assertion should be broadened.

4. **The Isolated vs Fast tradeoff expectation (eval 7)** was missed by both configurations — both discussed Isolated vs Writable instead, which is the more natural tradeoff. The assertion appears misframed.

5. **The tradeoff analysis expectation (eval 4)** — both configurations failed the "Predictive + Inspiring synergy" assertion identically. The skill doesn't add tradeoff analysis beyond what the baseline provides.

## Verdict

The skill adds minimal measurable value over the baseline model on these evals. The +3.2pp improvement comes from 2 marginal assertions, at a 22.8% token cost. The core question for deciding whether to keep or delete this skill is whether the structured output format (Issue/Location/Impact/Fix) is valuable enough to justify the overhead, since detection quality is essentially equal.
