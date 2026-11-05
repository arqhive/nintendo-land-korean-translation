"""창(글 상자)별 크기 표 → work/survey/window_table.md. 한글 몇 자가 한 줄에 들어가는지도 적는다."""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
import textwidth as tw, nl_font as nf
ROOT = nf.ROOT; S = os.path.join(ROOT, 'work', 'survey')
cal = nf.load_calib()
wm = json.load(open(os.path.join(S, 'winmap.json'), encoding='utf-8'))
ms = json.load(open(os.path.join(S, 'messages_ja.json'), encoding='utf-8'))
live = {e['file'] + '|' + (e['label'] or str(e['idx'])) for e in ms if tw.plain(e['ja']).strip()}
g = collections.defaultdict(list)
for k in live:
    m = wm[k]
    if m['how'] != 'rel': g[(m['layout'], m['pane'])].append((k, m))
rows = []
for (lay, pane), lst in g.items():
    m = lst[0][1]; f = tw.font(m['font']); name = m['font'][:-6]
    hw = cal.get(name, {}).get('char_w') or tw.char_w(f, '漢')
    adv = hw * m['fsize'][0] / f.width + m['cspace']
    chars = '∞' if m['max_w'] is None else int((m['max_w'] + m['cspace']) // adv)
    rows.append((len(lst), lay, pane, name, m['fsize'][0], m['max_w'] or '∞', m['max_lines'], chars, sorted({x[1]['how'] for x in lst}),
                 sorted({x[0].split('/')[-1].split('|')[0] for x in lst})[:3]))
rows.sort(key=lambda r: -r[0])
L = ['# 창 크기 표 (3단계, 2026-11-06)', '',
     '- 폭 = 글 상자 폭(px, 레이아웃 좌표). 한글 칸 = 한 줄에 들어가는 한글 글자 수(띄어쓰기 없이).',
     '- 줄 = 상자 높이로 계산한 최대 줄 수. 원문이 이보다 크게 들어간 줄은 검사기가 원문 크기를 한도로 쓴다.',
     '- 창을 못 찾은 줄(rel) %d개는 원문 폭 기준으로 검사.' % sum(1 for k in live if wm[k]['how'] == 'rel'), '',
     '| 줄 수 | 레이아웃 / 글 상자 | 폰트 | 글자 크기 | 폭(px) | 줄 | 한글 칸 | 연결 | 메시지 파일 |', '|---|---|---|---|---|---|---|---|---|']
for r in rows:
    L.append('| %d | %s / %s | %s | %.1f | %s | %s | %s | %s | %s |' % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], ','.join(r[8]), ', '.join(r[9])))
open(os.path.join(S, 'window_table.md'), 'w', encoding='utf-8').write('\n'.join(L) + '\n')
print('\n'.join(L[:24]))
print('... 창', len(rows))
