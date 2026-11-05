"""번역 작업 묶음 만들기 → work/tl/packet_<묶음>.json (원문 포함, git 제외)

항목: id, file(짧은 이름), label, speaker, voiced, ja(후리가나 태그 뺀 원문, 다른 태그는 그대로), en(영어판, 태그 뺌),
      max_chars(한 줄 최대 한글 글자 수, 띄어쓰기는 약 0.3자), max_lines
순서: 파일 → 라벨 순(앞뒤 줄이 장면 흐름이 되도록)
"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
import textwidth as tw, nl_font as nf

ROOT = nf.ROOT
for k, v in nf.load_calib().items():
    tw.HANGUL_W[k] = v['char_w']
RUBY = re.compile(r'\{0:0:[0-9a-f]*\}')
tl = json.load(open(os.path.join(ROOT, 'translation', 'messages.json'), encoding='utf-8'))
wm = json.load(open(os.path.join(ROOT, 'work', 'survey', 'winmap.json'), encoding='utf-8'))
DEFAULT = ('LunchMsg_A4.bffnt', [34.4, 40.8], 0.0)


def group(r):
    f = r['file']; b = f.split('/')[-1]
    if b == 'TtlScrollWindow.msbt':
        return 'statue'
    for k in ('Pkm', 'Mtr'):
        if '/' + k + '/' in f or b.startswith(k) or ('Name' + k) in b:
            return 'pkm_mtr'
    for k in ('Zld', 'Nzm', 'Lig', 'Dbt', 'Mro', 'Ysi', 'Dkb', 'Fzr', 'Blf', 'Gwr', 'Atr'):
        if '/' + k + '/' in f or b.startswith(k) or ('Name' + k) in b:
            return 'attractions'
    if '/Ttl/' in f or b.startswith('Ttl'):
        return 'ttl'
    if f.startswith('LayoutMessage/'):
        return 'common_layout'
    return 'common_msg'


def limits(r):
    k = r['file'] + '|' + (r['label'] or str(r['idx']))
    m = wm[k]
    font, fsize, cs = (m['font'], m['fsize'], m['cspace']) if m.get('font') else DEFAULT
    f = tw.font(font); name = font[:-6]
    adv = tw.HANGUL_W.get(name, tw.char_w(f, '漢')) * fsize[0] / f.width + cs
    ow = max(tw.line_widths(r['ja'], font, fsize, cs) or [0])
    ol = len(tw.plain(r['ja']).split('\n'))
    if m['how'] == 'rel':
        return max(1, int(ow // adv)), ol
    if m['max_w'] is None:
        return None, max(m['max_lines'], ol)
    return int(max(m['max_w'], ow) // adv), max(m['max_lines'], ol)


packs = collections.defaultdict(list)
for r in tl:
    if r.get('skip'):
        continue
    mc, ml = limits(r)
    packs[group(r)].append(dict(id=r['id'], file=r['file'].split('/')[-1], label=r['label'], speaker=r['speaker'],
                                voiced=r['voiced'], ja=RUBY.sub('', r['ja']), en=tw.plain(r['en']), max_chars=mc, max_lines=ml))
os.makedirs(os.path.join(ROOT, 'work', 'tl'), exist_ok=True)
for g, lst in packs.items():
    lst.sort(key=lambda x: (x['file'], x['label'] or ''))
    json.dump(lst, open(os.path.join(ROOT, 'work', 'tl', 'packet_%s.json' % g), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print('%-14s %4d줄 %6d자' % (g, len(lst), sum(len(tw.plain(x['ja'])) for x in lst)))
