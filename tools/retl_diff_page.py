"""다시 번역(11/17) 대조표: 마지막 커밋과 지금 translation/ko 를 비교해 바뀐 줄만 HTML 표로.
출력: work/review/다시번역_대조표.html (원문이 들어 있어 git 제외 폴더)
"""
import os, sys, json, re, html, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = sys.argv[1] if len(sys.argv) > 1 else 'HEAD'
tl = {r['id']: r for r in json.load(open(os.path.join(ROOT, 'translation', 'messages.json'), encoding='utf-8'))}
GROUPS = [('ttl', '타이틀·모니타 안내'), ('common_msg', '공용 메시지·조작 팁'), ('common_layout', '메뉴·화면 글'),
          ('statue', '석상 설명'), ('pkm_mtr', '피크민·메트로이드'), ('attractions', '나머지 어트랙션')]
ICON = re.compile(r'[-]')


def show(s):
    s = re.sub(r'\{0:3:0002\}', '⟨', s); s = s.replace('{0:3:ffff}', '⟩')
    s = re.sub(r'\{[^}]*\}', '▢', s)
    s = ICON.sub('Ⓘ', s)
    return html.escape(s).replace('\n', '<br>')


rows = []; total = 0
for g, title in GROUPS:
    old = {e['id']: e['ko'] for e in json.loads(subprocess.run(['git', '-C', ROOT, 'show', '%s:translation/ko/%s.json' % (REF, g)], capture_output=True).stdout)}
    cur = json.load(open(os.path.join(ROOT, 'translation', 'ko', '%s.json' % g), encoding='utf-8'))
    ch = [e for e in cur if old.get(e['id']) != e['ko']]
    total += len(ch)
    rows.append('<h2 id="%s">%s <small>%d줄</small></h2><table><thead><tr><th>#</th><th>화자</th><th>원문</th><th>이전</th><th>지금</th></tr></thead><tbody>' % (g, title, len(ch)))
    for i, e in enumerate(ch, 1):
        r = tl[e['id']]
        rows.append('<tr><td class="n">%d<br><span>%d</span></td><td class="sp">%s</td><td class="ja">%s</td><td class="old">%s</td><td class="new">%s</td></tr>'
                    % (i, e['id'], html.escape((r.get('speaker') or '').split('→')[0]), show(r['ja']), show(old[e['id']]), show(e['ko'])))
    rows.append('</tbody></table>')
nav = ' · '.join('<a href="#%s">%s</a>' % (g, t) for g, t in GROUPS)
page = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>다시 번역 대조표</title><style>
body{font-family:"Malgun Gothic",sans-serif;margin:16px;background:#fafafa;color:#222}
h1{font-size:20px}h2{font-size:17px;margin-top:28px}small{color:#888;font-weight:normal}
.note{color:#555;font-size:13px}nav{position:sticky;top:0;background:#fafafa;padding:6px 0;font-size:14px}
table{border-collapse:collapse;width:100%;font-size:14px;background:#fff}
th,td{border:1px solid #ddd;padding:6px 8px;vertical-align:top}th{background:#eee;position:sticky;top:30px}
td.n{color:#999;width:3em;font-size:12px}td.n span{font-size:10px}td.sp{width:5em;font-size:12px;color:#666}
td.ja{color:#555;width:28%}td.old{color:#a33;width:30%}td.new{color:#063;width:30%;font-weight:600}
</style><h1>다시 번역 대조표 <small>바뀐 줄 ''' + str(total) + '''줄</small></h1>
<p class="note">⟨…⟩ 색 글씨 · ▢ 변수(이름·숫자) · Ⓘ 버튼 아이콘 · 빨강 = 이전, 초록 = 지금</p><nav>''' + nav + '</nav>' + ''.join(rows)
os.makedirs(os.path.join(ROOT, 'work', 'review'), exist_ok=True)
out = os.path.join(ROOT, 'work', 'review', '다시번역_대조표.html')
open(out, 'w', encoding='utf-8').write(page)
print(out, total)
