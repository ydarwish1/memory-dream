---
name: memory-dream
description: Audit, measure and clean up an AI agent's memory the way Anthropic's research "The components of agent memory" describes (dreaming). Measures the index against Claude Code's 200-line / 25 KB load limit; finds stale, duplicate, contradicted and conflict-copy notes and broken links; builds an eval from your own transcripts; runs a dream pass on a copy; applies it only after you say yes, with a backup. Use when the user says "audit my memory", "dream", "run a dream pass", "clean up agent memory", "is my memory stale", "my MEMORY.md is too long", "memory conflict copies", or wants to know whether their memory actually helps.
license: MIT
---

# memory-dream

## References (read these first)

- Anthropic, "The components of agent memory": https://www.anthropic.com/research/components-of-agent-memory — the research this skill applies (memory as prediction, small beats big, dreaming, wikis, the injected layer).
- Claude Cookbook, "Dreaming with a dynamic workflow": https://platform.claude.com/cookbook/managed-agents-cma-dreaming-with-a-dynamic-workflow — Anthropic's own dream pass over session transcripts, linked from the article.
- Claude quickstart "knowledge-wiki": https://github.com/anthropics/claude-quickstarts/tree/main/managed-agents/knowledge-wiki — turning a corpus into a linked wiki, linked from the article.
- Claude Code memory docs: https://code.claude.com/docs/en/memory — auto memory lives in `~/.claude/projects/<project>/memory/`; only the first 200 lines or 25 KB of `MEMORY.md` load at session start.
- Lin et al. 2025, "Sleep-time Compute: Beyond Inference Scaling at Test-time": https://arxiv.org/abs/2504.13171 — the idea of thinking offline between sessions (the article credits Letta and UC Berkeley).
- Managed Agents "Dreams" docs: https://platform.claude.com/docs/en/managed-agents/dreams and the memory tool: https://platform.claude.com/docs/en/agents-and-tools/tool-use/memory-tool — the hosted versions of the same ideas.
- Karpathy, "LLM Wiki": https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f — the wiki pattern the article cites.
- `references/research.md` — every research fact this skill uses, with its number and source.
- `references/note-format.md` — what makes a note worth keeping.
- `references/formats.md` — the two JSON files you write (topics, findings) and the eval question format.
- `references/schedule.md` — a plan for a recurring dream pass with one writer.

All links above were opened and loaded when this skill was published.

## What memory is for

Memory is a bet that something will matter again. It pays off when it holds what a session worked out and could not read off the machine again: tested rules, traps, decisions, how to check a thing, and how the user likes to work. Live state (ports, versions, "X is deployed") goes stale; a note about it is worth most when it says how and when it was checked. Transcripts are the ground truth. When a note and a live check disagree, the live check wins and the note gets fixed.

This skill does not tell anyone how to write notes. The research found fixed writing rules made strong models worse. It measures the memory, checks it, and reorganises it.

## Ground rules

- Every routine reads the live memory and writes only to a copy, except `apply`, which runs only after the user says yes in this conversation, and makes a backup first.
- Nothing is deleted. Duplicates, conflict copies and old index files move into `_archive-dream-<date>/` inside the pool, which no routine reads as live notes.
- Live checks are read-only commands (`ssh host hostname`, `curl -s .../health`, `test -e path`). Never print secrets; check that a key exists, not its value.
- Scripts are deterministic and offline. The judgement (is this note still true?) is yours, written into `findings.json`.

`SKILL_DIR` below means the folder that holds this file. Python 3.8+ is the only requirement.

## Find the memory first

Pick the adapter that matches the user's setup and read it:
- Claude Code auto memory (`~/.claude/projects/*/memory/` with a `MEMORY.md`): `adapters/claude-code.md`
- A plain folder of markdown notes with an index file: `adapters/plain-folder.md`
- Anything else (a database, an API, a different file layout): `adapters/custom-store.md`

Every routine below takes a POOL folder. For a custom store, export it to a folder first.

## Routine 1: audit (report only)

```bash
python3 SKILL_DIR/scripts/audit.py POOL --transcripts TRANSCRIPTS_DIR --json /tmp/memory-audit.json
```

It reports: index lines and bytes against 200 / 25 KB; each note's class (rule, state, duplicate, contradicted: a note is "contradicted" only when your findings.json or another note says so; the transcripts are evidence you judge in the dream); how many notes carry a "verified" or "not re-checked" marker; the machine-state notes (`external_state_list` in the JSON) and which of them have no marker; conflict copies (`*.sync-conflict-*`, "conflicted copy"); sync leftovers (files Syncthing keeps in `.stversions/`, counted only, never read as notes); broken `[[links]]` and markdown links; orphans (notes nothing points to); and, with transcripts, how often each note was read.

Tell the user the numbers in plain words. The class labels are rules of thumb (hand checks agree with them about 6 to 8 times in 10): spot-check ten notes and say how many you agree with.

## Routine 2: eval (score the baseline)

