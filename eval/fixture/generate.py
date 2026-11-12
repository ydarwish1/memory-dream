#!/usr/bin/env python3
"""Build the synthetic fixture: a made-up memory pool for a made-up user (alex, project acme-app)
with planted defects, two transcripts, an eval question set and the answer key.
usage: python3 generate.py [OUT_DIR]   (default: this folder). Deterministic: same output every run."""
import os
import sys
import json

OUT = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
POOL = os.path.join(OUT, 'pool')
TR = os.path.join(OUT, 'transcripts')


def note(fname, ntype, desc, body, name=None):
    name = name or fname[:-3].split('_', 1)[-1].replace('_', '-')
    return fname, '---\nname: %s\ndescription: %s\nmetadata:\n  type: %s\n---\n\n%s\n' % (name, desc, ntype, body.strip())


NOTES = []
add = lambda *a, **k: NOTES.append(note(*a, **k))

# --- good notes: tested rules and preferences. They must survive a dream pass byte for byte.
GOOD = [
 ('feedback_review_before_merge.md', 'feedback', 'Every pull request needs two approvals before merge',
  'Every pull request needs two approvals before merge.\n\n**Why:** a one-reviewer merge shipped a broken migration in January.\n\n**How to apply:** ask for a second reviewer before you press merge. Verified 2025-02-02 on three merges.'),
 ('feedback_flaky_test_freeze_clock.md', 'feedback', 'Flaky date tests: freeze the clock',
  'Date tests that fail near midnight: freeze the clock to a fixed morning time in the test setup.\n\n**Why:** the suite failed only between 23:00 and 01:00. Freezing the clock fixed 4 of 4 runs. Verified 2025-02-11.'),
 ('feedback_small_commits.md', 'feedback', 'Keep commits small and named by what they change',
  'Keep each commit to one change and name it by what it changes.\n\n**Why:** reverting a mixed commit took an hour in February. Verified 2025-02-14.'),
 ('feedback_read_errors_fully.md', 'feedback', 'Read the innermost error frame first',
  'Name a crash from its innermost frame, not the first line you see.\n\n**Why:** two bug reports blamed the wrong module. Verified 2025-01-30.'),
 ('feedback_one_question_at_a_time.md', 'feedback', 'Ask one question at a time',
  'When something is unclear, ask one question, wait, then go on.\n\n**Why:** alex skipped half of a five-question message. Verified 2025-02-08.'),
 ('user_alex_role.md', 'user', 'Alex is the solo founder of acme-app',
  'Alex is the solo founder of acme-app and writes most of the code. Verified 2025-01-20 (alex said so).'),
 ('user_alex_timezone.md', 'user', 'Alex works in the afternoon and evening',
  'Alex works mostly from 14:00 to 22:00 local time. Verified 2025-01-22 (alex said so).'),
 ('feedback_measure_before_claiming.md', 'feedback', 'A speed claim needs a before and after number',
  'A claim that something is faster needs a before number and an after number from the same machine.\n\n**Why:** a "2x faster" claim was noise. Verified 2025-02-19.'),
 ('feedback_plain_words.md', 'feedback', 'Explain in plain words first',
  'Lead with the plain answer, then the detail.\n\n**Why:** alex asked for it twice. Verified 2025-02-03.'),
 ('feedback_backup_before_bulk_edits.md', 'feedback', 'Back up before a bulk edit',
  'Before a bulk edit of many files, make a backup copy and prove the original did not change.\n\n**Why:** a bulk rename hit the wrong folder once. Verified 2025-02-21.'),
 ('reference_glossary.md', 'reference', 'Words alex uses for parts of acme-app',
  '"The board" means the main dashboard. "The queue" means the background job list. Verified 2025-01-25 (alex said so).'),
 ('feedback_name_the_file.md', 'feedback', 'Cite the file a fact came from',
  'When you answer from a note, name the note.\n\n**Why:** alex wants to check the source. Verified 2025-02-05.'),
]
for g in GOOD:
    add(*g)

