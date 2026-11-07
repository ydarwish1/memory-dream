# Adapter: Claude Code auto memory

Where it lives (https://code.claude.com/docs/en/memory):

- Memory: `~/.claude/projects/<project>/memory/` with a `MEMORY.md` index and one file per memory.
  `<project>` comes from the git repository path, with `/` turned into `-`
  (for example `/home/alex/acme-app` becomes `-home-alex-acme-app`).
- Transcripts: `~/.claude/projects/<project>/*.jsonl`, one file per session.
- Only the first 200 lines or 25 KB of `MEMORY.md` load at session start.

Find the pools:

```bash
ls -d ~/.claude/projects/*/memory
wc -lc ~/.claude/projects/*/memory/MEMORY.md
```

Run the routines with:

- POOL = `~/.claude/projects/<project>/memory`
- TRANSCRIPTS_DIR = `~/.claude/projects/<project>` (the `*.jsonl` files next to `memory/`)

Notes:

- Each project has its own pool. Audit the ones the user cares about, or all of them and report a table.
- If the user keeps a shared pool elsewhere (one folder for every project), treat that folder as
  a plain folder (`adapters/plain-folder.md`) and pass every project folder's transcripts.
- Claude Code may clean up old transcripts after its retention period, so the eval can only use
  what is still on disk.
