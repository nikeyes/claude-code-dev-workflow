# Eval Transcript: deep-research "Research performance"

## Task
Invocation: `/stepwise-research:deep-research Research performance`

## What Happened

### Step 1: Read the Skill

I read the SKILL.md at `research/skills/deep-research/SKILL.md` and followed its workflow exactly.

### Step 2: Clarification Phase Triggered

The skill's Step 1 ("Clarification Phase") instructs:

> If the research topic is **ambiguous or unclear**, ask 1-2 clarifying questions using the AskUserQuestion tool.

"Performance" is highly ambiguous. It can refer to:
- Software/application performance
- Database performance
- Web/frontend performance
- System/infrastructure performance
- Human or organizational performance
- Business performance metrics
- Athletic performance
- Artistic/musical performance

The skill lists three criteria for **skipping** clarification:
1. Topic is explicit (e.g., "research Docker containerization security") — NOT met
2. User has provided clear context — NOT met
3. Query is self-contained — NOT met

**Conclusion: Clarification was required.**

### Step 3: Did I Spawn Workers Immediately?

**No.** I recognized the ambiguity and did NOT spawn any research workers.

Instead, I:
1. Identified the ambiguity in the topic "performance"
2. Formulated the questions I would ask via AskUserQuestion
3. Wrote those questions to `would_ask.md`
4. Stopped without proceeding to worker spawning

### What I Would Have Done Next

If the user had clarified (e.g., "software application performance"), I would have:
1. Determined query complexity (likely "state-of-the-art" or "multi-faceted analysis" → 4-6 workers)
2. Generated 4-6 focused sub-questions (e.g., profiling techniques, caching strategies, benchmarking, language/runtime performance comparisons, etc.)
3. Spawned all research workers in a single message for parallel execution
4. Synthesized findings into a structured report

## Verdict

The skill **correctly guided** recognizing ambiguity before spawning workers. The clarification-first behavior was followed exactly as specified in the skill's Step 1 instructions. No workers were spawned prematurely.

| Behavior | Expected | Actual |
|---|---|---|
| Recognize ambiguity | Yes | Yes |
| Ask clarifying questions | Yes (via AskUserQuestion) | Yes (written to would_ask.md) |
| Spawn workers immediately | No | No |
| Stop before research | Yes | Yes |