# --- duplicates (3 pairs): the shorter copy should move to the archive
add('feedback_python_use_uv.md', 'feedback', 'Use uv for Python packages',
    'Use uv for Python packages in acme-app: run uv sync, not pip install. pip install broke the lock file twice in February. Verified 2025-02-12.')
add('feedback_use_uv_for_python.md', 'feedback', 'Use uv for Python packages',
    'Use uv for Python packages in acme-app: run uv sync, not pip install. pip install broke the lock file twice in February.')
add('reference_restart_worker.md', 'reference', 'How to restart the background worker',
    'To restart the background worker run systemctl restart acme-worker on the app server, then check systemctl status acme-worker shows active. Verified 2025-02-15.')
add('reference_worker_restart_steps.md', 'reference', 'How to restart the background worker',
    'To restart the background worker run systemctl restart acme-worker on the app server, then check systemctl status acme-worker shows active.')
add('user_alex_short_answers.md', 'user', 'Alex prefers short answers',
    'Alex prefers short answers: the result first, then at most three lines of detail. Alex said this on 2025-01-28 and again on 2025-02-09. Verified 2025-02-09.')
add('user_prefers_short_answers.md', 'user', 'Alex prefers short answers',
    'Alex prefers short answers: the result first, then at most three lines of detail. Alex said this on 2025-01-28 and again on 2025-02-09.')

# --- a numbered series of deploy logs: the older entries are superseded state
for v, d in ((11, '2025-01-10'), (12, '2025-01-24'), (13, '2025-02-07'), (14, '2025-03-05')):
    add('project_acme_deploy_v%d.md' % v, 'project', 'acme-app v1.%d deployed %s' % (v - 10, d),
        'acme-app v1.%d deployed to production on %s. It is live. Rollback: redeploy v1.%d.' % (v - 10, d, v - 11))

# --- two notes a transcript contradicts
add('reference_staging_access.md', 'reference', 'Staging has no SSH; use the web console',
    'Staging has no SSH. Port 22 is closed, so use the web console at https://console.example.com to run commands on staging.',
    name='staging-access')
add('project_api_port.md', 'project', 'The acme-app API listens on port 8080',
    'The acme-app API listens on port 8080 on the app server. Health check: curl localhost:8080/health.')

# --- notes with broken links (two are one typo away from a real note, two point nowhere)
add('reference_deploy_checklist.md', 'reference', 'Release checklist for acme-app',
    'Release checklist: run the tests, tag the release, deploy to staging, check the board, then deploy to production. Verified 2025-02-20.',
    name='deploy-checklist')
add('feedback_onboarding_notes.md', 'feedback', 'What a new session should read first',
    'A new session should read the glossary and [[staging-acess]] before touching servers.\n\n**Why:** a session ran commands on production by mistake. Verified 2025-02-01.')
add('reference_release_flow.md', 'reference', 'How a release moves from branch to production',
    'A release follows [[deploy-checklst]]. The older steps lived in [[old-runbook]]. Verified 2025-02-20.')
add('project_roadmap.md', 'project', 'acme-app roadmap themes',
    'Roadmap themes for the spring: billing, the board redesign, and the public API. Details were in [[q3-roadmap]]. Decided with alex on 2025-02-18.')

# --- a superseded pair after an earlier dream pass: the newer note names the older one stale, and the pass wrote its
# marker into the older note. Only the older note is contradicted; the marker must not flag the newer note back.
add('feedback_changelog_per_commit.md', 'feedback', 'Changelog: one line per commit',
    '> **Checked 2025-03-02: possibly superseded: named stale by feedback_changelog_by_feature.md. Read the newer note first.**\n\n'
    'Write the changelog as one line per commit.\n\n**Why:** it was quick to write. Verified 2025-01-18.')
add('feedback_changelog_by_feature.md', 'feedback', 'Changelog: group by feature',
    'Group the changelog by feature, one line per change a user can see. This supersedes feedback_changelog_per_commit.md, '
    'which said one line per commit.\n\n**Why:** alex could not find the billing changes in a list of 40 commits. Verified 2025-03-01.')

