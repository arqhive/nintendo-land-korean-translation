"""번역본 검토 페이지 → work/review/번역본.html (원문 포함이라 git 제외)
어트랙션·화면별 고르기, 낱말 검색(원문·번역·영어), id 로 바로 찾기. 태그는 작은 표시로 바꿔 보여 줌."""
import os, sys, json, re, html
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tl = json.load(open(os.path.join(ROOT, 'translation', 'messages.json'), encoding='utf-8'))
ICON = {'': 'A', '': 'B', '': 'X', '': 'Y', '': '십자', '': '십자', '': 'A', '': 'B',
        '': 'HOME', '': '+', '': '−', '': '1', '': '2', '': '스틱', '': 'C', '': 'Z',
        '': 'L스틱', '': 'R스틱', '': 'L', '': 'R', '': 'ZL', '': 'ZR', '': 'GamePad', '': '리모컨', '': '?'}
NAMES = {'Ttl': '광장·모니타', 'Statue': '석상', 'Mtr': '메트로이드 블래스트', 'Zld': '젤다 배틀 퀘스트', 'Pkm': '피크민 어드벤처',
         'Lig': '루이지 고스트 맨션', 'Dbt': '동물의 숲 사탕 축제', 'Mro': '마리오 체이스', 'Ysi': '요시의 과일 카트', 'Dkb': '동키콩 크래시 코스',
         'Fzr': '캡틴 팔콘 트위스터 레이스', 'Blf': '벌룬 트립 브리즈', 'Gwr': '옥토퍼스 댄스', 'Nzm': '타카마루 수리검 도장', 'Atr': '어트랙션 투어',
         'CmnMsg': '공통 메시지 창', 'CmnLay': '공통 화면'}


def group(r):
    f = r['file']; b = f.split('/')[-1]
    if b == 'TtlScrollWindow.msbt':
        return 'Statue'
    for k in ('Mtr', 'Zld', 'Pkm', 'Lig', 'Dbt', 'Mro', 'Ysi', 'Dkb', 'Fzr', 'Blf', 'Gwr', 'Nzm', 'Atr', 'Ttl'):
        if '/' + k + '/' in f or b.startswith(k) or ('Name' + k) in b or ('_' + k) in b:
            return k
    return 'CmnLay' if f.startswith('LayoutMessage/') else 'CmnMsg'


def show(s):
    s = html.escape(s or '')
    s = re.sub(r'\{0:3:ffff\}', '</span>', s)
    s = re.sub(r'\{0:3:([0-9a-f]{4})\}', r'<span class="col">', s)
    s = re.sub(r'\{0:0:[0-9a-f]*\}', '', s)
    s = re.sub(r'\{6:\d+:[0-9a-f]*\}', '<i class="v">이름</i>', s)
    s = re.sub(r'\{[345]:\d+:[0-9a-f]*\}', '<i class="v">값</i>', s)
    s = re.sub(r'\{2:\d+:[0-9a-f]*\}', '<i class="v">그림</i>', s)
    s = re.sub(r'\{[^}]*\}', '<i class="v">태그</i>', s)
    for k, v in ICON.items():
        s = s.replace(k, '<b class="ic">%s</b>' % v)
    s = re.sub(r'[-]', '<b class="ic">?</b>', s)
    return s.replace('\n', '<br>')


rows = []
for r in tl:
    if r.get('skip'):
        continue
    rows.append(dict(id=r['id'], g=group(r), f=r['file'].split('/')[-1].replace('.msbt', ''), l=r['label'] or '', sp=r.get('speaker', ''),
                     vo=r['voiced'], ja=show(r['ja']), ko=show(r.get('ko')), en=show(r['en']),
                     q=(re.sub(r'\{[^}]*\}', '', r['ja']) + ' ' + (r.get('ko') or '') + ' ' + re.sub(r'\{[^}]*\}', '', r['en'])).lower()))
order = list(NAMES)
rows.sort(key=lambda x: (order.index(x['g']), x['f'], x['l']))
counts = {g: sum(1 for x in rows if x['g'] == g) for g in order}
opts = ''.join('<option value="%s">%s (%d)</option>' % (g, NAMES[g], counts[g]) for g in order if counts[g])

