#!/usr/bin/env python3
"""transcripts: read Claude Code session transcripts (*.jsonl) for the eval and for fact checks.

usage:
  python3 transcripts.py questions DIR [--out candidates.jsonl]
      Candidate eval questions: what sessions looked up or asked (user questions, memory reads,
      grep/find/cat lookups), each with the next assistant reply. A person or agent then picks
      the real ones and writes the answer and the proof line.
  python3 transcripts.py evidence DIR NOTE.md
      For one note: its concrete tokens (code spans, paths, host:port, versions) and every
      transcript line that mentions them, oldest first, marked LIVE when it is a command result
      or a user message (ground truth) and SAID when it is only the assistant talking.
  python3 transcripts.py proof DIR "exact answer text"
      Transcript lines that contain the answer: use one as the proof of an eval question.

Transcript format: one JSON object per line with "type" (user/assistant), "timestamp" and
"message.content" (a string, or a list of text / tool_use / tool_result blocks)."""
import os
import re
import sys
import json
import glob
import argparse
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M

LOOKUP_RE = re.compile(r'\b(grep|rg|find|cat|ls|head|recall)\b')


def blocks(content):
    if isinstance(content, str):
        yield 'text', content, None
        return
    for c in content or []:
        t = c.get('type')
        if t == 'text':
            yield 'text', c.get('text', ''), None
        elif t == 'tool_use':
            inp = c.get('input') or {}
            yield 'tool_use', inp.get('command') or inp.get('file_path') or json.dumps(inp), c.get('id')
        elif t == 'tool_result':
            cc = c.get('content')
            if isinstance(cc, list):
                cc = '\n'.join(x.get('text', '') for x in cc if isinstance(x, dict))
            yield 'tool_result', cc or '', c.get('tool_use_id')


def events(tdir):
    for p in sorted(glob.glob(os.path.join(tdir, '**', '*.jsonl'), recursive=True)):
        for ln, raw in enumerate(open(p, encoding='utf-8', errors='replace'), 1):
            try:
                o = json.loads(raw)
            except ValueError:
                continue
            if o.get('type') not in ('user', 'assistant'):
                continue
            for kind, text, tid in blocks((o.get('message') or {}).get('content')):
                yield dict(file=os.path.relpath(p, tdir), line=ln, ts=o.get('timestamp', ''), role=o['type'], kind=kind, text=text, tid=tid)


def questions(tdir):
    out, pending = [], []
    for e in events(tdir):
        if e['role'] == 'user' and e['kind'] == 'text' and e['text'].strip().endswith('?'):
            pending.append(dict(src='%s:%d' % (e['file'], e['line']), ts=e['ts'], ask=e['text'].strip()[:300], reply=''))
        elif e['kind'] == 'tool_use' and (LOOKUP_RE.search(e['text']) or 'memory' in e['text'].lower()):
            pending.append(dict(src='%s:%d' % (e['file'], e['line']), ts=e['ts'], ask='LOOKUP: ' + e['text'][:300], reply=''))
        elif e['role'] == 'assistant' and e['kind'] == 'text':
            for p in pending:
                p['reply'] = e['text'][:500]
                out.append(p)
            pending = []
    return out


TOKEN_RE = re.compile(r'`([^`\n]{3,80})`|((?:/[\w.@+-]+){2,})|\b([\w.-]+:\d{2,5})\b|\bv?(\d+\.\d+\.\d+)\b|\bport (\d{2,5})\b')


def evidence(tdir, note_path):
    """Lines that share an exact token with the note, or two of its subject words.
    A command and its result are joined into one LIVE line: that is ground truth."""
    text = M.read(note_path)
    fm, fields, body = M.split_frontmatter(text)
    toks = set()
    for m in TOKEN_RE.finditer(text):
        toks.add(next(g for g in m.groups() if g))
    subject = set(M.words(fields.get('name', '') + ' ' + fields.get('description', '')))
    for t in toks:  # "curl localhost:8080/health" also means: localhost, health
        subject |= set(w for w in M.words(t.replace('/', ' ').replace(':', ' ')) if not w.isdigit())
    subject -= {'acme', 'app', 'note', 'notes', 'how', 'has', 'have', 'not', 'use', 'run'}
    cmds, hits = {}, []
    for e in events(tdir):
        if e['kind'] == 'tool_use':
            cmds[e['tid']] = e['text']
            continue
        txt, live = e['text'], (e['role'] == 'user' and e['kind'] == 'text')
        if e['kind'] == 'tool_result':
            txt, live = 'CMD: %s  =>  %s' % (cmds.get(e['tid'], '?'), e['text']), True
        found = [t for t in toks if t in txt]
        lw = set(M.words(txt))
        shared = sorted(subject & lw)
        if found or len(shared) >= 2:
            i = txt.find(found[0]) if found else 0
            hits.append('%s %s %s:%d [%s] %s' % (e['ts'][:19], 'LIVE' if live else 'SAID', e['file'], e['line'],
                                                 ', '.join(found[:3] or shared[:4]), txt[max(0, i - 120):i + 200].replace('\n', ' ')))
    return sorted(toks | subject), sorted(hits)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('mode', choices=['questions', 'evidence', 'proof'])
    ap.add_argument('dir')
    ap.add_argument('arg', nargs='?')
    ap.add_argument('--out')
    a = ap.parse_args()
    if a.mode == 'questions':
        qs = questions(a.dir)
        if a.out:
            with open(a.out, 'w') as f:
                for q in qs:
                    f.write(json.dumps(q) + '\n')
        for q in qs[:200]:
            print('%s %s\n   ask: %s\n   reply: %s' % (q['ts'][:10], q['src'], q['ask'][:160], q['reply'][:200].replace('\n', ' ')))
        print('%d candidates' % len(qs))
    elif a.mode == 'evidence':
        toks, hits = evidence(a.dir, a.arg)
        print('tokens: ' + ', '.join(toks))
        for h in hits:
            print(h)
        print('%d transcript lines' % len(hits))
    else:
        for e in events(a.dir):
            if a.arg in e['text']:
                live = (e['kind'] == 'tool_result') or (e['role'] == 'user' and e['kind'] == 'text')
                i = e['text'].find(a.arg)
                print('%s %s %s:%d %s' % (e['ts'][:19], 'LIVE' if live else 'SAID', e['file'], e['line'], e['text'][max(0, i - 100):i + 140].replace('\n', ' ')))
    return 0


if __name__ == '__main__':
    sys.exit(main())
