# Implementation Plan: "Make it better"

## Problem: This Request Is Too Vague to Plan

The prompt "Make it better" does not provide enough information to create a useful implementation plan. "Better" is undefined — it could mean:

- Faster performance
- More readable code
- Better test coverage
- Improved documentation
- Simpler architecture
- More features
- Fewer bugs
- Better UX/DX

Without knowing what dimension of "better" to optimize for, any plan risks wasting effort on the wrong thing.

---

## What I Can See in the Codebase

This is a Claude Code plugin suite (`stepwise-dev`) with 4 plugins:
- **stepwise-core**: Research → Plan → Implement → Validate workflow skills
- **stepwise-git**: Git commit workflow
- **stepwise-web**: Web research agent
- **stepwise-research**: Multi-agent deep research

---

## Guesses at What "Better" Might Mean

Given the nature of the project, here are plausible interpretations ranked by likelihood:

### Option A: Better skill quality / prompt engineering
Improve the instructions in SKILL.md files to produce more consistent, higher-quality outputs.

### Option B: Better test coverage
The project has smoke tests for bash scripts but no automated tests for skills/agents. Add eval coverage.

### Option C: Better documentation
README files exist but may be outdated or incomplete.

### Option D: Better developer experience
Reduce friction in the install/update workflow.

---

## Recommended Next Steps

**Before planning, clarify the goal:**

1. What specific problem are you experiencing?
2. What does "better" mean in this context — quality, speed, coverage, UX?
3. Is there a specific skill, agent, or script that is underperforming?

---

## Provisional Plan (if forced to guess)

If I had to pick the highest-value improvement based on a quick codebase scan:

### Phase 1: Identify weak spots
- Run existing smoke tests: `make test`
- Review skill eval results in `*-workspace/` directories
- Check which skills have eval fixtures vs. which don't

### Phase 2: Improve lowest-coverage skills
- Add eval fixtures for under-tested skills
- Run manual tests in Claude Code

### Phase 3: Validate
- Re-run evals
- Compare before/after outputs

---

## Conclusion

This plan is speculative because the input was too vague. A better prompt would be:

> "Make the `create-plan` skill better at handling vague prompts"

or

> "Make the smoke tests better by adding edge case coverage"

**Recommendation: Ask the user what they actually want before investing in a plan.**
