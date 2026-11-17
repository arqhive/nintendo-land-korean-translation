"""다시 번역(11/17) 결과 합치기: work/tl/retl/<묶음>_*.json([{"id":…, "ko":…}]) → translation/ko/<묶음>.json
사용: python -I tools/retl_merge.py <묶음> [--dry]
--dry 면 바뀔 줄 수만 센다. 같은 id 가 두 파일에 있으면 멈춘다.
"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g = sys.argv[1]; dry = '--dry' in sys.argv
d = os.path.join(ROOT, 'work', 'tl', 'retl')
new = {}
for x in sorted(os.listdir(d)):
    if x.startswith(g + '_') and x.endswith('.json'):
        for e in json.load(open(os.path.join(d, x), encoding='utf-8')):
            assert e['id'] not in new, ('같은 id 두 번', e['id'], x)
            new[e['id']] = e.get('ko')          # ko 없음 = 검토했고 지금 번역 그대로
p = os.path.join(ROOT, 'translation', 'ko', '%s.json' % g)
cur = json.load(open(p, encoding='utf-8'))
ids = {e['id'] for e in cur}
extra = set(new) - ids
assert not extra, ('묶음에 없는 id', sorted(extra)[:10])
keep = set(json.load(open(os.path.join(d, 'keep.json'))))
for e in cur:
    if e['id'] in keep and new.get(e['id']) not in (None, e['ko']):
        raise SystemExit('사용자가 고친 줄을 바꾸려 함: id %d %r → %r' % (e['id'], e['ko'], new[e['id']]))
changed = same = 0
for e in cur:
    if e['id'] in new:
        if new[e['id']] is not None and e['ko'] != new[e['id']]:
            changed += 1; e['ko'] = new[e['id']]
        else:
            same += 1
print('%s: 전체 %d줄, 다시 번역 받은 줄 %d(바뀜 %d, 같음 %d), 아직 안 한 줄 %d' % (g, len(cur), len(new), changed, same, len(cur) - len(new)))
if not dry:
    open(p, 'w', encoding='utf-8').write(json.dumps(cur, ensure_ascii=False, indent=1) + '\n')
