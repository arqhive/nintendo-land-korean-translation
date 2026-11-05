"""번역문 넘침 검사.

사용: python -I tools/check_overflow.py [번역.json]
  번역 JSON: [{"file":..., "label":..., "ko":...}, ...]  또는  {"파일|라벨": "번역", ...}
  인자가 없으면 원문 자체를 검사(도구 확인용, 넘침 0이어야 정상).

기준(work/survey/winmap.json):
  * 창을 찾은 줄: 한 줄 폭 ≤ max(창 폭, 원문 폭), 줄 수 ≤ max(창 줄 수, 원문 줄 수)
    (원문이 창보다 넓게 들어가 있는 곳은 게임이 그 크기를 실제로 쓰는 것으로 본다)
  * 창을 못 찾은 줄(rel): 같은 폰트(기본 Msg)로 잰 번역 폭 ≤ 원문 폭 × REL_TOL, 줄 수 ≤ 원문 줄 수
  * 변수 태그(이름·숫자)는 폭 0으로 센다 → 이름이 들어가는 줄은 여유를 따로 본다(경고 표시)
한글 폭은 work/font_calib.json 의 char_w(빌드에서 쓰는 값)로 잰다.
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import textwidth as tw, nl_font as nf

ROOT = nf.ROOT
SURVEY = os.path.join(ROOT, 'work', 'survey')
REL_TOL = 1.0
DEFAULT_FONT = ('LunchMsg_A4.bffnt', [34.4, 40.8], 0.0, 0.0)
VAR = re.compile(r'\{(3|4|5|6):\d+:[0-9a-f]*\}')

for k, v in nf.load_calib().items():
    tw.HANGUL_W[k] = v['char_w']


def key_of(e):
    return e['file'] + '|' + (e['label'] or str(e['idx']))


def measure(text, m):
    font, fsize, cs, ls = (m['font'], m['fsize'], m['cspace'], m['lspace']) if m.get('font') else DEFAULT_FONT
    ws = tw.line_widths(text, font, fsize, cs)
    return ws, len(tw.plain(text).split('\n'))


def limits(e, m):
    ow, ol = measure(e['ja'], m)
    ow = max(ow) if ow else 0
    if m['how'] == 'rel':
        return ow * REL_TOL, ol, 'rel'
    mw = m['max_w']
    return (None if mw is None else max(mw, ow)), max(m['max_lines'], ol), m['how']


def check(ko_map):
    wm = json.load(open(os.path.join(SURVEY, 'winmap.json'), encoding='utf-8'))
    ms = json.load(open(os.path.join(SURVEY, 'messages_ja.json'), encoding='utf-8'))
    out = []
    for e in ms:
        k = key_of(e)
        ko = ko_map.get(k) if ko_map is not None else e['ja']
        if ko is None or not tw.plain(ko).strip():
            continue
        m = wm[k]
        mw, ml, how = limits(e, m)
        ws, nl = measure(ko, m)
        w = max(ws) if ws else 0
        prob = []
        if mw is not None and w > mw + 0.5:
            prob.append('폭 %d/%dpx' % (round(w), round(mw)))
        if nl > ml:
            prob.append('줄 %d/%d' % (nl, ml))
        if prob:
            out.append(dict(key=k, how=how, box=(m.get('layout', '') + '/' + m.get('pane', '')) if m.get('layout') else '',
                            problem=', '.join(prob), has_var=bool(VAR.search(ko)), ja=tw.plain(e['ja']), ko=tw.plain(ko)))
    return out


def load_ko(path):
    j = json.load(open(path, encoding='utf-8'))
    if isinstance(j, dict):
        return j
    return {x['file'] + '|' + x['label']: x['ko'] for x in j if x.get('ko')}


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    ko = load_ko(sys.argv[1]) if len(sys.argv) > 1 else None
    res = check(ko)
    print('넘침 %d줄' % len(res))
    for r in res[:200]:
        print('  [%s] %s  %s%s\n      원문: %s\n      번역: %s' % (r['how'], r['key'], r['problem'], ' (변수 있음)' if r['has_var'] else '', r['ja'][:60], r['ko'][:60]))