page = '''<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>닌텐도 랜드 번역본</title><style>
:root{--bg:#fafaf7;--fg:#1d1d1b;--mut:#6b6b66;--line:#e2e1da;--card:#fff;--ko:#0b4f8a;--hl:#fff3b0;--col:#c2410c}
@media (prefers-color-scheme:dark){:root{--bg:#18191b;--fg:#e8e6e1;--mut:#9a9890;--line:#2e3033;--card:#202225;--ko:#8cc4ff;--hl:#5a4a00;--col:#fb923c}}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.55 "Malgun Gothic",system-ui,sans-serif}
header{position:sticky;top:0;background:var(--bg);border-bottom:1px solid var(--line);padding:10px 16px;display:flex;gap:8px;flex-wrap:wrap;align-items:center;z-index:2}
h1{font-size:17px;margin:0 8px 0 0}select,input{font:inherit;padding:5px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
input[type=search]{flex:1;min-width:180px}label{color:var(--mut);font-size:13px}#n{color:var(--mut);font-size:13px}
table{width:100%;border-collapse:collapse}td{border-bottom:1px solid var(--line);padding:7px 10px;vertical-align:top}
td.m{width:150px;color:var(--mut);font-size:12px;word-break:break-all}td.ko{color:var(--ko);font-size:16px}td.ja,td.en{font-size:14px}
.en{display:none}body.showen .en{display:table-cell}.col{color:var(--col);font-weight:600}
i.v{font-style:normal;font-size:11px;border:1px solid var(--mut);border-radius:4px;padding:0 3px;color:var(--mut)}
b.ic{font-size:11px;background:var(--fg);color:var(--bg);border-radius:9px;padding:0 5px}
tr.hit td{background:var(--hl)}.sp{display:block}.vo{color:var(--col)}main{padding:0 6px 40px}
@media (max-width:700px){td.m{width:80px}td.ja{display:none}}
</style></head><body><header><h1>닌텐도 랜드 번역본</h1>
<select id="g"><option value="">전체 (@@N@@)</option>@@OPTS@@</select>
<input type="search" id="s" placeholder="원문·번역·영어 검색 / 숫자만 넣으면 id"> <label><input type="checkbox" id="e"> 영어판</label> <span id="n"></span></header>
<main><table><tbody id="t"></tbody></table></main>
<script>const R=@@ROWS@@;
const t=document.getElementById('t'),g=document.getElementById('g'),s=document.getElementById('s'),n=document.getElementById('n');
function draw(){const gv=g.value,q=s.value.trim().toLowerCase();let out=[],c=0;
for(const r of R){if(gv&&r.g!==gv)continue;if(q){if(/^\\d+$/.test(q)){if(String(r.id)!==q)continue}else if(!r.q.includes(q))continue}
c++;if(c>1500)continue;out.push('<tr><td class="m">#'+r.id+'<br>'+r.f+'<br>'+r.l+'<span class="sp">'+r.sp+(r.vo?' <span class="vo">♪음성</span>':'')+'</span></td><td class="ja">'+r.ja+'</td><td class="ko">'+r.ko+'</td><td class="en">'+r.en+'</td></tr>')}
t.innerHTML=out.join('');n.textContent=c+'줄'+(c>1500?' (앞 1500줄만 표시)':'')}
g.onchange=draw;s.oninput=draw;document.getElementById('e').onchange=e=>document.body.classList.toggle('showen',e.target.checked);draw();</script></body></html>
'''.replace('@@N@@', str(len(rows))).replace('@@OPTS@@', opts).replace('@@ROWS@@', json.dumps(rows, ensure_ascii=False))
os.makedirs(os.path.join(ROOT, 'work', 'review'), exist_ok=True)
p = os.path.join(ROOT, 'work', 'review', '번역본.html')
open(p, 'w', encoding='utf-8').write(page)
print(p, len(rows), '줄', {NAMES[k]: v for k, v in counts.items()})
