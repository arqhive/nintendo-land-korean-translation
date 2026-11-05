"""번역 묶음 검사: python -I tools/check_ko.py <묶음이름>   (예: statue)
입력: translation/ko/<묶음>.json = [{"id": 123, "ko": "...", "note": "..."}]
검사:
  누락    — 묶음의 id 가 번역에 없음 / 빈 번역
  태그    — 원문(후리가나 뺀)의 {..} 태그 목록과 번역의 태그 목록이 다름(순서 무관, 개수 포함)
  일본어  — 번역에 가나·한자가 남음
  넘침    — 창 폭(px)·줄 수 초과 (check_overflow 와 같은 기준)
  부호    — 「….」「~.」「~,」, 전각 부호(！？：～・), 줄 끝이 종결어미(다·요·까·죠·오·네·군)인데 부호 없음
  용어    — 용어집 공식 표기와 다른 흔한 오기(사전 목록)
"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
import check_overflow as co, textwidth as tw

ROOT = co.ROOT
TAG = re.compile(r'\{[^}]*\}')
RUBY = re.compile(r'\{0:0:[0-9a-f]*\}')
JP = re.compile(r'[぀-ヿ一-鿿]')
END = re.compile(r'(다|요|까|죠|오|네|군|지|자|라|어|아|해|래|게)$')
# 아이콘 → (받침 있음, 받침이 ㄹ) — docs/icons.md
ICON = {'': (0, 0), '': (0, 0), '': (0, 0), '': (0, 0), '': (1, 0), '': (1, 0),
        '': (0, 0), '': (0, 0), '': (1, 0), '': (0, 0), '': (0, 0), '': (1, 0),
        '': (0, 0), '': (1, 0), '': (0, 0), '': (0, 0), '': (1, 0), '': (1, 0),
        '': (1, 1), '': (1, 1), '': (1, 1), '': (1, 1), '': (0, 0), '': (1, 0),
        '': (0, 0)}
WRONG = {'스타십': '스타쉽', '키스 ': '키이스', '테크타이트': '텍타이트', '데쿠나무': '데크나무', '원생생물': '원주생물',
         '올리마르': '올리마', '겟소': '징오징오', '캔디': '사탕', '모니터 로봇': '모니타', '닌텐도랜드': '닌텐도 랜드'}


def main(g):
    pk = json.load(open(os.path.join(ROOT, 'work', 'tl', 'packet_%s.json' % g), encoding='utf-8'))
    ko = {x['id']: x for x in json.load(open(os.path.join(ROOT, 'translation', 'ko', '%s.json' % g), encoding='utf-8'))}
    tl = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'translation', 'messages.json'), encoding='utf-8'))}
    probs = collections.defaultdict(list)
    kmap = {}
    for p in pk:
        k = ko.get(p['id'])
        if not k or not (k.get('ko') or '').strip():
            probs['누락'].append((p['id'], p['ja'][:30])); continue
        s = k['ko']; r = tl[p['id']]
        kmap[r['file'] + '|' + (r['label'] or str(r['idx']))] = s
        if collections.Counter(TAG.findall(p['ja'])) != collections.Counter(TAG.findall(s)):
            probs['태그'].append((p['id'], sorted(TAG.findall(p['ja'])), sorted(TAG.findall(s))))
        pua = lambda x: collections.Counter(c for c in x if '' <= c <= '')
        if pua(p['ja']) != pua(s):
            probs['아이콘 글자'].append((p['id'], ''.join(pua(p['ja']).elements()).encode('unicode_escape').decode(), ''.join(pua(s).elements()).encode('unicode_escape').decode()))
        for m in re.finditer(r'([-])\s?(을|를|으로|로|이|가|은|는|과|와)(?![가-힣])', TAG.sub('', s)):
            ic, josa = m.group(1), m.group(2)
            if ic in ICON:
                bat, rieul = ICON[ic]
                ok = {'을': bat, '를': not bat, '이': bat, '가': not bat, '은': bat, '는': not bat, '과': bat, '와': not bat,
                      '으로': bat and not rieul, '로': (not bat) or rieul}[josa]
                if not ok:
                    probs['아이콘 조사'].append((p['id'], '%s+%s' % (hex(ord(ic)), josa), TAG.sub('', s)[:40]))
        if JP.search(TAG.sub('', s)):
            probs['일본어'].append((p['id'], s[:40]))
        t = TAG.sub('', s)
        if re.search(r'…\.|~\.|~,|[！？：～・]', t):
            probs['부호'].append((p['id'], '금지 부호', t[:50]))
        for ln in t.split('\n')[:-1] + [t.split('\n')[-1]]:
            ln = ln.rstrip()
            if ln and END.search(ln) and len(ln) > 3 and '◆' not in ln[-1:]:
                probs['부호(줄끝)'].append((p['id'], ln[-20:]))
        for w, right in WRONG.items():
            if w in t:
                probs['용어'].append((p['id'], w + '→' + right, t[:40]))
    for o in co.check(kmap):
        probs['넘침'].append((o['key'].split('/')[-1], o['problem'], o['ko'][:40]))
    extra = set(ko) - {p['id'] for p in pk}
    if extra:
        probs['묶음에 없는 id'].append(sorted(extra)[:20])
    print('[%s] 원문 %d줄, 번역 %d줄' % (g, len(pk), len(ko)))
    for k, v in probs.items():
        print('== %s %d' % (k, len(v)))
        for x in v[:40]:
            print('   ', x)
    if not probs:
        print('문제 없음')


if __name__ == '__main__':
    main(sys.argv[1])
