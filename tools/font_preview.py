"""원본 글자 | 새 한글을 한 줄로 이어 붙여 폰트별 비교 그림(work/font_preview/cmp_*.png)."""
import sys, os
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
import bffnt_tool as bt, font_atlas as fa, nl_font as nf
OUT = os.path.join(nf.ROOT, 'work', 'font_preview'); os.makedirs(OUT, exist_ok=True)
ORIG = 'あそぶ設定対戦ゼルダの伝説'
KO = '놀기설정대전젤다의전설한글'
cal = nf.load_calib()
for p in bt.all_fonts():
    name = os.path.basename(p)[:-6]
    if name not in cal: continue
    f = bt.load(p); sh = fa.decode_sheets(f); packed = nf.is_packed(name); st = cal[name]
    row = []
    for c in ORIG:
        g = f.charmap.get(ord(c)); w = f.widths[g][2] if g is not None else st['char_w']
        row.append(fa.get_glyph(sh, f, g)[:, :max(w, 1)] if g is not None else np.zeros((f.cell_h, w), np.uint8))
    row.append(np.full((f.cell_h, 4), 60, np.uint8))
    for c in KO:
        row.append(nf.render_hangul(c, f, st, packed)[:, :st['char_w']])
    img = np.hstack(row)
    sc = max(1, 60 // f.cell_h)
    Image.fromarray(img).resize((img.shape[1] * sc, img.shape[0] * sc), Image.NEAREST).save(os.path.join(OUT, 'cmp_%s.png' % name))
print(OUT)
