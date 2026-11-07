# Adapter: a plain folder of markdown notes

What the scripts expect:

- One folder (POOL) with one `.md` file per note at the top level.
- An index file in that folder, `MEMORY.md` by default (`--index NAME.md` for another name).
  Index lines look like `- [Title](note-file.md) — one-line description`.
- Optional frontmatter in each note: `name`, `description`, `type` (feedback / project / user / reference).
  Notes without frontmatter work too; the file name and first line stand in.
- Links between notes can be `[[note-name]]` or `[text](note-file.md)`.
- Sub-folders starting with `_archive` are archives. `topics/` holds topic pages (the dream writes them).

Transcripts: any folder of `*.jsonl` files in the Claude Code format (see `scripts/transcripts.py`).
If your agent logs another format, convert it to that shape first: one JSON object per line with
`type` (user or assistant), `timestamp`, and `message.content`.

Example:

```bash
python3 SKILL_DIR/scripts/audit.py /home/alex/notes --index INDEX.md --transcripts /home/alex/agent-logs
```

If several machines sync this folder, look for conflict copies first (`*.sync-conflict-*`,
"conflicted copy"): the audit lists them, and `references/schedule.md` shows how to stop new ones.