Read `eval/build-eval.md`. In short:
1. `python3 SKILL_DIR/scripts/transcripts.py questions TRANSCRIPTS_DIR --out /tmp/candidates.jsonl` lists what past sessions looked up or asked.
2. Pick 20–40 real ones. For each, write the true answer as key strings and the transcript line that proves it (`transcripts.py proof DIR "answer"`). Prefer LIVE lines (a command result or the user's own words) over the assistant's text.
3. Hold out a quarter at random before you change anything. Do not tune on them.
4. `python3 SKILL_DIR/scripts/score.py POOL questions.json --split dev` and `--split heldout --quiet` (so you do not see the held-out rows) give accuracy, hit@3 and tokens. That is the baseline. Add `--kind transcript` to score only the questions proven by a session.

`score.py` uses `recall.py`, a cheap index-first lookup, so the score measures how findable the facts are, the same way before and after.

## Routine 3: dream (on a copy)

1. **Check the notes that can go stale.** For every note the audit calls state or contradicted, and every note about a machine or an outside service:
   - `python3 SKILL_DIR/scripts/transcripts.py evidence TRANSCRIPTS_DIR POOL/<note>.md` shows the transcript lines about it, oldest first, LIVE or SAID.
   - Run one read-only live check where you can.
   - Write the verdict into `findings.json` (format in `references/formats.md`): `stale` (with evidence and what is true now), `verified` (with the check you ran), `rewrite` (with the corrected text), or `unconfirmed` (the evidence is too weak either way).
   - Start with the notes that are read most often (audit `reads`). Do not re-check everything: aim the work at facts that change. If every read count is 0 (transcripts that never name note files), start with the state notes and the notes about machines.
   - Run a live check only on machines the user owns and you can reach safely. If you cannot (someone else's servers, no access), rest the verdict on LIVE transcript lines and say so in the evidence.
2. **Write `topics.json`:** 4–20 topics that fit this user's work, each with words that file notes under it, and a short list of facts you checked, each naming its check and date (a live command today, or a LIVE transcript line).
3. **Run the pass** (any scratch folder works; the examples use /tmp):
   ```bash
   python3 SKILL_DIR/scripts/dream.py POOL /tmp/memory-dream-out --topics topics.json --findings findings.json
   ```
   It copies the pool, archives conflict copies and duplicates, applies your findings, marks unmarked state notes "not re-checked", repairs links that are one typo off, writes one topic page per topic, and writes a short `MEMORY.md` (what memory is for, goals, one line per topic). The output folder must be new. `--date` defaults to today; keep that on a real memory.
   Next to the output it writes `OUT.summary.md` (read it first), `OUT.diff` (every changed note), `OUT.report.json`, and `OUT.base.json` (used by apply).
   If the summary lists a conflict copy that differs from its live note, read both and ask the user which is right before you apply. The pass keeps the live note.
4. **Re-run the eval** on the output, dev split and held-out split separately:
   `python3 SKILL_DIR/scripts/score.py /tmp/memory-dream-out questions.json --split heldout`
5. **Show the user:** before and after numbers, `/tmp/memory-dream-out.diff`, and the list of notes found stale. A held-out gain you can show is the result; a miss with honest numbers is also a result.

## Routine 4: apply (only after the user says yes)

```bash
python3 SKILL_DIR/scripts/apply.py POOL /tmp/memory-dream-out          # dry run: what would change
python3 SKILL_DIR/scripts/apply.py POOL /tmp/memory-dream-out --yes    # backup, then swap
```

It writes a `.tgz` backup of the live pool first. A live file that changed since the dream started is kept, not overwritten. Re-run the audit afterwards and compare.

Claude Code note: the harness reads `MEMORY.md` as an index, and the agent opens topic pages and notes on demand, so the new layout works without extra tools.

## Routine 5: schedule (a plan; the user installs it)

Read `references/schedule.md` and write the user a plan: one machine (or one job) is the only writer of `MEMORY.md` and the topic pages; other writers add note files and a per-machine inbox only; a nightly or weekly pass runs routines 1–3 plus the live checks, with cadence set by how often each note is read; the eval runs each time and the pass rolls back if accuracy drops. Give paste-ready steps; do not install a scheduler yourself.

## Try it on the fixture first

```bash
python3 SKILL_DIR/eval/fixture/generate.py
python3 SKILL_DIR/scripts/audit.py SKILL_DIR/eval/fixture/pool --transcripts SKILL_DIR/eval/fixture/transcripts
python3 SKILL_DIR/scripts/dream.py SKILL_DIR/eval/fixture/pool /tmp/fixture-dream --topics SKILL_DIR/eval/fixture/example-topics-checked.json --findings SKILL_DIR/eval/fixture/example-findings.json --date 2025-03-15
python3 SKILL_DIR/scripts/fixture_judge.py SKILL_DIR/eval/fixture /tmp/fixture-dream
```

The judge grades the run against `eval/fixture/answer-key.json`.

## Before publishing anything built with this skill

`python3 SKILL_DIR/scripts/privacy_scan.py FOLDER --words /path/outside/the/folder/private-words.txt` fails on names, emails, home paths, IP addresses, key-shaped strings and any word in your private list. Keep that list outside the folder you publish.
