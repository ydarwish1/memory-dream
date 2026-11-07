# The research facts this skill uses

Source for all facts unless noted: Anthropic, "The components of agent memory",
https://www.anthropic.com/research/components-of-agent-memory

| # | Fact | Number | What the skill does with it |
|---|---|---|---|
| 1 | A memory note is a prediction that a pattern will matter again. The best notes record the rule, how it was verified, and traps. Notes that copy live state go stale. | CL-Bench mean reward, no memory → with memory: Opus 5 0.564 → 0.828, Opus 5.5 0.655 → 0.838, Sonnet 4.6 0.330 → 0.364 | `audit` separates tested rules from live-state copies; `dream` marks state notes "verified <date>" or "not re-checked". |
| 2 | Small beats big. One model wrote everything down and spent its turns reorganising notes instead of acting. | Sonnet 3.7: 413 files in 225 folders, 977,930 characters, 1 badge. Fable 5: 10 files (one `global.md` dashboard), 43,406 characters, 4 badges | `dream` merges duplicates, archives superseded entries, and keeps the index short. |
| 3 | Say what memory is for, not how to write it. Fixed rules hurt strong models. | "Record only failures" cut the memory gain by 0.234 (Opus 5), 0.150 (Opus 4.7), 0.020 (Sonnet 4.6) | The skill never adds note-writing rules; the index states what memory is for. |
| 4 | Dreaming: an offline pass that checks notes against the original transcripts and corrects them. The transcript is the ground truth. | One corrected note (Mt. Moon) let a stuck run reach Cerulean City at action 1,935; with the raw note it never did | `dream` step 1: check notes against transcripts and one live read-only command; write findings. |
| 5 | A wiki (linked pages) plus search beats search alone when an answer needs several sources, and saves tokens. It gives no gain on single-document lookups, and a wiki can grow bigger than its sources. | Harvey LAB: 87% vs 73% (multi-document); Stainless: 61% vs 53%, about 20,000 fewer tokens per question; one wiki grew to 1.77x its 115 KB corpus | `dream` writes topic pages (a small wiki) that point at the notes; `score.py` measures tokens so bloat shows up. |
| 6 | The injected top layer must stay small. Dreaming pushes detail down and leaves a link. | Claude Code loads only the first 200 lines or 25 KB of `MEMORY.md` (https://code.claude.com/docs/en/memory) | `audit` checks the budget; `dream` rewrites the index to one line per topic and fails if it is over. |
| 7 | One writer per page. Agents writing one shared table at once overwrote each other. | 41 of 57 facts kept (shared table) vs 57 of 57 (one agent per page, terms quoted word for word) | `audit` finds conflict copies; `schedule` plans one writer for the index and per-machine inboxes. |
| 8 | A pass across many sessions fixes what one session cannot see: broken links, duplicates, missing index pages. | 9 links to a missing page repointed; wiki went from 38 entries / 225 links to 41 / 278 | `dream` repairs links one typo away and adds topic pages; the rest are listed for a person. |
| 9 | Dreaming costs compute. Aim it at facts likely to change, and set the cadence by how often a note is read. | (design guidance, no number) | `audit --transcripts` counts reads; `schedule` sets nightly / weekly / monthly checks by read count. |

Background: Lin et al. 2025, "Sleep-time Compute: Beyond Inference Scaling at Test-time", https://arxiv.org/abs/2504.13171
(the article credits Letta and UC Berkeley for the idea of using idle time to think ahead).
