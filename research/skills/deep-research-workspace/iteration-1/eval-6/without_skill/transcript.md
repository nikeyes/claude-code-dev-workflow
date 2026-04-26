# Transcript: Eval-6 Without Skill

## Task

Analyze the pros and cons of microservices vs monolith architectures for a growing startup.

## Approach

This evaluation was completed **without** using the `deep-research` skill or any multi-agent workflow. The answer was generated directly from the base model's knowledge in a single pass.

## Steps Taken

1. Checked whether the output directory existed (`/research/skills/deep-research-workspace/iteration-1/eval-6/without_skill/outputs`). The `outputs/` subdirectory did not exist, so it was created with `mkdir -p`.

2. Wrote the analysis directly from internal knowledge. No web searches, no sub-agents, no spawned tasks were used.

3. The report was structured as a balanced markdown document covering:
   - Monolith pros and cons (6 pros, 5 cons)
   - Microservices pros and cons (6 pros, 6 cons)
   - A decision framework table mapping team/product factors to architecture choice
   - A practical recommendation section
   - A summary comparison table

4. Saved the report to `outputs/report.md`.

5. Wrote this transcript to `transcript.md`.

## Observations

**What went well:**
- Fast to execute — single-pass generation with no coordination overhead.
- The answer draws on well-established industry knowledge (Martin Fowler, Sam Newman, and widely cited case studies from Netflix/Amazon/Uber) without needing to look anything up.
- The structure (pros/cons, decision table, recommendation) is clear and immediately useful.

**Limitations of this approach vs. using the deep-research skill:**
- No current sources or citations. The analysis is based on training data and may miss recent developments (e.g., new orchestration tooling, updated thinking from practitioners).
- No web verification. Claims like "Netflix started as a monolith" are based on well-known historical facts, but a research workflow would confirm and cite primary sources.
- No parallel exploration of subtopics. A multi-agent approach would simultaneously research scaling benchmarks, team structure studies, and migration case studies, then synthesize them. This single-pass answer is necessarily shallower.
- The framing is generic. A skilled researcher would ask clarifying questions about the specific startup context (team size, funding stage, tech stack, industry) before writing the analysis.

## Time and Effort

- Total wall-clock time: approximately 2 minutes.
- Tokens used: single inference pass for the report, plus this transcript.
- No tool calls beyond file writes and a directory existence check.