# --- orphans: notes the index never mentions
add('project_cache_warmup_idea.md', 'project', 'Idea: warm the cache after each deploy',
    'Idea from 2025-02-26: warm the cache after each deploy by loading the ten busiest pages. Not built yet. Decided to try it in March.')
add('reference_log_locations.md', 'reference', 'Where acme-app writes its logs',
    'acme-app writes logs to /var/log/acme/app.log and the worker to /var/log/acme/worker.log on the app server.')
add('feedback_small_prs.md', 'feedback', 'Keep pull requests under 400 lines',
    'Keep pull requests under 400 changed lines.\n\n**Why:** big PRs waited days for review. Verified 2025-02-17.')

# --- machine-state notes with no verified / not re-checked marker
UNMARKED = [
 ('project_db_version.md', 'project', 'The database runs Postgres 16.2', 'The database server runs Postgres 16.2 as of 2025-02-01.'),
 ('project_disk_usage.md', 'project', 'The app server disk was 81% full', 'The app server disk was 81% full on 2025-02-25 (34 GB free).'),
 ('project_ci_runner.md', 'project', 'CI runs on a self-hosted runner', 'CI runs on a self-hosted runner on the build server since 2025-01-15.'),
 ('project_backup_cron.md', 'project', 'Nightly backup cron at 02:00', 'A cron job on the database server takes a backup every night at 02:00. It is running.'),
 ('project_staging_url.md', 'project', 'Staging lives at staging.example.com', 'Staging is live at https://staging.example.com since 2025-01-12.'),
 ('project_cdn_setup.md', 'project', 'Static files go through the CDN', 'Static files are served through the CDN since 2025-02-10. Deployed with v1.3.'),
 ('project_queue_size.md', 'project', 'The job queue holds about 2,000 jobs a day', 'The background queue on the worker server handles about 2,000 jobs a day as of 2025-02-20.'),
 ('project_node_version.md', 'project', 'acme-app runs on Node 22.11.0', 'acme-app runs on Node 22.11.0 on the app server, installed 2025-01-30.'),
]
for u in UNMARKED:
    add(*u)

# --- the rest: ordinary notes that already say when they were checked
FILLER = [
 ('reference_check_disk.md', 'reference', 'How to check disk space on the app server', 'Run df -h / on the app server. Verified 2025-02-25.'),
 ('reference_tail_logs.md', 'reference', 'How to follow the app log', 'Run tail -f /var/log/acme/app.log on the app server. Verified 2025-02-22.'),
 ('reference_run_tests.md', 'reference', 'How to run the test suite', 'Run uv run pytest -q in the repo root. Verified 2025-02-12.'),
 ('reference_migrations.md', 'reference', 'How to run database migrations', 'Run uv run alembic upgrade head, then check the board loads. Verified 2025-02-13.'),
 ('reference_feature_flags.md', 'reference', 'Where feature flags live', 'Feature flags live in config/flags.yaml in the repo. Verified 2025-02-16.'),
 ('reference_billing_provider.md', 'reference', 'Billing goes through the payment provider sandbox in tests', 'Tests use the payment provider sandbox keys from .env.test. Verified 2025-02-18.'),
 ('reference_error_tracking.md', 'reference', 'Errors go to the error tracker', 'Errors from production go to the error tracker project acme-app. Verified 2025-02-19.'),
 ('project_board_redesign.md', 'project', 'Board redesign: decided on a two-column layout', 'Decided with alex on 2025-02-23: the board redesign uses a two-column layout. Verified 2025-02-23.'),
 ('project_public_api_scope.md', 'project', 'Public API v1 covers read endpoints only', 'Decided on 2025-02-24: public API v1 covers read endpoints only. Verified 2025-02-24.'),
 ('project_pricing_tiers.md', 'project', 'Two pricing tiers', 'Decided on 2025-02-27: two pricing tiers, free and team. Verified 2025-02-27.'),
 ('reference_local_dev.md', 'reference', 'How to start acme-app locally', 'Run uv sync, then uv run acme dev, then open http://localhost:3000 . Verified 2025-02-12.'),
 ('reference_secrets_rule.md', 'reference', 'Where secrets live', 'Secrets live in the password manager and in .env files that git ignores. Never paste them into chat. Verified 2025-02-04.'),
 ('reference_support_inbox.md', 'reference', 'Support email goes to the shared inbox', 'Support email goes to support@example.com, a shared inbox alex reads daily. Verified 2025-02-06.'),
 ('reference_dns_provider.md', 'reference', 'DNS is managed at the registrar', 'DNS for example.com is managed at the registrar dashboard. Verified 2025-02-07.'),
 ('reference_monitoring.md', 'reference', 'Uptime checks every minute', 'An uptime check hits https://staging.example.com/health and production every minute. Verified 2025-02-26.'),
]
for x in FILLER:
    add(*x)

