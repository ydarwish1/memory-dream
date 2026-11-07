#!/usr/bin/env python3
"""Template adapter for a custom memory store. Fill in list_notes, read_note and write_note.

usage: python3 custom_store.py export DIR
       python3 custom_store.py import DIR [--dry-run | --yes]"""
import os
import re
import sys
import json


def list_notes():
    """Return every note id in your store, e.g. database primary keys or API ids."""
    raise NotImplementedError('fill in list_notes() for your store')


def read_note(note_id):
    """Return the note text (markdown; frontmatter optional)."""
    raise NotImplementedError('fill in read_note() for your store')


def write_note(note_id, text):
    """Save the note text back to your store."""
    raise NotImplementedError('fill in write_note() for your store')


def safe_name(note_id):
    return re.sub(r'[^A-Za-z0-9._-]+', '_', str(note_id)).strip('_') or 'note'


def export(d):
    if os.path.exists(d):
        sys.exit('refusing: %s exists' % d)
    os.makedirs(d)
    ids, index = {}, ['# Memory index', '']
    for nid in list_notes():
        f = safe_name(nid) + '.md'
        text = read_note(nid)
        open(os.path.join(d, f), 'w', encoding='utf-8').write(text)
        ids[f] = nid
        first = next((l.strip() for l in text.splitlines() if l.strip() and not l.startswith('---')), '')
        index.append('- [%s](%s) — %s' % (f[:-3], f, first[:150]))
    open(os.path.join(d, 'MEMORY.md'), 'w', encoding='utf-8').write('\n'.join(index) + '\n')
    json.dump(ids, open(os.path.join(d, '.ids.json'), 'w'))
    print('exported %d notes to %s' % (len(ids), d))


def do_import(d, yes):
    ids = json.load(open(os.path.join(d, '.ids.json')))
    changed = []
    for f, nid in ids.items():
        p = os.path.join(d, f)
        if os.path.exists(p) and open(p, encoding='utf-8').read() != read_note(nid):
            changed.append((nid, p))
    print('%d notes changed' % len(changed))
    gone = [f for f in ids if not os.path.exists(os.path.join(d, f))]
    if gone:
        print('archived by the dream (not deleted from your store): ' + ', '.join(gone))
    if not yes:
        print('dry run; add --yes after the user agreed')
        return
    for nid, p in changed:
        write_note(nid, open(p, encoding='utf-8').read())
    print('imported %d notes' % len(changed))


if __name__ == '__main__':
    if len(sys.argv) < 3 or sys.argv[1] not in ('export', 'import'):
        sys.exit(__doc__)
    if sys.argv[1] == 'export':
        export(sys.argv[2])
    else:
        do_import(sys.argv[2], '--yes' in sys.argv)
