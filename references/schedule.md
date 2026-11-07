# A recurring dream pass (plan template)

Write this plan for the user and let them install it. Fill in their machines, folders and times.

## One writer per file

| File | Its only writer |
|---|---|
| `MEMORY.md` and `topics/<topic>.md` | the dream job |
| `topics/_inbox-<machine>.md` | that machine (new notes add one line here, not to `MEMORY.md`) |
| a new note file | the machine that wrote it (unique file name) |
| a correction to an existing note | the dream job |

A sync tool makes a conflict copy only when two devices change the same file between two syncs.
When each file has one writer, that cannot happen. The audit counts conflict copies, so the plan
can prove it: the target is 0 new copies for 7 runs in a row.

If several machines share one pool, pick one to run the job. The others send new note files and
their inbox to it before the run, and take the job's files back after it. A file a machine changed
since the last sync is never overwritten by the pull; it goes up on the next push instead.

## Each run

1. Snapshot the pool (keep 7).
2. Take in new notes and inbox lines; file them onto topic pages.
3. `audit.py` with `--transcripts` for the read counts.
4. Live checks, most-read notes first: a small file of `{fact, command, expected}` read-only
   checks. A failed check stamps "CHECK FAILED <date>" on the fact instead of silently rewriting it.
5. Rebuild `MEMORY.md`; fail if over 200 lines or 25 KB.
6. Repair links; list the rest.
7. `score.py` on the saved question sets. If accuracy drops 5 points or more, restore the
   snapshot's index and topic pages.
8. Write a short dream log: counts, failed checks, eval numbers, conflict copies.

## Cadence by reads

| Read in the last 7 days | Read in the last 30 days | Not read in 30 days |
|---|---|---|
| check nightly | check weekly | check monthly |

Count reads from transcripts (`audit.py --transcripts`): a note that sessions open often is worth
re-checking often; one nobody opens can wait.

## What to give the user

- The scheduler entry (cron, systemd timer, launchd, Task Scheduler) as a paste-ready block.
- Where the logs go and how to read the newest one.
- How to turn it off and how to restore the last snapshot.
