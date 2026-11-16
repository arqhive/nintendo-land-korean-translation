"""닌텐도 랜드 BFFNT 에 한글을 넣는다.

폰트 두 종류:
  * plain  (LunchMsg_A4, LunchRuby_A4): 채널 하나 = 글자 알파
  * packed (Lunch*_LA4Packed): 채널 하나에 채움(255)과 테두리(약 128)를 함께 구움.
      값 = 128*D + 127*F  (F=채움 0..1, D=채움을 반경 r 로 넓힌 것 0..1)
    → 한글도 채움을 그린 뒤 같은 식으로 테두리를 굽는다. r 은 원본에서 역산(fit_outline).

크기·굵기는 원본 한자(크기)·가나(획 굵기)의 '채움'만으로 잰다(테두리 제외).
원본 글자는 셀 비트맵·폭을 그대로 옮긴다(font_atlas.get_glyph → put_glyph).
"""
import os, sys, json, collections
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import bffnt_tool as bt, font_atlas as fa, font_render as fr

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 한글 글꼴: 티머니 둥근바람(사용자 결정 2026-11-06, noonnu 458). 굵기 400=Regular, 800=ExtraBold
FONT_DIR_KO = os.path.join(ROOT, 'tools', 'fonts')
fr.FONT_PATH = {400: os.path.join(FONT_DIR_KO, 'TmoneyRoundWindRegular.ttf'),
                800: os.path.join(FONT_DIR_KO, 'TmoneyRoundWindExtraBold.ttf')}
BODY_FONT = fr.FONT_PATH
# 숫자 폰트(G0·G1) 단위 글자: 원본이 붓글씨 느낌이라 안동 까투리(사용자 결정 2026-11-16)
UNIT_FONT = os.path.join(FONT_DIR_KO, 'AndongKaturi.ttf')
CALIB = os.path.join(ROOT, 'work', 'font_calib.json')
KANA = [chr(c) for c in list(range(0x3041, 0x3097)) + list(range(0x30A1, 0x30FB))]
HANZI = '任天堂遊対戦設定説明勝負画面選択開始終了確認全新島村山上手作見回体'


def is_packed(name):
    return 'Packed' in name


def has_kana(font):
    return any(ord(c) in font.charmap for c in 'あいうアイウ')


def fill_of(cell, packed):
    if not packed:
        return cell
    v = cell.astype(np.float32)
    return np.clip((v - 128) * 255 / 127, 0, 255).astype(np.uint8)


def dilate(F, r):
    """F: float 0..1. 반경 r(실수) 원판 그레이 팽창."""
    R = int(np.ceil(r + 1))
    H, W = F.shape
    P = np.pad(F, R)
    out = np.zeros_like(F)
    for dy in range(-R, R + 1):
        for dx in range(-R, R + 1):
            w = np.clip(r + 0.5 - np.hypot(dx, dy), 0, 1)
            if w <= 0:
                continue
            out = np.maximum(out, P[R + dy:R + dy + H, R + dx:R + dx + W] * w)
    return out


def compose(fill, r):
    F = fill.astype(np.float32) / 255
    D = np.maximum(dilate(F, r), F)
    return np.clip(np.rint(128 * D + 127 * F), 0, 255).astype(np.uint8)


def sample_cells(f, sheets, chars):
    return [fa.get_glyph(sheets, f, f.charmap[ord(c)]) for c in chars if ord(c) in f.charmap]


def fit_outline(f, sheets):
    cells = sample_cells(f, sheets, KANA[:40] + list(HANZI))
    best = None
    for r in np.arange(0.5, 6.01, 0.25):
        err = 0.0
        for c in cells:
            sim = compose(fill_of(c, True), r)
            err += np.abs(sim.astype(np.int32) - c.astype(np.int32)).mean()
        err /= len(cells)
        if best is None or err < best[1]:
            best = (float(r), err)
    return best


def measure(cells, packed):
    ink, wid, iw, ih, bot = [], [], [], [], []
    for c in cells:
        c = fill_of(c, packed)
        ink += fr.stem_ink(c); wid += fr.stems(c)
        bb = fr.ink_bbox(c)
        if bb:
            iw.append(bb[2] - bb[0]); ih.append(bb[3] - bb[1]); bot.append(bb[3])
    med = lambda a: float(np.median(a)) if a else 0.0
    return dict(ink=float(np.mean(ink)) if ink else 0, wid=float(np.mean(wid)) if wid else 0,
                w=med(iw), h=med(ih), bot=med(bot))


