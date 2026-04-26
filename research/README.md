# stepwise-research

Multi-agent deep research plugin for Claude Code with parallel web searches and synthesis.

## Overview

`stepwise-research` implements a sophisticated multi-agent research system inspired by Anthropic's Claude.ai Research feature. It orchestrates parallel web searches across multiple specialized agents, synthesizes findings, and produces comprehensive research reports with proper citations.

**Key Features:**
- 🤖 **Multi-agent orchestration** - Lead researcher spawns 1-6+ worker agents based on query complexity
- ⚡ **Parallel execution** - Workers search simultaneously for faster results
- 📚 **Comprehensive synthesis** - Cross-references findings from multiple sources
- 🔍 **Citation verification** - Dedicated agent ensures accuracy and completeness
- 📝 **Structured reports** - Markdown with YAML frontmatter, numbered citations, and metadata
- 💾 **Persistence** - Saves to `thoughts/` directory for future reference

## Architecture

Based on research showing that **multi-agent systems produce 90.2% better results** than single-agent approaches (Anthropic research).

### Components

1. **deep-research skill** (`/stepwise-research:deep-research`)
   - Main entry point
   - Orchestrates high-level workflow
   - Spawns lead agent and citation analyst

2. **research-lead agent**
   - Breaks query into sub-questions
   - Spawns research-worker agents in parallel
   - Synthesizes findings into coherent narrative
   - Detects gaps and spawns follow-up workers
   - Generates structured report

3. **research-worker agents** (1-6+ spawned per query)
   - Execute focused web searches (broad → narrow strategy)
   - Fetch and analyze source content
   - Return compressed findings with citations
   - Operate independently in separate contexts

4. **citation-analyst agent**
   - Maps claims to supporting sources
   - Verifies URL accessibility
   - Assesses source quality
   - Flags unsupported claims
   - Generates citation quality report

5. **generate-report script** (part of deep-research skill)
   - Formats reports with YAML frontmatter
   - Standardizes citation format
   - Integrates with `thoughts/` system

## Installation

```bash
# Add marketplace
/plugin marketplace add nikeyes/stepwise-dev

# Install plugin
/plugin install stepwise-research@stepwise-dev

# Restart Claude Code
```

**No additional configuration required!** The plugin uses Claude Code's built-in `WebSearch` and `WebFetch` tools.

## Usage

### Basic Usage

```bash
/stepwise-research:deep-research <research topic>
```

### Examples

**Simple query (1 worker, ~15 minutes):**
```bash
/stepwise-research:deep-research What is Docker and how does it work?
```

**Comparison query (2-3 workers, ~20-25 minutes):**
```bash
/stepwise-research:deep-research Compare React vs Vue.js for enterprise applications
```

**Complex research (4-6+ workers, ~30-40 minutes):**
```bash
/stepwise-research:deep-research Analyze the state of AI code generation tools in 2026
```

### What to Expect

1. **Clarification** (if needed): May ask 1-2 questions if topic is ambiguous
2. **Research phase**: Lead agent spawns workers, who search in parallel
3. **Synthesis**: Lead agent cross-references and synthesizes findings
4. **Verification**: Citation analyst checks accuracy
5. **Report generation**: Structured markdown saved to `thoughts/shared/research/`

### Output Structure

Reports are saved to:
```
thoughts/shared/research/[topic]-[date].md
```

Example report structure:
```markdown
---
title: Research on Docker Containerization
date: 2026-02-19
query: What is Docker and how does it work?
keywords: docker, containerization, virtualization, devops, deployment
status: complete
agent_count: 2
source_count: 12
---

# Research on Docker Containerization

## Executive Summary
[3-5 sentence overview]

## Detailed Findings

### Docker Architecture
[Synthesized findings with citations] [1] [2] [3]

### Container Runtime
[More findings] [4] [5]

## Conclusions
- [Key takeaway 1]
- [Key takeaway 2]
- [Key takeaway 3]

## Bibliography
[1] Docker Official Documentation - https://docs.docker.com/
[2] CNCF Container Whitepaper - https://...
...
```

## Worker Scaling

The lead agent automatically determines how many workers to spawn based on query complexity:

| Query Type | Workers | Example |
|------------|---------|---------|
| Simple definition | 1 | "What is Kubernetes?" |
| How-to guide | 1-2 | "How does JWT authentication work?" |
| Comparison (2 items) | 2-3 | "React vs Vue" |
| Comparison (3+ items) | 3-5 | "Top 5 databases compared" |
| State-of-the-art | 4-6 | "Current state of WebAssembly" |
| Multi-faceted analysis | 5-8 | "Enterprise AI adoption analysis" |

## Source Quality

Workers prioritize sources in this order:

**Tier 1 (Highest priority):**
- .gov, .edu domains
- Peer-reviewed journals
- Official documentation
- RFC documents

**Tier 2 (Industry standard):**
- Major tech company blogs
- Reputable tech publications
- Well-maintained project wikis

**Tier 3 (Community):**
- Personal blogs (expert authors)
- Conference talks
- Stack Overflow

**Tier 4 (Avoided):**
- SEO content farms
- Aggregators
- Low-quality forums

## Integration with Thoughts System

Reports integrate with the `stepwise-core` thoughts management system:

1. Reports saved to `thoughts/shared/research/`
2. Reports discoverable via `grep -r thoughts/shared/research/`
3. YAML frontmatter enables metadata-based searching

## Citation Quality

The citation-analyst agent ensures:
- ✅ All claims are supported by sources
- ✅ URLs are accessible
- ✅ Source quality is appropriate (prefer .gov, .edu)
- ✅ Multiple citations for major claims (2-3+)
- ✅ Bibliography is complete and formatted correctly

## Performance Characteristics

**Token Usage:**
- Research shows **token usage correlates with quality** (80% variance explained)
- Workers use 3-5 search iterations (broad → narrow)
- Each worker fetches 5-10 sources
- Lead agent performs comprehensive synthesis
- Total: ~50K-150K tokens depending on complexity

**Time Estimates:**
- Simple: 10-15 minutes
- Comparison: 20-25 minutes
- Complex: 30-45 minutes

*(Note: Actual time varies based on web search latency and source availability)*

**Cost Optimization:**
- Workers use Sonnet model (efficiency)
- Lead uses Opus model (synthesis quality)
- Parallel execution minimizes wall-clock time

## Limitations

- **Web-only research:** Does not access local files, databases, or proprietary sources
- **No multimedia analysis:** Text-only (no image, video, or audio analysis)
- **English bias:** Web search results may favor English sources
- **Recency:** Limited to publicly indexed web content
- **Rate limiting:** May hit WebSearch rate limits on very complex queries

## Troubleshooting

**Lead agent fails to spawn workers:**
- Check that `Task` tool is available
- Verify `WebSearch` and `WebFetch` are accessible (built-in tools)
- Try simpler query first

**Citation analyst reports many broken URLs:**
- May indicate sources behind paywalls or temporary outages
- Workers should automatically prefer accessible sources
- Consider re-running research with more specific query

**Report not saved to thoughts/:**
- Verify `thoughts/shared/research/` directory exists
- Create manually if needed: `mkdir -p thoughts/shared/research`
- Check write permissions

**Workers return low-quality sources:**
- Lead agent should detect this and spawn follow-up workers
- Consider refining query to be more specific
- Check if topic is too niche (limited high-quality sources available)

## Future Enhancements

Planned for future releases:
- Memory persistence across context truncations
- Recursive depth-first exploration for complex queries
- Multi-modal research (images, PDFs, videos)
- Custom source filters (allow/deny domains)
- Interactive refinement (mid-research questions)
- Research templates for common patterns

## Credits

Architecture inspired by:
- Anthropic's Claude.ai Research system
- Anthropic Cookbook multi-agent patterns
- Community implementations (claude-deep-research, deep-research)

Adapted for local-only operation in Claude Code CLI environment.

## License

Apache License 2.0 (see main repository LICENSE file)

## Links

- Main repository: https://github.com/nikeyes/stepwise-dev
- Issues: https://github.com/nikeyes/stepwise-dev/issues
- Marketplace: `/plugin marketplace add nikeyes/stepwise-dev`