ORPHANS = ['project_cache_warmup_idea.md', 'reference_log_locations.md', 'feedback_small_prs.md']


def index_text():
    lines = ['# Memory index', '']
    for f, t in NOTES:
        if f in ORPHANS:
            continue
        desc = t.split('description: ', 1)[1].split('\n', 1)[0]
        lines.append('- [%s](%s) — %s' % (f[:-3].split('_', 1)[-1].replace('_', ' ').title(), f, desc))
    lines += ['', '## Session log (pasted over time)', '']
    for i in range(1, 181):  # the bloat: a running log nobody prunes
        lines.append('- 2025-0%d-%02d session %03d: worked on acme-app; see the notes above for anything that mattered.' % (1 + i % 3, 1 + i % 28, i))
    return '\n'.join(lines) + '\n'


def tr_line(ts, role, content):
    return json.dumps(dict(type=role, timestamp=ts, message=dict(role=role, content=content)))


SESSION_A = [
 tr_line('2025-03-10T15:00:00Z', 'user', 'Can you check the staging server logs for the 500 errors?'),
 tr_line('2025-03-10T15:00:20Z', 'assistant', [dict(type='text', text='My notes say staging has no SSH. I will try SSH once before I use the console.'),
                                            dict(type='tool_use', id='t1', name='Bash', input=dict(command='ssh staging hostname'))]),
 tr_line('2025-03-10T15:00:25Z', 'user', [dict(type='tool_result', tool_use_id='t1', content='staging-1')]),
 tr_line('2025-03-10T15:00:40Z', 'assistant', [dict(type='text', text='SSH to staging works: ssh staging printed staging-1. The note that says there is no SSH is wrong.'),
                                            dict(type='tool_use', id='t2', name='Bash', input=dict(command='ssh staging tail -5 /var/log/acme/app.log'))]),
 tr_line('2025-03-10T15:00:45Z', 'user', [dict(type='tool_result', tool_use_id='t2', content='2025-03-10 14:58:01 ERROR 500 /api/orders timeout')]),
 tr_line('2025-03-10T15:01:00Z', 'assistant', [dict(type='text', text='The 500s are order API timeouts.')]),
]
SESSION_B = [
 tr_line('2025-03-12T16:00:00Z', 'user', 'We moved the API to port 9090 yesterday. Does the health check pass?'),
 tr_line('2025-03-12T16:00:10Z', 'assistant', [dict(type='tool_use', id='u1', name='Bash', input=dict(command='curl -s localhost:9090/health'))]),
 tr_line('2025-03-12T16:00:12Z', 'user', [dict(type='tool_result', tool_use_id='u1', content='{"status":"ok","port":9090}')]),
 tr_line('2025-03-12T16:00:30Z', 'assistant', [dict(type='text', text='Yes. The API answers on port 9090 and the health check passes.')]),
 tr_line('2025-03-12T16:05:00Z', 'user', 'What is the latest deployed version?'),
 tr_line('2025-03-12T16:05:20Z', 'assistant', [dict(type='text', text='v1.4, deployed on 2025-03-05.')]),
]

