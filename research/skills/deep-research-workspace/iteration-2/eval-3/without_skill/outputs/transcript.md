# Research Transcript: PostgreSQL vs MySQL for High-Traffic Web Applications

**Date**: 2026-04-26
**Method**: Direct knowledge synthesis (no skill, no web search, no agents)
**Output**: report.md

---

## What Was Done

### 1. Task Setup
Received a research task: compare PostgreSQL vs MySQL for high-traffic web applications in 2025. The explicit constraint was to answer as Claude would normally, using training data only — no deep-research skill, no SKILL.md files, no generate-report script, no web fetching.

### 2. Output Directory Verification
Verified the target output directory existed:
- `/Users/jorge.castro/mordor/personal/stepwise-dev/research/skills/deep-research-workspace/iteration-2/eval-3/without_skill/outputs/`

The directory was empty and ready.

### 3. Research Synthesis from Training Data

All content in `report.md` was generated from Claude's training knowledge (cutoff early 2025). No external tools were used to gather information. The research covered:

**Architecture**: Reviewed the MVCC implementations in both databases, connection models (process-per-connection in PostgreSQL vs thread-per-connection in MySQL), and implications for high-traffic workloads.

**Performance**: Drew on knowledge of Percona, sysbench, and community benchmark patterns to characterize where each database excels — MySQL for simple high-throughput reads, PostgreSQL for complex queries and mixed workloads.

**Replication and HA**: Covered Patroni/repmgr/streaming replication for PostgreSQL and InnoDB Cluster/GTID/ProxySQL for MySQL. Addressed horizontal scaling solutions (Citus, Vitess/PlanetScale).

**Advanced Features**: Documented JSONB/GIN indexes, partitioning, index types, row-level security, transactional DDL, and pgvector (critical differentiator for AI workloads in 2025).

**Cloud Landscape**: Mapped managed service options for both databases across AWS, GCP, and Azure, noting the rise of PostgreSQL-compatible cloud databases (AlloyDB, Neon, CockroachDB).

**Real-World Usage**: Cited known production deployments — GitHub/Shopify/YouTube on MySQL+Vitess, Cloudflare/Spotify/Supabase on PostgreSQL.

**Decision Framework**: Synthesized findings into actionable guidance (when to choose each, summary table, conclusion).

### 4. File Creation
Wrote `report.md` directly using the Write tool. No intermediate drafts or external lookups.

---

## Approach Characteristics

| Attribute | Value |
|---|---|
| Information source | Claude training data (no web search) |
| Agents spawned | None |
| Tools used | Bash (directory check), Write (two files) |
| Research depth | Single-pass synthesis |
| Verification | None (no external sources consulted) |
| Time to complete | Single session, ~2 minutes |

---

## Limitations of This Approach

1. **No verification against current sources**: All facts reflect training data. Specific version numbers, benchmark figures, and product features may have changed since training cutoff.

2. **No citation of primary sources**: References listed in the report are representative pointers, not verified URLs retrieved at research time.

3. **No parallel research angles**: A skilled researcher would simultaneously explore multiple sub-questions (architecture, benchmarks, cloud, ecosystem) and synthesize. This report was written sequentially from memory.

4. **No gap analysis**: Without querying external sources, blind spots in training data are not detectable.

5. **Single perspective**: No cross-referencing of conflicting expert opinions or community debates (e.g., autovacuum tuning debates, Vitess vs Citus tradeoffs at edge cases).

---

## Notes for Evaluators

This transcript represents the "without skill" baseline for eval-3. The report reflects what Claude produces when answering a research question directly from training data in a single pass, without orchestration, parallel agents, web searches, or structured research prompts.

Comparison with the "with skill" output should focus on:
- Depth and coverage of topics
- Citation quality and verifiability
- Structure and completeness of the decision framework
- Presence of 2024–2025 specific developments (pgvector, Aurora performance, Neon/Supabase ecosystem)
- Accuracy of technical claims
