"""2단계 출력 시험 빌드.

work/test_strings.json 의 문구를 원문 대신 넣고, 그 한글을 폰트 4개(Msg·M·L·Ruby)에 추가한다.
산출물(work/build/test/):
  sdcafiine/0005000010101F00/NintendoLandKR/content/JpJapanese/...   (Aroma SDCafiine)
  cemu/NintendoLand_KR_Test/rules.txt + content/JpJapanese/...       (Cemu 그래픽 팩)
"""
import sys, os, json, shutil, hashlib
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from nlib import *
import bffnt_tool as bt, font_atlas as fa, nl_font as nf

ROOT = nf.ROOT
UPD = os.path.join(ROOT, 'Nintendo Land [Update] [0005000e10101f00]', 'content', 'JpJapanese')
OUT = os.path.join(ROOT, 'work', 'build', 'test')
FONTS_WITH_HANGUL = ['LunchMsg_A4', 'LunchM_LA4Packed', 'LunchL_LA4Packed', 'LunchRuby_A4']


def ext_align(data):
    info, files = sarc_read(data); lay = dict(sarc_layout(data)); al = {}
    for n, s in lay.items():
        ex = os.path.splitext(n)[1]
        a = next(a for a in (0x2000, 0x1000, 0x800, 0x400, 0x200, 0x100, 0x80, 0x40, 0x20, 0x10, 8, 4) if s % a == 0)
        al[ex] = min(al.get(ex, 0x2000), a)
    return info, files, al


def repack(orig, replace):
    """orig SARC 바이트, replace {이름: 새 바이트} -> 같은 정렬·순서로 다시 묶음"""
    info, files, al = ext_align(orig)
    return sarc_write([(n, replace.get(n, b)) for n, b, _ in files], info['mult'], info['endian'],
                      info['data_off'], lambda n, b: al[os.path.splitext(n)[1]], info['ver'])


def build_messages(tests):
    raw = yaz0_decompress(open(os.path.join(UPD, 'Message', 'AllMessage.szs'), 'rb').read())
    hit = set(); outer_rep = {}
    for on, ob, _ in sarc_read(raw)[1]:
        inner_rep = {}
        for x, bb, _ in sarc_read(ob)[1]:
            base = x.split('/')[-1]
            keys = [k for k in tests if k.split('|')[0] == base]
            if not keys:
                continue
            m = msbt_read(bb); lab2idx = {v: k for k, v in m['labels'].items()}
            texts = list(m['texts'])
            for k in keys:
                lab = k.split('|')[1]
                texts[lab2idx[lab]] = str_to_msbt(tests[k], m['endian']); hit.add(k)
            inner_rep[x] = msbt_write(m, texts)
        if inner_rep:
            outer_rep[on] = repack(ob, inner_rep)
    miss = set(tests) - hit
    assert not miss, miss
    new = repack(raw, outer_rep)
    # 검증: 바꾼 줄만 달라졌는지
    changed = same = 0
    A = {x: bb for _, ob, _ in sarc_read(raw)[1] for x, bb, _ in sarc_read(ob)[1]}
    B = {x: bb for _, ob, _ in sarc_read(new)[1] for x, bb, _ in sarc_read(ob)[1]}
    assert A.keys() == B.keys()
    for x in A:
        ta, tb = msbt_read(A[x])['texts'], msbt_read(B[x])['texts']
        assert len(ta) == len(tb)
        for a, b in zip(ta, tb):
            if a == b: same += 1
            else: changed += 1
    print('메시지: 바뀐 줄 %d (시험 문구 %d), 그대로 %d' % (changed, len(tests), same))
    assert changed == len(tests)
    return new


def build_fonts(chars):
    raw = yaz0_decompress(open(os.path.join(UPD, 'Layout', 'Font.szs'), 'rb').read())
    rep = {}
    for n, b, _ in sarc_read(raw)[1]:
        name = n[:-6]
        if name not in FONTS_WITH_HANGUL:
            continue
        path = os.path.join(bt.FONT_DIR, n)
        assert open(path, 'rb').read() == b, '추출본이 업데이트판과 다름: ' + n
        data, st = nf.rebuild(path, chars)
        # 검증: 원본 글자 모양 보존(BC4 손실 허용), 새 한글이 비지 않음
        old, new = bt.BFFNT(b), bt.BFFNT(data)
        os_, ns = fa.decode_sheets(old), fa.decode_sheets(new)
        bad = 0
        for code, g in old.charmap.items():
            d = np.abs(fa.get_glyph(os_, old, g).astype(int) - fa.get_glyph(ns, new, new.charmap[code]).astype(int)).max()
            bad += d > 24
        blank = sum(1 for c in chars if 0xAC00 <= ord(c) <= 0xD7A3 and fa.get_glyph(ns, new, new.charmap[ord(c)]).max() == 0)
        print('폰트 %-20s 원본 %4d + 한글 %3d, 시트 %d→%d, 원본 글자 어긋남 %d, 빈 한글 %d, %d→%d바이트'
              % (name, st['kept'], st['hangul'], st['orig_sheets'], st['sheets'], bad, blank, len(b), len(data)))
        assert bad == 0 and blank == 0
        rep[n] = data
    return repack(raw, rep)


def main():
    tests = {k: v for k, v in json.load(open(os.path.join(ROOT, 'work', 'test_strings.json'), encoding='utf-8')).items() if not k.startswith('_')}
    chars = set(''.join(tests.values()))
    msg = build_messages(tests)
    font = build_fonts(chars)
    files = {}
    for rel, data in (('Message/AllMessage.szs', msg), ('Layout/Font.szs', font)):
        z = yaz0_compress(data)
        assert yaz0_decompress(z) == data
        files[rel] = z
        print('%-24s %8d바이트  md5 %s' % (rel, len(z), hashlib.md5(z).hexdigest()))
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    sd = os.path.join(OUT, 'sdcafiine', '0005000010101F00', 'NintendoLandKR', 'content', 'JpJapanese')
    cemu_root = os.path.join(OUT, 'cemu', 'NintendoLand_KR_Test')
    cm = os.path.join(cemu_root, 'content', 'JpJapanese')
    for base in (sd, cm):
        for rel, z in files.items():
            p = os.path.join(base, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(z)
    open(os.path.join(cemu_root, 'rules.txt'), 'w', encoding='utf-8').write(
        '[Definition]\ntitleIds = 0005000010101F00\nname = Korean Test\npath = "Nintendo Land/Mods/Korean Test"\n'
        'description = 닌텐도 랜드 한글 출력 시험\nversion = 6\n')
    print('->', OUT)


if __name__ == '__main__':
    main()
