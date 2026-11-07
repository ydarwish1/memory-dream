#!/usr/bin/env python3
"""apply: swap the dreamed copy into the live pool. Run it only after the user says yes.

usage: python3 apply.py LIVE DREAMED --yes [--backup-dir DIR]

Needs DREAMED.base.json (written by dream.py): the live pool's checksums when the dream started.
 - First it writes a tar.gz backup of LIVE (default: next to LIVE).
 - A live file that changed or appeared since the dream started is KEPT as it is (someone wrote it).
 - Every other file takes the dreamed version.
 - A top-level note the dream moved into its archive is MOVED there in LIVE too. Nothing is deleted.
Without --yes it only prints what it would do."""
import os
import sys
import json
import shutil
import tarfile
import argparse
import datetime
sys.dont_write_bytecode = True  # keep the skill folder clean
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import memlib as M


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('live')
    ap.add_argument('dreamed')
    ap.add_argument('--yes', action='store_true')
    ap.add_argument('--backup-dir')
    a = ap.parse_args()
    live, new = os.path.abspath(a.live), os.path.abspath(a.dreamed)
    base = json.load(open(new + '.base.json'))
    L, N = M.manifest(live), M.manifest(new)
    changed = set(r for r in L if r in base and L[r] != base[r])
    added = set(r for r in L if r not in base)
    write = [r for r in N if r not in changed and r not in added and L.get(r) != N[r]]
    arch = dict((os.path.basename(r), r) for r in N if r.startswith('_archive-dream-'))
    move = [r for r in L if '/' not in r and r.endswith('.md') and r not in N and r not in changed and r not in added and r in arch]
    print('kept (changed since the dream): %d %s' % (len(changed), sorted(changed)[:10]))
    print('kept (new since the dream):     %d %s' % (len(added), sorted(added)[:10]))
    print('write: %d files   move to archive: %d files' % (len(write), len(move)))
    if not a.yes:
        print('dry run. Add --yes to apply (after the user agreed).')
        return 0
    bdir = a.backup_dir or os.path.dirname(live)
    stamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    bpath = os.path.join(bdir, '%s-backup-%s.tgz' % (os.path.basename(live), stamp))
    with tarfile.open(bpath, 'w:gz') as t:
        t.add(live, arcname=os.path.basename(live))
    print('backup: ' + bpath)
    for r in write:
        dst = os.path.join(live, r)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(new, r), dst)
    for r in move:
        dst = os.path.join(live, arch[r])
        if os.path.exists(dst) and M.md5(dst) != L[r]:
            dst = dst[:-3] + '.live-copy.md'
        os.replace(os.path.join(live, r), dst)
    print('applied. To undo: extract %s over the pool.' % bpath)
    return 0


if __name__ == '__main__':
    sys.exit(main())
