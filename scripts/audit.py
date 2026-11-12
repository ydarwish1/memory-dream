#!/usr/bin/env python3
"""audit: measure a memory pool. Report only; it never writes into the pool.

usage: python3 audit.py POOL [--index MEMORY.md] [--findings findings.json] [--transcripts DIR] [--json OUT]

Reports: index size against the 200 line / 25 KB budget, note classes (rule / state / duplicate /
contradicted), verified markers, conflict copies, sync leftovers (.stversions, counted only), broken links, orphans (notes the index and topic
pages never mention), and, with --transcripts, how often each note was read."""
import os
import sys
import json
import glob
import argparse
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M


NAME_MAX = 150  # read back at most this many bytes before a '.md'
# Bytes a note file name may hold. Any other byte ends the name. translate() maps them to 'a' and the rest to ' '.
NAME_TABLE = bytes(0x61 if chr(b) in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_.-' else 0x20 for b in range(256))


def reads_from_transcripts(tdir, notes):
    """How often each note's file name appears in the transcripts.
    One pass per transcript: find each literal '.md', read the name back (up to NAME_MAX bytes), map it to a note
    once. Counting every note name in every transcript is one pass per note and does not finish on gigabytes; a
    name regex over the whole text backtracks on base64 image data and is as slow."""
    counts = dict((f, 0) for f in notes)
    memo = {}

    def note_of(name):
        if name not in memo:
            s, r = name.decode('utf-8', 'replace'), None
            if s in counts:
                r = s
            else:  # 'old_feedback_x.md' or '-feedback_x.md' still names feedback_x.md, as a substring count did
                for i, ch in enumerate(s):
                    if ch in '_-.' and s[i + 1:] in counts:
                        r = s[i + 1:]
                        break
            memo[name] = r
        return memo[name]

    for p in glob.glob(os.path.join(tdir, '**', '*.jsonl'), recursive=True):
        try:
            with open(p, 'rb') as fh:
                data = fh.read()
        except OSError:
            continue
        i = data.find(b'.md')
        while i != -1:
            start = max(0, i - NAME_MAX)
            j = start + data[start:i].translate(NAME_TABLE).rfind(b' ') + 1
            if j > 0 and data[j - 1:j] == b'\\':  # JSON escape before the name: \nname.md, \tname.md, —name.md
                j += 1 if data[j:j + 1] in (b'n', b't', b'r', b'b', b'f') else 5 if data[j:j + 1] == b'u' else 0
            if j < i:
                f = note_of(data[j:i + 3])
                if f:
                    counts[f] += 1
            i = data.find(b'.md', i + 3)
    return counts


def audit(pool, index='MEMORY.md', findings=None, transcripts=None):
    notes = M.load_pool(pool, index)
    lines, size = M.index_size(pool, index)
    dpairs = M.duplicate_pairs(notes)
    dups = dict((p['duplicate'], p['keep']) for p in dpairs)
    olds = M.series_old(notes)
    named = M.named_stale_map(notes)
    fnd = M.load_findings(findings)
    classes, reasons = {}, {}
    for f, n in notes.items():
        c, why = M.classify(f, n, dups, olds, named, fnd)
        classes[f], reasons[f] = c, why
    ext = [f for f, n in notes.items() if M.EXT_RE.search(n.body)]
    unmarked = [f for f in ext if not M.MARK_RE.search(notes[f].text)]
    marked = [f for f in notes if M.MARK_RE.search(notes[f].text)]
    referenced = set(os.path.basename(i['target']) for i in M.index_lines(pool, index))
    tdir = os.path.join(pool, 'topics')
    if os.path.isdir(tdir):
        for tf in os.listdir(tdir):
            if tf.endswith('.md'):
                for i in M.index_lines(tdir, tf):
                    referenced.add(os.path.basename(i['target']))
    orphans = sorted(f for f in notes if f not in referenced)
    rep = dict(
        pool=os.path.basename(os.path.abspath(pool)),
        index=dict(file=index, lines=lines, bytes=size, line_budget=M.INDEX_LINE_BUDGET, byte_budget=M.INDEX_BYTE_BUDGET,
                   over_budget=lines > M.INDEX_LINE_BUDGET or size > M.INDEX_BYTE_BUDGET),
        notes=len(notes),
        classes=dict((k, sum(1 for v in classes.values() if v == k)) for k in ('rule', 'state', 'duplicate', 'contradicted')),
        class_of=classes, reason_of=reasons,
        duplicates=dpairs, series_older=olds,
        verified_marked=len(marked), external_state_notes=len(ext), external_state_list=sorted(ext), external_state_unmarked=sorted(unmarked),
        conflict_copies=M.conflict_copies(pool),
        sync_leftovers=M.sync_leftovers(pool),
        broken_links=M.broken_links(pool, notes),
        orphans=orphans,
    )
    if transcripts:
        r = reads_from_transcripts(transcripts, notes)
        rep['reads'] = dict(sorted(r.items(), key=lambda kv: -kv[1]))
    return rep


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('pool')
    ap.add_argument('--index', default='MEMORY.md')
    ap.add_argument('--findings')
    ap.add_argument('--transcripts')
    ap.add_argument('--json')
    a = ap.parse_args()
    rep = audit(a.pool, a.index, a.findings, a.transcripts)
    if a.json:
        with open(a.json, 'w') as f:
            json.dump(rep, f, indent=1)
    i = rep['index']
    print('memory-dream audit: %s' % rep['pool'])
    print('  index      %d lines / %d bytes (budget %d / %d) %s' % (i['lines'], i['bytes'], i['line_budget'], i['byte_budget'],
                                                                     'OVER BUDGET' if i['over_budget'] else 'ok'))
    print('  notes      %d  -> rule %d, state %d, duplicate %d, contradicted %d' % (
        rep['notes'], rep['classes']['rule'], rep['classes']['state'], rep['classes']['duplicate'], rep['classes']['contradicted']))
    print('  markers    %d notes say verified / not re-checked; %d of %d machine-state notes have no marker' % (
        rep['verified_marked'], len(rep['external_state_unmarked']), rep['external_state_notes']))
    print('  conflicts  %d copies: %s' % (len(rep['conflict_copies']), ', '.join(rep['conflict_copies'])))
    for d, c in sorted(rep['sync_leftovers'].items()):
        print('  leftovers  %d files in %s (sync tool copies, not notes)' % (c, d))
    print('  links      %d broken' % len(rep['broken_links']))
    for b in rep['broken_links'][:20]:
        print('             %s -> %s' % (b['note'], b['link']))
    print('  duplicates %d pairs, %d older series entries' % (len(rep['duplicates']), len(rep['series_older'])))
    print('  orphans    %d notes nothing links to' % len(rep['orphans']))
    for f, c in sorted(rep['class_of'].items()):
        if c == 'contradicted':
            print('  CONTRADICTED %s: %s' % (f, rep['reason_of'][f]))
    if 'reads' in rep:
        top = [(f, c) for f, c in rep['reads'].items() if c][:5]
        print('  most read  ' + (', '.join('%s (%d)' % t for t in top) or '(no note names appear in the transcripts)'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