QUESTIONS = [
 dict(id='ssh-staging', q='How do I get a shell on staging?', query='ssh into staging server shell access', keys=['ssh staging'], split='dev', proof='transcripts/session-2025-03-10.jsonl:3'),
 dict(id='api-port', q='Which port does the API use?', query='api port health check', keys=['9090'], split='heldout', proof='transcripts/session-2025-03-12.jsonl:3'),
 dict(id='restart-worker', q='How do I restart the background worker?', query='restart background worker', keys=['systemctl restart acme-worker'], split='dev', proof='pool/reference_restart_worker.md'),
 dict(id='python-tool', q='Which tool installs Python packages?', query='python packages install tool', keys=['uv sync'], split='dev', proof='pool/feedback_python_use_uv.md'),
 dict(id='latest-deploy', q='What is the latest deployed version?', query='latest deploy version production', keys=['v1.4'], split='dev', proof='transcripts/session-2025-03-12.jsonl:6'),
 dict(id='log-path', q='Where does the app write its logs?', query='where are the app logs', keys=['/var/log/acme/app.log'], split='heldout', proof='transcripts/session-2025-03-10.jsonl:5'),
 dict(id='short-answers', q='How does alex like answers?', query='alex prefers answers style', keys=['result first'], split='dev', proof='pool/user_alex_short_answers.md'),
 dict(id='review-rule', q='What does a pull request need before merge?', query='pull request merge approvals', keys=['two approvals'], split='dev', proof='pool/feedback_review_before_merge.md'),
 dict(id='flaky-dates', q='How do we fix flaky date tests?', query='flaky date tests midnight', keys=['freeze the clock'], split='heldout', proof='pool/feedback_flaky_test_freeze_clock.md'),
 dict(id='disk-check', q='How do I check disk space?', query='check disk space', keys=['df -h'], split='dev', proof='pool/reference_check_disk.md'),
 dict(id='release-steps', q='What are the release steps?', query='release checklist steps', keys=['tag the release'], split='dev', proof='pool/reference_deploy_checklist.md'),
 dict(id='cache-idea', q='What was the cache idea?', query='cache idea after deploy', keys=['busiest pages'], split='heldout', proof='pool/project_cache_warmup_idea.md'),
]

for _q in QUESTIONS:  # transcript = proven by a session; note = a regression question proven by a note
    _q['kind'] = 'note' if _q['proof'].startswith('pool/') else 'transcript'

TOPICS = dict(goals=['Ship the board redesign.', 'Launch the public API (read endpoints first).'], topics=[
 dict(id='servers', title='Servers and access', purpose='How to reach the servers and what runs where.',
      words=['staging', 'server', 'ssh', 'port', 'api', 'worker', 'disk', 'logs', 'log', 'database', 'cdn', 'node', 'postgres', 'cron', 'backup', 'queue', 'monitoring', 'dns', 'url'], facts=[]),
 dict(id='releases', title='Releases and deploys', purpose='How a change reaches production, and the deploy history.',
      words=['deploy', 'deployed', 'release', 'checklist', 'migrations', 'rollback', 'version', 'production', 'flags'], facts=[]),
 dict(id='workflow', title='How we work', purpose='Tested rules for code, review and tests.',
      words=['review', 'merge', 'prs', 'pull', 'commits', 'tests', 'test', 'flaky', 'python', 'uv', 'errors', 'measure', 'backup', 'bulk', 'ci', 'runner'], facts=[]),
 dict(id='alex', title='Alex: how alex likes to work', purpose='Who alex is and how to talk with alex.',
      words=['alex', 'user', 'answers', 'short', 'question', 'plain', 'timezone', 'role', 'glossary', 'cite', 'onboarding'], facts=[]),
 dict(id='product', title='acme-app product decisions', purpose='Roadmap, pricing and design decisions.',
      words=['roadmap', 'pricing', 'board', 'redesign', 'public', 'scope', 'cache', 'idea', 'billing', 'support', 'secrets'], facts=[]),
])

