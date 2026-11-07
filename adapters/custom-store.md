# Adapter: a custom store (database, API, anything else)

The scripts work on a folder. For any other store, export it to a folder, run the routines, and
import the result after the user says yes.

Fill in the three functions in `adapters/custom_store.py`:

| Function | Returns | Used for |
|---|---|---|
| `list_notes()` | a list of note ids | export |
| `read_note(note_id)` | the note text (markdown, frontmatter optional) | export |
| `write_note(note_id, text)` | nothing | import (apply) |

Then:

```bash
python3 SKILL_DIR/adapters/custom_store.py export /tmp/acme-pool     # writes <id>.md files + MEMORY.md
python3 SKILL_DIR/scripts/audit.py /tmp/acme-pool
# ... eval and dream as usual, output in /tmp/acme-dream ...
python3 SKILL_DIR/adapters/custom_store.py import /tmp/acme-dream --dry-run
python3 SKILL_DIR/adapters/custom_store.py import /tmp/acme-dream --yes    # only after the user agreed
```

`import` writes back only notes whose text changed, plus the new index and topic pages if your
store can hold them (otherwise keep those as files next to the store and point the agent at them).
Archived notes are reported, not deleted: decide with the user what your store should do with them.
