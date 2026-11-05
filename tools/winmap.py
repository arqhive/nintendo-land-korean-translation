"""메시지 → 표시 글 상자(창) 연결과 한 줄 최대 폭·최대 줄 수.

결과: work/survey/winmap.json  {"파일|라벨": {box, layout, pane, font, fsize, cspace, lspace, max_w, max_lines, how}}
how:
  exact  LayoutMessage 의 라벨 == 같은 레이아웃(부품 포함) 글 상자의 텍스트 ID
  stem   라벨 줄기(@ 떼고 첫 토막) == 글 상자 이름·ID 줄기
  rule   장면·공통 메시지 종류 규칙(RULES)
  rel    못 찾음 → 원문 폭을 기준으로 검사(check_overflow 에서 처리)
일본어 실행에서는 _JpJa 상자가 있으면 그 상자를 쓴다.
"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import textwidth as tw

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SURVEY = os.path.join(ROOT, 'work', 'survey')

# (파일 정규식, 라벨 정규식) -> (레이아웃, 글 상자)   위에서부터 먼저 맞는 것
RULES = [
    (r'GameWindow\.msbt$', r'.*', 'GameWindow_00', 'T_GameWd_00_JpJa'),
    (r'TtlScrollWindow\.msbt$', r'^StatueName', 'Cmg_ScrollWindow_00', 'T_Prize_00'),
    (r'TtlScrollWindow\.msbt$', r'.*', 'Cmg_ScrollWindow_00', 'T_Text_00'),
    (r'StartCall\.msbt$', r'^@MsgS', 'Cmg_StartCall_00', 'T_StartCallS_00'),
    (r'StartCall\.msbt$', r'.*', 'StartCall_00', 'T_Text_00'),
    (r'Success\.msbt$', r'^@MsgS', 'Cmg_Success_00', 'T_TextS_00'),
    (r'Success\.msbt$', r'.*', 'Success_00', 'T_Text_00'),
    (r'Failure\.msbt$', r'^@MsgS', 'Cmg_Failure_00', 'T_TextS_00'),
    (r'Failure\.msbt$', r'.*', 'Failure_00', 'T_Text_00'),
    (r'NextCall\.msbt$', r'.*', 'Cmg_Next_00', 'T_Text_00'),
    (r'CmnMsgWin\.msbt$', r'.*', 'Cmn_MsgWindow_00', 'T_Message_00_JpJa'),
    (r'AdviceWin\.msbt$', r'.*', 'Cmn_AdviceWindow_00', 'T_Message_00_JpJa'),
    (r'NoticeWin\.msbt$', r'.*', 'Cmn_NoticeWindow_00', 'T_Message_00_JpJa'),
    # 코스·미션·마스터 조건 이름(번역 넘침 검사 중 추가, 11/06)
    (r'(StageName\w+|/Mtr)\.msbt$', r'^Course_', 'SelCourseName_00', 'T_Course_00'),
    (r'(StageName\w+|/Mtr)\.msbt$', r'^MissionB?_', 'SelMissionName_00', 'T_Mission_00'),
    (r'(StageName\w+|/Mtr)\.msbt$', r'^MasterB?_', 'Cmn_SelMission_00', 'T_Master_00'),
    (r'/Mtr\.msbt$', r'^Itm', 'Mtr_ItemGet_00', 'T_Text_00'),
    (r'(StageName\w+|/Mtr)\.msbt$', r'^MissionSub_', 'Cmn_SelMission_00', 'T_SubTitle_00'),
    (r'(StageName\w+|/Mtr)\.msbt$', r'^Option[A-Za-z]+$', 'SelCourseOption_00', 'T_Option_00'),
    (r'(StageName\w+|/Mtr)\.msbt$', r'^Option[A-Za-z]+_\d', 'SelCourseOption_00', 'T_OptionItem_00'),
    (r'GameModeName\.msbt$', r'.*', 'Cmn_StampWindow_00', 'T_GameName_00'),
    # 스탬프 이름: 획득 창(800px, M)과 목록(850px, Msg) 중 좁은 획득 창 기준
    (r'StampName\w+\.msbt$', r'.*', 'Cmn_StampWindow_00', 'T_StampCd_00'),
]
UNLIMITED = {('Cmg_ScrollWindow_00', 'T_Text_00')}   # 가로로 흐르는 띠(폭 10000)


def stem(s):
    s = re.sub(r'^(T_|\$|@)+', '', s.lstrip('$@'))
    s = re.sub(r'_(JpJa|Eu\w\w|Us\w\w)$', '', s)
    return re.split(r'_', s)[0].lower()


def load():
    tb = json.load(open(os.path.join(SURVEY, 'textboxes.json'), encoding='utf-8'))
    parts = json.load(open(os.path.join(SURVEY, 'layout_parts.json'), encoding='utf-8'))
    ms = json.load(open(os.path.join(SURVEY, 'messages_ja.json'), encoding='utf-8'))
    return tb, parts, ms


def box_limits(r):
    f = tw.font(r['font'])
    w = r['size'][0] * abs(r['scale'][0])
    if (r['layout'], r['pane']) in UNLIMITED:
        w = None
    lines = None
    if f is not None:
        sy = r['fsize'][1] / f.height
        step = f.line_feed * sy + r['lspace']
        h = abs(r['size'][1]) * abs(r['scale'][1])
        lines = max(1, int((h - r['fsize'][1]) // step) + 1) if step > 0 else 1
    return w, lines


def build():
    tb, parts, ms = load()
    by_lay = collections.defaultdict(list)
    for r in tb:
        by_lay[r['layout']].append(r)

    def cands(lay, depth=0, seen=None):
        seen = seen or set()
        if lay in seen or depth > 4:
            return []
        seen.add(lay)
        out = list(by_lay.get(lay, []))
        for p in parts.get(lay, []):
            if p['layout']:
                out += cands(p['layout'], depth + 1, seen)
        return out

    def prefer_jp(rs):
        names = {r['pane'] for r in rs}
        out = []
        for r in rs:
            if re.search(r'_(Eu\w\w|Us\w\w)$', r['pane']):
                continue
            if not r['pane'].endswith('_JpJa') and r['pane'] + '_JpJa' in names:
                continue
            out.append(r)
        return out or rs

    def find(lay, pane):
        for r in by_lay.get(lay, []):
            if r['pane'] == pane:
                return r

    res = {}
    for e in ms:
        key = e['file'] + '|' + (e['label'] or str(e['idx']))
        hit, how = [], 'rel'
        if e['file'].startswith('LayoutMessage/'):
            lay = e['file'].split('/')[-1][:-5]
            cs = cands(lay)
            lab = (e['label'] or '').lstrip('@')
            hit = [r for r in cs if r['textid'].lstrip('$').lstrip('@') == lab]
            how = 'exact'
            if not hit:
                st = stem(e['label'] or '')
                hit = [r for r in cs if st and (stem(r['pane']) == st or stem(r['textid']) == st)]
                how = 'stem'
            if not hit:
                # 부품 이름으로: 라벨 Btn_02 ↔ 부품 L_PauseBtn_02 → 그 부품 레이아웃의 글 상자
                st = stem(e['label'] or '')
                num = re.search(r'_(\d+)$', e['label'] or '')
                for p in parts.get(lay, []):
                    pn = p['pane'] or ''
                    if not (st and p['layout'] and st in pn.lower()):
                        continue
                    if num and not pn.endswith('_' + num.group(1)):
                        continue
                    sub = [r for r in cands(p['layout']) if r['font'] != 'CafeStd_25.bffnt']
                    if sub:
                        hit = sub; how = 'part'; break
        else:
            for fre, lre, lay, pane in RULES:
                if re.search(fre, e['file']) and re.search(lre, e['label'] or ''):
                    r = find(lay, pane)
                    if r:
                        hit, how = [r], 'rule'
                    break
        if not hit:
            res[key] = dict(how='rel')
            continue
        hit = prefer_jp(hit)
        lim = []
        for r in hit:
            w, n = box_limits(r)
            lim.append((w if w is not None else 1e9, n or 99, r))
        w, n, r = min(lim, key=lambda x: (x[0], x[1]))
        res[key] = dict(how=how, layout=r['layout'], pane=r['pane'], font=r['font'], fsize=r['fsize'],
                        cspace=r['cspace'], lspace=r['lspace'], max_w=None if w >= 1e9 else round(w, 1),
                        max_lines=n, n_cand=len(hit))
    json.dump(res, open(os.path.join(SURVEY, 'winmap.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    return res, ms


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    res, ms = build()
    c = collections.Counter(v['how'] for v in res.values())
    nonempty = {e['file'] + '|' + (e['label'] or str(e['idx'])) for e in ms if tw.plain(e['ja']).strip()}
    c2 = collections.Counter(res[k]['how'] for k in nonempty)
    print('전체', len(res), dict(c))
    print('글 있는 줄', len(nonempty), dict(c2))
