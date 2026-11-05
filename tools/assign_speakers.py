"""화자표 적용: translation/messages.json 의 speaker 칸을 채운다(규칙 표는 work/speaker/speaker_rules.md 에 설명).

speaker 값: "화자→상대" 형식
  모니타→플레이어      : 안내 로봇 모니타(가타카나 어미 デス·マス). 대사창 기본
  모니타(수련)→플레이어 : 닌자성 수련 지도, 플레이어를 「どの(殿)」로 부름 (Nzm T1xx~T2xx, T9xx)
  모니타 공주→플레이어  : 닌자성 공주 역(わらわ·そなた·じゃ) (Nzm T300~T567, T520 제외)
  가짜 공주→플레이어    : 정체를 드러낸 가짜(가타카나 악당 말투) (Nzm T520)
  다크 모니타→플레이어  : 피크민 어트랙션 악당(ワタシ, 히라가나 존댓말) (Pkm W503~W547)
  석상 명판(설명)       : 석상 설명 중 ◆…◆ 부분(서술체)  ※ 같은 줄 뒤쪽은 모니타 한마디
  시스템 안내→플레이어  : 공통 창·안내 창·알림 창·조작 힌트·UI
"""
import os, sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'translation', 'messages.json')
tl = json.load(open(P, encoding='utf-8'))


def num(label):
    m = re.search(r'_([A-Z])(\d+)', label or '')
    return (m.group(1), int(m.group(2))) if m else (None, None)


def speaker(r):
    f = r['file'].split('/')[-1]; lab = r['label'] or ''
    k, n = num(lab)
    if f == 'NzmGameWindow.msbt':
        if n == 520:
            return '가짜 공주→플레이어'
        if 300 <= n <= 567:
            return '모니타 공주→플레이어'
        return '모니타(수련)→플레이어'
    if f == 'PkmGameWindow.msbt' and k == 'W' and 503 <= n <= 547:
        return '다크 모니타→플레이어'
    if f == 'MtrGameWindow.msbt' and lab in ('@Msg_T012', '@Msg_T013', '@Msg_W005', '@Msg_W300'):
        return '시스템 안내→플레이어'
    if 'GameWindow' in f or 'NoMsgVoice' in f:
        return '모니타→플레이어'
    if f == 'TtlScrollWindow.msbt':
        if lab.startswith('StatueName') or lab.startswith('GateName'):
            return '(이름)'
        return '석상 명판+모니타→플레이어' if '◆' in r['ja'] else '모니타→플레이어'
    if re.search(r'(StartCall|Success|Failure|NextCall)\.msbt$', f):
        return '알림(큰 글씨)→플레이어'
    if f in ('AdviceWin.msbt', 'NoticeWin.msbt', 'CmnMsgWin.msbt', 'ErrorViewerMsg.msbt', 'OliveMessage.msbt'):
        return '시스템 안내→플레이어'
    if re.search(r'(Name|Rank|Unit|Format|ReplaceList)', f):
        return '(이름·단위)'
    return '(UI)'


import collections
c = collections.Counter()
for r in tl:
    if r.get('skip'):
        continue
    r['speaker'] = speaker(r); c[r['speaker']] += 1
json.dump(tl, open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for k, v in c.most_common():
    print('%-24s %d' % (k, v))
