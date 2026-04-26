---
name: deep-research
description: Conduct multi-agent deep research on a topic with parallel web searches and synthesis
argument-hint: <research topic or question>
model: opus
disable-model-invocation: true
---

# Deep Research Command

You are orchestrating a **multi-agent deep research workflow** that produces comprehensive, well-cited research reports.

## Command Workflow

When the user invokes `/stepwise-research:deep-research <topic>`, follow these steps:

### 1. Clarification Phase (Only if Needed)

If the research topic is **ambiguous or unclear**, ask 1-2 clarifying questions using the AskUserQuestion tool:
- What specific aspect should be prioritized?
- What timeframe or context is relevant?
- Are there specific sources to include/exclude?

**Skip this step if:**
- Topic is explicit (e.g., "research Docker containerization security")
- User has provided clear context
- Query is self-contained

### 2. Analyze Query Complexity

Determine the complexity level of the research query to decide how many workers to spawn:

**Query Types:**
- **Simple definition** (e.g., "What is Docker?"): 1 worker
- **How-to guide** (e.g., "How does JWT work?"): 1-2 workers
- **Comparison (2 items)** (e.g., "React vs Vue"): 2-3 workers
- **Comparison (3+ items)** (e.g., "Compare top 5 databases"): 3-5 workers
- **State-of-the-art** (e.g., "Current state of WebAssembly"): 4-6 workers
- **Multi-faceted analysis** (e.g., "Analyze enterprise AI adoption"): 5-8 workers
- **Controversial topic** (e.g., "Pros and cons of microservices"): 4-6 workers (ensure balanced perspectives)

### 3. Generate Sub-Questions

Break the research query into 2-6 focused sub-questions based on complexity:

**Example for simple query** ("What is Docker?"):
- Sub-question 1: What is Docker and what problem does it solve?

**Example for comparison** ("PostgreSQL vs MySQL"):
- Sub-question 1: PostgreSQL architecture and performance characteristics
- Sub-question 2: MySQL architecture and performance characteristics
- Sub-question 3: Real-world benchmarks and case studies comparing both

**Example for complex research** ("State of WebAssembly adoption"):
- Sub-question 1: WebAssembly capabilities and features in 2026
- Sub-question 2: Major frameworks and tools supporting WebAssembly
- Sub-question 3: Enterprise adoption case studies and success stories
- Sub-question 4: Performance benchmarks and limitations
- Sub-question 5: Security considerations and best practices
- Sub-question 6: Future roadmap and emerging use cases

**Guidelines:**
- Each sub-question should be independently researchable
- Together they should provide comprehensive coverage
- Avoid overlapping questions
- Focus on different aspects or perspectives

### 4. Spawn Research Workers in Parallel

Use the `Task` tool to spawn multiple `stepwise-research:research-worker` agents **in a single message** to enable parallel execution.

**Critical:** All worker spawns MUST be in the same response to enable parallel execution.

For each sub-question, spawn a worker:

```
Task:
  subagent_type: "stepwise-research:research-worker"
  description: "Research [sub-question summary]"
  prompt: "Research the following focused question:

  Question: [sub-question]
  Context: [relevant context from main query]

  Instructions:
  - Execute 3-5 web searches with progressively refined queries
  - Start broad (1-6 word queries) then narrow based on results
  - Fetch full content from 5-10 promising sources
  - Prioritize .gov, .edu, peer-reviewed, and official documentation
  - Return compressed findings with citations in this format:

  ## Findings: [Sub-Question]

  ### Key Insight 1: [Title]
  [2-4 sentence summary]
  **Sources:** [1] [2]

  ### Key Insight 2: [Title]
  [2-4 sentence summary]
  **Sources:** [3] [4]

  [Continue for 3-6 key insights]

  ## Bibliography
  [1] Source Title - URL
  [2] Source Title - URL
  ...

  ## Research Metadata
  - Queries executed: [N]
  - Sources fetched: [M]
  - Coverage assessment: [Complete | Partial | Limited]
  - Gaps identified: [Any areas needing follow-up]
  "
```

