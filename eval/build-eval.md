# Build an eval from your own transcripts

The eval answers one question: when a session needs a fact, does the memory hand it over?
Build it from what sessions really needed, not from what you guess they need.

## 1. Collect candidates

```bash
python3 SKILL_DIR/scripts/transcripts.py questions TRANSCRIPTS_DIR --out /tmp/candidates.jsonl
```

Each candidate is a user question or a lookup a session ran (grep, find, cat, a memory read),
with the reply that followed. Good picks: a path, a port, a price, a decision, a how-to, a
machine fact, a preference. Skip opinions and one-off chatter.

## 2. Write each question

For each pick, write an entry in `questions.json` (format in `references/formats.md`):

- `query`: the words the session searched for, or the question in short words. If the real
  query contains the answer itself, drop those words and say so in a `note` field.
- `keys`: short strings that must appear in a correct answer (`"9090"`, `"ssh staging"`).
- `proof`: the transcript line that shows the answer is true. Find it with
  `python3 SKILL_DIR/scripts/transcripts.py proof TRANSCRIPTS_DIR "9090"`.
  Prefer LIVE lines (a command result, or the user's own words). If the newest LIVE line
  disagrees with an older one, the newest wins: facts change.
- Run one live read-only check for machine facts. If today's value differs from the transcript,
  use today's value and write down both.

Aim for 20–40 questions. Fewer than 10 gives numbers too noisy to act on.

If the transcripts are thin (only a few real lookups), use every one of them, then add
regression questions whose proof is a note ("this fact must stay findable after the dream").
Mark those with `"proof": "note: <file>"` and report the two kinds separately: only the
transcript-backed questions say anything about real need.

## 3. Hold some out

Before you change anything, mark a random quarter `"split": "heldout"` (use a fixed seed and
write it down). Do not look at the held-out questions while you dream. Report them separately.

Honest limit: if you wrote the questions yourself, the held-out set is not blind to you. For a
blind check, draw a few more questions after the dream is frozen, label them, and score both
the old and the new pool on them.

## 4. Score

```bash
python3 SKILL_DIR/scripts/score.py POOL questions.json --split dev
python3 SKILL_DIR/scripts/score.py POOL questions.json --split heldout
```

- accuracy: every key appears in what the lookup printed
- hit@3: one of the top-3 files holds every key
- tokens: printed characters / 4, an estimate (compare runs only on the same machine and paths,
  because file paths in the output count too)