def hanzi_char_w(f):
    cnt = collections.Counter()
    for code, g in f.charmap.items():
        if 0x4E00 <= code <= 0x9FFF and g in f.widths:
            cnt[f.widths[g][2]] += 1
    return cnt.most_common(1)[0][0] if cnt else min(f.max_char_w, f.cell_w)


def calibrate(path):
    name = os.path.basename(path)[:-6]
    f = bt.load(path); sheets = fa.decode_sheets(f); packed = is_packed(name)
    fr.MAXRUN[0] = max(6, f.cell_h // 8)
    kana = measure(sample_cells(f, sheets, KANA), packed)
    hanzi = measure(sample_cells(f, sheets, HANZI), packed)
    cw = hanzi_char_w(f)
    r = fit_outline(f, sheets) if packed else (0.0, 0.0)
    margin = int(np.ceil(r[0]))
    best = None
    for size in range(max(6, f.cell_h // 2), f.cell_h + 6):
        cells = [fr.render(ch, size, 500, f.cell_w, f.cell_h, cw) for ch in fr.REF_HANGUL[:20]]
        m = measure(cells, False)
        if m['h'] + 2 * margin > f.cell_h or m['w'] + 2 * margin > cw:
            continue
        s = abs(m['w'] - hanzi['w']) + 0.7 * abs(m['h'] - hanzi['h'])
        if best is None or s < best[0]:
            best = (s, size)
    size = best[1]
    bw = None
    for wght in (sorted(fr.FONT_PATH) if isinstance(fr.FONT_PATH, dict) else range(300, 901, 50)):
        cells = [fr.render(ch, size, wght, f.cell_w, f.cell_h, cw) for ch in fr.REF_HANGUL]
        m = measure(cells, False)
        cnt = collections.Counter(v for c in cells for v in fr.stems(c))
        mode = cnt.most_common(1)[0][1] / max(1, sum(cnt.values())) if cnt else 0
        s = 2.0 * fr._pen(m['ink'], kana['ink']) + 0.5 * fr._pen(m['wid'], kana['wid']) + 0.5 * (1 - mode)
        if bw is None or s < bw[0]:
            bw = (s, wght, m)
    res = dict(size=size, wght=bw[1], char_w=cw, baseline=int(round(hanzi['bot'])), outline_r=r[0],
               outline_err=round(float(r[1]), 2), kana_ink=round(kana['ink'], 2), hangul_ink=round(bw[2]['ink'], 2),
               hanzi_wh=[hanzi['w'], hanzi['h']], hangul_wh=[bw[2]['w'], bw[2]['h']])
    print('%-24s %s' % (name, res))
    return name, res


def calibrate_unit(path, unit_chars='개명분위점트회히'):
    """숫자 폰트(G0·G1): 가나가 없어 단위 한자(点·回)로 크기를, 숫자+단위 한자로 테두리를 잰다. 굵기는 ExtraBold 고정.
    단위 글자가 숫자 폰트로 찍혀 한글판에서 「?」가 나온 일(닌자성 연속 횟수, 2026-11-16 실기)로 추가."""
    name = os.path.basename(path)[:-6]
    fr.FONT_PATH = {800: UNIT_FONT}
    f = bt.load(path); sheets = fa.decode_sheets(f)
    ref = [c for c in '点回' if ord(c) in f.charmap]
    hanzi = measure(sample_cells(f, sheets, ref), True)
    cw = f.widths[f.charmap[ord(ref[0])]][2]
    cells = sample_cells(f, sheets, '0123456789' + ''.join(ref))
    best_r = None
    for r in np.arange(0.5, 8.01, 0.25):
        err = sum(np.abs(compose(fill_of(c, True), r).astype(np.int32) - c.astype(np.int32)).mean() for c in cells) / len(cells)
        if best_r is None or err < best_r[1]:
            best_r = (float(r), err)
    margin = int(np.ceil(best_r[0]))
    best = None
    for size in range(max(6, f.cell_h // 2), f.cell_h + 6):
        m = measure([fr.render(ch, size, 800, f.cell_w, f.cell_h, cw) for ch in fr.REF_HANGUL[:20]], False)
        if m['h'] + 2 * margin > f.cell_h or m['w'] + 2 * margin > cw:
            continue
        s = abs(m['w'] - hanzi['w']) + 0.7 * abs(m['h'] - hanzi['h'])
        if best is None or s < best[0]:
            best = (s, size, m)
    # 붓글씨 글꼴은 글자마다 위아래가 들쭉날쭉하다 → 실제로 쓸 글자의 채움 위아래를 재서
    # 테두리까지 칸 안에 들어오게 크기를 줄이고, 한자 채움 가운데에 맞춰 기준선을 옮긴다.
    size, base = best[1], int(round(hanzi['bot']))
    cen = hanzi['bot'] - hanzi['h'] / 2
    while True:
        ys = [np.where(c.max(1) > 0)[0] for c in (fr.render(ch, size, 800, f.cell_w, f.cell_h, cw, baseline=base) for ch in unit_chars)]
        top, bot = min(y[0] for y in ys), max(y[-1] for y in ys)
        if bot - top + 1 + 2 * margin <= f.cell_h:
            break
        size -= 1
    shift = int(round(cen - (top + bot) / 2))
    shift = max(margin - top, min(f.cell_h - 1 - margin - bot, shift))
    base = int(base + shift)
    res = dict(size=int(size), wght=800, char_w=cw, baseline=base, outline_r=best_r[0],
               outline_err=round(float(best_r[1]), 2), hanzi_wh=[hanzi['w'], hanzi['h']], hangul_wh=[best[2]['w'], best[2]['h']],
               font=os.path.basename(UNIT_FONT), note='단위 한자(%s) 기준' % ''.join(ref))
    fr.FONT_PATH = BODY_FONT
    print('%-24s %s' % (name, res))
    return name, res


def load_calib():
    return json.load(open(CALIB, encoding='utf-8')) if os.path.exists(CALIB) else {}


def render_hangul(ch, f, st, packed):
    fr.FONT_PATH = {st['wght']: os.path.join(FONT_DIR_KO, st['font'])} if st.get('font') else BODY_FONT
    try:
        cell = fr.render(ch, st['size'], st['wght'], f.cell_w, f.cell_h, st['char_w'], baseline=st['baseline'])
    finally:
        fr.FONT_PATH = BODY_FONT
    return compose(cell, st['outline_r']) if packed else cell


def rebuild(path, add_chars, keep_all=True, keep_chars=None):
    """원본 글자(전부 또는 keep_chars)를 그대로 옮기고 add_chars 의 한글을 새로 그린다."""
    name = os.path.basename(path)[:-6]
    f = bt.load(path); src = fa.decode_sheets(f); packed = is_packed(name)
    st = load_calib()[name]
    if keep_all:
        keep = sorted(f.charmap, key=lambda c: f.charmap[c])
    else:
        keep = sorted(ord(c) for c in keep_chars if ord(c) in f.charmap)
    new = sorted({ord(c) for c in add_chars if ord(c) not in f.charmap and 0xAC00 <= ord(c) <= 0xD7A3})
    order = keep + new
    nsheets = max(f.num_sheets if keep_all else 1, -(-len(order) // f.per_sheet))
    sheets = [np.zeros((f.sheet_h, f.sheet_w), np.uint8) for _ in range(nsheets)]
    widths, cmap = {}, {}
    for i, code in enumerate(order):
        cmap[code] = i
        if code in f.charmap:
            g = f.charmap[code]
            fa.put_glyph(sheets, f, i, fa.get_glyph(src, f, g))
            widths[i] = f.widths.get(g, (f.def_left, f.def_glyph_w, f.def_char_w))
        else:
            fa.put_glyph(sheets, f, i, render_hangul(chr(code), f, st, packed))
            widths[i] = (0, st['char_w'], st['char_w'])
    if f.alter_index not in range(len(order)):
        f.alter_index = 0
    else:
        old_alt_code = next((c for c, g in f.charmap.items() if g == f.alter_index), None)
        f.alter_index = cmap.get(old_alt_code, 0)
    data = f.build(sheets=fa.encode_sheets(sheets), widths=widths, cmaps=[bt.CMAP.scan(cmap)])
    return data, dict(name=name, kept=len(keep), hangul=len(new), sheets=nsheets, orig_sheets=f.num_sheets)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1] == 'calib':
        res = load_calib()
        for p in bt.all_fonts():
            f = bt.load(p)
            if not has_kana(f):
                continue
            n, r = calibrate(p); res[n] = r
        json.dump(res, open(CALIB, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
