"""고유 그림을 검토용 접촉 시트로. 단색(모든 픽셀 같은 색, 알파 포함)·8px 이하는 기계 판정으로 따로 기록.
시트: work/survey/tex/sheets/sheet_NNN.png (칸 160px, 8×6), 칸 아래 번호. 목록 work/survey/tex/sheets.json"""
import os, sys, json
sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
T = os.path.join(ROOT, 'work', 'survey', 'tex')
rs = [json.loads(l) for l in open(os.path.join(T, 'index.jsonl'), encoding='utf-8')]
uniq = {r['id']: r for r in rs if 'id' in r}
auto, todo = {}, []
for i, r in sorted(uniq.items()):
    a = np.asarray(Image.open(os.path.join(T, 'img', '%05d.png' % i)).convert('RGBA'))
    if max(a.shape[:2]) <= 8:
        auto[i] = '8px 이하'; continue
    if (a == a[0, 0]).all():
        auto[i] = '단색'; continue
    todo.append(i)
CELL, COLS, ROWS = 160, 8, 6
os.makedirs(os.path.join(T, 'sheets'), exist_ok=True)
sheets = []
for s in range(0, len(todo), COLS * ROWS):
    ids = todo[s:s + COLS * ROWS]
    sh = Image.new('RGB', (COLS * CELL, ROWS * (CELL + 14)), (40, 40, 40))
    d = ImageDraw.Draw(sh)
    for k, i in enumerate(ids):
        im = Image.open(os.path.join(T, 'img', '%05d.png' % i)).convert('RGBA')
        bg = Image.new('RGBA', im.size, (110, 110, 110, 255)); bg.alpha_composite(im)
        bg.thumbnail((CELL - 4, CELL - 4))
        x, y = (k % COLS) * CELL, (k // COLS) * (CELL + 14)
        sh.paste(bg.convert('RGB'), (x + 2, y + 2))
        d.text((x + 2, y + CELL), '%d %dx%d' % (i, uniq[i]['w'], uniq[i]['h']), fill=(255, 255, 0))
    n = len(sheets); sh.save(os.path.join(T, 'sheets', 'sheet_%03d.png' % n)); sheets.append(ids)
json.dump(dict(auto=auto, sheets=sheets), open(os.path.join(T, 'sheets.json'), 'w', encoding='utf-8'))
print('고유 %d, 기계 판정 %d (단색 %d, 8px 이하 %d), 눈 검토 %d장 → 시트 %d개' % (len(uniq), len(auto), sum(v == '단색' for v in auto.values()), sum(v != '단색' for v in auto.values()), len(todo), len(sheets)))
