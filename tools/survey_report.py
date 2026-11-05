"""all_files.jsonl 집계: 형식별 개수표(바깥 파일·묶음 안 잎 파일), 일본어 문자열이 걸린 형식과 예시.
→ work/survey/survey_report.md"""
import os, sys, json, collections
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'work', 'survey')
rs = [json.loads(l) for l in open(os.path.join(S, 'all_files.jsonl'), encoding='utf-8')]
top = [r for r in rs if '//' not in r['path']]
leaves = [r for r in rs if not r.get('note', '').startswith('container')]
L = ['# 전수 조사 집계 (4단계)', '',
     '- 바깥 파일(디스크에 보이는 파일): 본편 %d, 업데이트 %d' % (sum(r['src'] == 'game' for r in top), sum(r['src'] == 'update' for r in top)),
     '- 묶음(SARC) %d개를 펼친 잎 파일 %d개' % (sum(r.get('note', '').startswith('container') for r in rs), len(leaves)), '',
     '| 확장자 | 잎 파일 수 | 크기(MB) | 일본어 걸린 파일 | 걸린 인코딩 |', '|---|---|---|---|---|']
g = collections.defaultdict(list)
for r in leaves:
    g[r['ext']].append(r)
for ext, lst in sorted(g.items(), key=lambda x: -len(x[1])):
    hit = [r for r in lst if r.get('jp')]
    enc = collections.Counter(e for r in hit for e in r['jp'])
    L.append('| %s | %d | %.1f | %d | %s |' % (ext, len(lst), sum(r['size'] for r in lst) / 1e6, len(hit), ', '.join('%s %d' % kv for kv in enc.most_common())))
L += ['', '## 일본어가 걸린 파일 예시(형식별 최대 5개)', '']
for ext, lst in sorted(g.items()):
    hit = [r for r in lst if r.get('jp')]
    if not hit:
        continue
    L.append('### %s (%d)' % (ext, len(hit)))
    for r in hit[:5]:
        for enc, v in r['jp'].items():
            L.append('- `%s` %s %d: %s' % (r['path'][-90:], enc, v['n'], ' / '.join(v['sample'][:6])))
    L.append('')
errs = [r for r in rs if 'ERR' in r.get('note', '')]
L += ['## 풀기 오류 %d' % len(errs)] + ['- %s %s' % (r['path'], r['note']) for r in errs]
open(os.path.join(S, 'survey_report.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L[:60]))