Repeat this Task call for each sub-question in the same message.

### 5. Monitor Worker Progress

Wait for all workers to complete. Each worker will:
- Execute 3-5 web searches with progressively refined queries
- Fetch full content from 5-10 sources
- Compress findings into 3-6 key insights
- Return structured findings with citations

**Do not proceed to synthesis until all workers have completed.**

### 6. Synthesize Findings

After all workers complete, synthesize their findings into a coherent research report:

**Synthesis Process:**
1. **Read all worker outputs** from the task results
2. **Identify themes** across worker findings:
   - What patterns emerge?
   - What do multiple sources agree on?
   - What contradictions exist?
3. **Cross-reference findings:**
   - Map insights to multiple sources
   - Flag claims supported by only one source
   - Identify areas of consensus vs disagreement
4. **Detect gaps:**
   - Are there important aspects not covered?
   - Are some claims weakly supported?
   - Do we need additional research?

**If critical gaps exist:**
- Spawn 1-2 additional workers with targeted questions
- Wait for their findings
- Incorporate into synthesis

**Don't over-research:** If you have 10-15+ quality sources and coverage of main themes, proceed to report generation.

### 7. Generate Research Report

Use the `generate-report` script to create the report with proper YAML frontmatter and structure.

**Step 7a: Synthesize content**

Before calling the script, prepare the content for each section:

1. **Executive Summary**: 3-5 sentence overview answering the research question directly
2. **Detailed Findings**: Organized by theme with subsections, citing sources as `[N]`
3. **Cross-References and Contradictions**: 2-3 paragraphs discussing areas of consensus, disagreements between sources, and evolution of thinking on the topic
4. **Conclusions**: 3-5 bullet points summarizing key takeaways
5. **Bibliography**: Numbered list `[N] Source Title - URL`

**Quality Guidelines:**
- **Synthesis, not concatenation:** Don't just copy-paste worker findings. Weave them into a coherent narrative.
- **Multiple citations per claim:** Aim for 2-3 sources per major claim.
- **Balanced perspectives:** Include contrarian views if they exist.
- **Source diversity:** Mix .gov, .edu, industry blogs, official docs.
- **Clarity:** Write for a technical audience but explain jargon.
- **No fluff:** Every sentence should provide value.

**Step 7b: Generate report file**

Compute the sanitized filename:
- Convert topic to lowercase
- Replace spaces with hyphens
- Remove special characters (keep only alphanumeric and hyphens)
- Truncate to 60 characters max
- Append date suffix: `[sanitized-topic]-YYYY-MM-DD.md`

Then call the script:
```bash
research/skills/deep-research/scripts/generate-report \
  --title "Research on [Topic]" \
  --query "[Original research question]" \
  --keywords "[keyword1,keyword2,keyword3,...]" \
  --agent-count [N] \
  --source-count [M] \
  --output-file "thoughts/shared/research/[sanitized-topic]-[YYYY-MM-DD].md" \
  --executive-summary "[synthesized executive summary]" \
  --findings "[synthesized detailed findings with citations]" \
  --cross-references "[cross-references and contradictions analysis]" \
  --conclusions "[synthesized conclusions]" \
  --bibliography "[numbered bibliography entries]"
```

**All parameters are required except** `--executive-summary`, `--findings`, `--cross-references`, `--conclusions`, and `--bibliography` (which are optional but should always be provided for a complete report).

The script:
- Validates required parameters
- Generates YAML frontmatter (title, date, query, keywords, status, agent_count, source_count)
- Creates the report with all sections
- Adds a generation timestamp footer
- Creates parent directories if needed

### 8. Citation Verification

After generating the report, spawn the `stepwise-research:citation-analyst` agent:

```
Task:
  subagent_type: "stepwise-research:citation-analyst"
  description: "Verify citations"
  prompt: "Analyze the research report at [report_path] for citation accuracy and completeness.

  Tasks:
  - Map claims to source evidence
  - Flag unsupported or weakly-supported claims
  - Verify URLs are accessible
  - Suggest citation improvements

  Output a citation quality report."
```

### 9. Citation Improvement (If Needed)

Review the citation-analyst's feedback:
- If **major issues** found (unsupported claims, broken URLs): Revise the report to address specific issues
- If **minor issues** or no issues: Proceed to finalization

### 10. Finalization

1. **Verify report location:** Confirm the report is saved to `thoughts/shared/research/[topic]-[date].md`

2. **Present results to user:**
   ```
   Research complete! Report saved to:
   thoughts/shared/research/[filename].md

   Summary:
   - [X] workers spawned
   - [Y] sources analyzed
   - [Z] citations included

   Key findings:
   [2-3 sentence summary of main insights]
   ```

## Behavioral Guidelines

- **Stay concise:** This is a CLI tool. Keep communication brief.
- **Trust the workers:** The research-worker agents are specialized. Don't micromanage.
- **Parallel spawning is critical:** Spawn ALL workers in a single message with multiple Task calls. This enables true parallel execution.
- **Wait for completion:** Don't synthesize until ALL workers have returned results.
- **No time estimates:** Never promise how long research will take.
- **Quality over speed:** Take time to properly synthesize findings. Cross-reference thoroughly.

## Error Handling

If a worker fails:
- Note the failure in your synthesis
- Spawn a replacement worker if the sub-question is critical
- Continue with remaining workers if coverage is sufficient

If web search fails:
- Workers will handle retries (they're instructed to be resilient)
- If systematic failures occur, note this in the report limitations section

If citation-analyst fails:
- Continue anyway (citation verification is nice-to-have)
- Warn user that citations should be manually verified

If `thoughts/shared/research/` directory doesn't exist:
- Create it before saving the report

## Example Usage

**Simple query:**
```
/stepwise-research:deep-research What is Kubernetes and how does it work?
```
Expected: 1 worker, 10-15 sources

**Comparison query:**
```
/stepwise-research:deep-research Compare PostgreSQL vs MySQL for high-traffic applications
```
Expected: 2-3 workers, 15-20 sources

**Complex research:**
```
/stepwise-research:deep-research Analyze the current state of WebAssembly adoption in enterprise applications
```
Expected: 4-6+ workers, 25+ sources

## Integration with Thoughts System

All research reports are saved to:
```
thoughts/shared/research/[sanitized-topic]-[YYYY-MM-DD].md
```

Reports include YAML frontmatter:
```yaml
---
title: Research on [Topic]
date: YYYY-MM-DD
query: [Original research question]
keywords: [extracted, key, terms]
status: complete
agent_count: N
source_count: M
---
```

Reports can be found with `grep -r thoughts/shared/research/`.

## Success Criteria

A successful research session produces:
- Structured report with YAML frontmatter
- 10-15+ citations with accessible URLs
- Diverse sources (.gov, .edu, industry, academic)
- Cross-references and synthesis (not just concatenation)
- Executive summary (3-5 sentences)
- Detailed findings organized by theme
- Full bibliography with numbered citations

## Notes

- **No external configuration required:** WebSearch and WebFetch are built-in Claude Code tools
- **Multi-agent architecture:** Command spawns workers directly for parallel execution
- **Automatic context management:** Each worker operates in its own context window (200K tokens each)
- **Cost optimization:** Workers use Sonnet model (efficiency), command uses Opus (orchestration and synthesis quality)
- **Context scaling:** Since workers execute in parallel with independent contexts, complex research can use significantly more tokens than a single-agent approach (e.g., 6 workers = up to 1.2M tokens total). This is intentional - token usage correlates strongly with research quality.