ANSWER_KEY = dict(
 index_over_budget=True,
 conflict_copies=['MEMORY.sync-conflict-20250305-101500-ABCDEF1.md', 'feedback_review_before_merge.sync-conflict-20250306-090000-ABCDEF1.md'],
 duplicates=[dict(keep='feedback_python_use_uv.md', duplicate='feedback_use_uv_for_python.md'),
             dict(keep='reference_restart_worker.md', duplicate='reference_worker_restart_steps.md'),
             dict(keep='user_alex_short_answers.md', duplicate='user_prefers_short_answers.md')],
 series_older=['project_acme_deploy_v11.md', 'project_acme_deploy_v12.md', 'project_acme_deploy_v13.md'],
 broken_links_fixable=[dict(note='feedback_onboarding_notes.md', link='[[staging-acess]]', to='reference_staging_access'),
                       dict(note='reference_release_flow.md', link='[[deploy-checklst]]', to='reference_deploy_checklist')],
 broken_links_unfixable=[dict(note='reference_release_flow.md', link='[[old-runbook]]'), dict(note='project_roadmap.md', link='[[q3-roadmap]]')],
 contradicted=[dict(note='reference_staging_access.md', evidence='transcripts/session-2025-03-10.jsonl:3 (ssh staging hostname -> staging-1)'),
               dict(note='project_api_port.md', evidence='transcripts/session-2025-03-12.jsonl:1 and :3 (moved to 9090; health ok on 9090)')],
 state_unmarked=sorted([u[0] for u in UNMARKED] + ['project_acme_deploy_v14.md', 'reference_log_locations.md', 'project_api_port.md',
                        'reference_staging_access.md', 'project_cache_warmup_idea.md']),
 named_stale=['feedback_changelog_per_commit.md'],
 sync_leftovers={'.stversions': 2},
 orphans=ORPHANS,
 good_notes_unchanged=[g[0] for g in GOOD],
)

# --- sync leftovers: old versions Syncthing kept. The audit counts them and never reads them as notes.
STVERSIONS = ['feedback_small_commits~20250301-120000.md', 'MEMORY~20250302-090000.md']


def main():
    for d in (POOL, TR):
        os.makedirs(d, exist_ok=True)
    for f, t in NOTES:
        open(os.path.join(POOL, f), 'w').write(t)
    idx = index_text()
    open(os.path.join(POOL, 'MEMORY.md'), 'w').write(idx)
    open(os.path.join(POOL, ANSWER_KEY['conflict_copies'][0]), 'w').write(idx.replace('session 180', 'session 180 (other machine)'))
    g0 = dict(NOTES)['feedback_review_before_merge.md']
    open(os.path.join(POOL, ANSWER_KEY['conflict_copies'][1]), 'w').write(g0.replace('two approvals', 'one approval'))
    os.makedirs(os.path.join(POOL, '.stversions'), exist_ok=True)
    for f in STVERSIONS:
        live = f.split('~')[0] + '.md'
        src = idx if live == 'MEMORY.md' else dict(NOTES)[live]
        open(os.path.join(POOL, '.stversions', f), 'w').write(src.replace('Verified', 'Old copy. Verified', 1))
    open(os.path.join(TR, 'session-2025-03-10.jsonl'), 'w').write('\n'.join(SESSION_A) + '\n')
    open(os.path.join(TR, 'session-2025-03-12.jsonl'), 'w').write('\n'.join(SESSION_B) + '\n')
    json.dump(QUESTIONS, open(os.path.join(OUT, 'questions.json'), 'w'), indent=1)
    json.dump(TOPICS, open(os.path.join(OUT, 'topics.json'), 'w'), indent=1)
    json.dump(ANSWER_KEY, open(os.path.join(OUT, 'answer-key.json'), 'w'), indent=1)
    print('fixture: %d notes + index + 2 conflict copies + %d .stversions files, 2 transcripts, %d questions -> %s' % (
        len(NOTES), len(STVERSIONS), len(QUESTIONS), OUT))


if __name__ == '__main__':
    main()
