"""번역용 JSON 만들기 → translation/messages.json  (원문 추출물이라 git 에는 넣지 않음)

항목: id, file, label, ja(태그 그대로), ja_plain, en(북미판), voiced(음성 파일 있음), box(표시 창), max_w, max_lines,
      how(창 연결 방법), speaker(5단계에서 채움), ko(번역), note
빈 원문(ja_plain 이 비어 있음)도 넣되 skip=true 로 표시(구조 보존용).
"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import sarc_read
import textwidth as tw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = os.path.join(ROOT, 'work', 'survey')
ms = json.load(open(os.path.join(S, 'messages_ja.json'), encoding='utf-8'))
us = json.load(open(os.path.join(S, 'messages_us.json'), encoding='utf-8'))
wm = json.load(open(os.path.join(S, 'winmap.json'), encoding='utf-8'))

# 음성: Voice/<묶음>.sarc 안 파일 이름(확장자 뺀 것) — 업데이트가 덮는 묶음은 업데이트 쪽
voice = {}
for top in ('Nintendo Land [Game] [0005000010101f00]', 'Nintendo Land [Update] [0005000e10101f00]'):
    vd = os.path.join(ROOT, top, 'content', 'JpJapanese', 'Voice')
    for f in os.listdir(vd):
        if f.endswith('.sarc'):
            voice[f[:-5]] = {os.path.splitext(n)[0] for n, _, _ in sarc_read(open(os.path.join(vd, f), 'rb').read())[1]}


def voiced(e):
    m = re.match(r'SceneMessage/(\w+?)/', e['file'])
    if not m or not e['label']:
        return False
    cat = m.group(1); lab = e['label'].lstrip('@')
    if 'TtlScrollWindow' in e['file']:
        return lab in voice.get('Ttl_Statue', set())
    if 'NoMsgVoice' in e['file']:
        lab = re.sub(r'_V$', '', lab)
    return lab in voice.get(cat, set()) or lab in voice.get('Common', set())


out = []
for i, e in enumerate(ms):
    k = e['file'] + '|' + (e['label'] or str(e['idx']))
    m = wm[k]
    jp = tw.plain(e['ja']).strip()
    r = dict(id=i, file=e['file'], label=e['label'], idx=e['idx'], ja=e['ja'], ja_plain=tw.plain(e['ja']),
             en=us.get(k, ''), voiced=voiced(e), box=(m['layout'] + '/' + m['pane']) if m.get('layout') else '',
             max_w=m.get('max_w'), max_lines=m.get('max_lines'), how=m['how'], speaker='', ko='', note='')
    if not jp:
        r['skip'] = True
    out.append(r)
os.makedirs(os.path.join(ROOT, 'translation'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'translation', 'messages.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
live = [r for r in out if not r.get('skip')]
print('전체 %d, 번역 대상 %d, 음성 있는 줄 %d, 글자 %d' % (len(out), len(live), sum(r['voiced'] for r in live), sum(len(r['ja_plain'].replace('\n', '')) for r in live)))
