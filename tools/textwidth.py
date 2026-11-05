"""글자 폭 계산(NW4F TextWriter 방식): 한 줄 폭 = Σ char_w × (fontSize.x / FINF.width) + charSpace × (글자 수 - 1).
줄 높이 = (FINF.lineFeed + lineSpace) × (fontSize.y / FINF.height)."""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import bffnt_tool as bt
_F = {}
def font(name):
    name = name[:-6] if name.endswith('.bffnt') else name
    if name not in _F:
        p = os.path.join(bt.FONT_DIR, name + '.bffnt')
        _F[name] = bt.load(p) if os.path.exists(p) else None
    return _F[name]
HANGUL_W = {}   # 폰트별 한글 폭(빌드 후 값) — nl_font 의 char_w
def char_w(f, c, name=None):
    g = f.charmap.get(ord(c))
    if g is None:
        if 0xAC00 <= ord(c) <= 0xD7A3 and name in HANGUL_W:
            return HANGUL_W[name]
        g = f.alter_index
    return f.widths.get(g, (f.def_left, f.def_glyph_w, f.def_char_w))[2]
TAG = re.compile(r'\{[^}]*\}')
def plain(s):
    return TAG.sub('', s)
def line_widths(text, fontname, fsize, cspace):
    f = font(fontname)
    if f is None:
        return None
    sx = fsize[0] / f.width
    out = []
    for ln in plain(text).split('\n'):
        n = len(ln)
        out.append(sum(char_w(f, c, fontname[:-6] if fontname.endswith('.bffnt') else fontname) for c in ln) * sx + cspace * max(0, n - 1))
    return out
def line_height(fontname, fsize, lspace):
    f = font(fontname)
    return (f.line_feed + lspace) * (fsize[1] / f.height) if f else None
