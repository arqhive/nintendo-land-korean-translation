"""전체 빌드: 메시지 + 폰트 + 그림 → work/build/<버전>/sdcafiine/0005000010101F00/NintendoLandKR/content/...

사용: python -I tools/build.py v0.1 [--sd D:]
  --sd 를 주면 SD 의 같은 경로에 복사하고 MD5 대조(사용자가 SD 를 시킬 때만 쓴다)

출력 4개(SDCafiine 은 경로가 같은 파일을 통째로 바꿔치기):
  content/JpJapanese/Message/AllMessage.szs   (업데이트판 기준)
  content/JpJapanese/Layout/Font.szs          (업데이트판 기준)
  content/Common/Package/Nzm_Cmn.pack         (본편, 기술 띠 그림 3장)
  content/Common/Package/Static2.pack         (업데이트판, 로고·그림자 8개)
"""
import os, sys, json, re, shutil, hashlib, time
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from nlib import *
import build_test as bt
import nl_apply
import bffnt_tool as bf, font_atlas as fa, nl_font as nf

ROOT = nf.ROOT
GAME = os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]')
UPD = os.path.join(ROOT, 'Nintendo Land [Update] [0005000e10101f00]')
TAG = re.compile(r'\{[^}]*\}')
HANGUL_FONTS = ['LunchMsg_A4', 'LunchM_LA4Packed', 'LunchL_LA4Packed', 'LunchRuby_A4']
BASE_CHARS = (''.join(chr(c) for c in range(0x20, 0x7F)) + ''.join(chr(c) for c in range(0xFF01, 0xFF5F))
              + ''.join(chr(c) for c in range(0x3041, 0x3097)) + ''.join(chr(c) for c in range(0x30A1, 0x30FD))
              + '　、。・ー〜～…‥「」『』（）［］【】〈〉《》！？：；／＼％＆＊＋－＝＜＞·©®™♪★☆○●◆◇□■△▲▽▼→←↑↓×÷')


def final_texts():
    tl = json.load(open(os.path.join(ROOT, 'translation', 'messages.json'), encoding='utf-8'))
    out = {}
    for r in tl:
        k = r['file'] + '|' + (r['label'] or str(r['idx']))
        if not r.get('skip') and r.get('ko'):
            out[k] = (r, r['ko'])
        else:
            out[k] = (r, None)
    return tl, out


# ---------------------------------------------------------------- 메시지
def build_messages(tl):
    by = {(r['file'], r['idx']): r for r in tl}
    raw = yaz0_decompress(open(os.path.join(UPD, 'content/JpJapanese/Message/AllMessage.szs'), 'rb').read())
    rep = {}; n_ko = 0
    for on, ob, _ in sarc_read(raw)[1]:
        for x, bb, _ in sarc_read(ob)[1]:
            key_file = on[:-5] + '/' + x
            m = msbt_read(bb); texts = list(m['texts']); ch = False
            for i in range(len(texts)):
                r = by.get((key_file, i))
                if r and not r.get('skip') and r.get('ko'):
                    texts[i] = str_to_msbt(r['ko'], m['endian']); ch = True; n_ko += 1
            if ch:
                rep[on + '/' + x] = msbt_write(m, texts)
    new = yaz0_decompress(nl_apply.apply_msg(open(os.path.join(UPD, 'content/JpJapanese/Message/AllMessage.szs'), 'rb').read(), rep))
    # 검증: 번역 줄만 바뀌었는지
    A = {(on, x): msbt_read(bb)['texts'] for on, ob, _ in sarc_read(raw)[1] for x, bb, _ in sarc_read(ob)[1]}
    B = {(on, x): msbt_read(bb)['texts'] for on, ob, _ in sarc_read(new)[1] for x, bb, _ in sarc_read(ob)[1]}
    assert A.keys() == B.keys()
    changed = sum(1 for k in A for a, b in zip(A[k], B[k]) if a != b)
    print('메시지: 번역 넣은 줄 %d, 실제 바뀐 줄 %d, 바뀐 msbt %d개' % (n_ko, changed, len(rep)))
    return rep


# ---------------------------------------------------------------- 폰트
ALIAS = {'·': '・'}      # 한국어 가운뎃점 → 일본어 가운뎃점 그림(M 폰트에는 · 가 없음)


def add_alias(data, chars):
    f = bf.BFFNT(data); cm = dict(f.charmap); added = []
    for a, src in ALIAS.items():
        if a in chars and ord(a) not in cm and ord(src) in cm:
            cm[ord(a)] = cm[ord(src)]; added.append(a)
    if not added:
        return data
    return f.build(cmaps=[bf.CMAP.scan(cm)])


def font_char_sets(tl):
    wm = json.load(open(os.path.join(ROOT, 'work', 'survey', 'winmap.json'), encoding='utf-8'))
    allc, Lc = set(BASE_CHARS), set('0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz !?.,:;+-/%()~…')
    for r in tl:
        s = r['ko'] if (not r.get('skip') and r.get('ko')) else r['ja']
        p = set(TAG.sub('', s)) - {'\n'}
        allc |= p
        m = wm[r['file'] + '|' + (r['label'] or str(r['idx']))]
        if m['how'] == 'rel' or (m.get('font') or '').startswith('LunchL'):
            Lc |= p
    return allc, Lc


def build_fonts(tl):
    allc, Lc = font_char_sets(tl)
    raw = yaz0_decompress(open(os.path.join(UPD, 'content/JpJapanese/Layout/Font.szs'), 'rb').read())
    rep = {}
    for n, b, _ in sarc_read(raw)[1]:
        name = n[:-6]
        if name not in HANGUL_FONTS:
            continue
        path = os.path.join(bf.FONT_DIR, n)
        assert open(path, 'rb').read() == b
        chars = Lc if name == 'LunchL_LA4Packed' else allc
        f0 = bf.BFFNT(b)
        keep = {chr(c) for c in f0.charmap if chr(c) in chars or 0xE000 <= c <= 0xF8FF}   # 아이콘 글자는 항상
        for a, src in ALIAS.items():            # 번역문 글자가 폰트에 없고 같은 모양 글자가 있으면 그 글자도 남김
            if a in chars and ord(a) not in f0.charmap and ord(src) in f0.charmap:
                keep.add(src)
        data, st = nf.rebuild(path, chars, keep_all=False, keep_chars=keep)
        data = add_alias(data, chars)
        new = bf.BFFNT(data); ns = fa.decode_sheets(new); os_ = fa.decode_sheets(f0)
        bad = sum(1 for c in keep if np.abs(fa.get_glyph(os_, f0, f0.charmap[ord(c)]).astype(int) - fa.get_glyph(ns, new, new.charmap[ord(c)]).astype(int)).max() > 24)
        hg = [c for c in chars if '가' <= c <= '힣']
        miss = [c for c in hg if ord(c) not in new.charmap]
        blank = sum(1 for c in hg if fa.get_glyph(ns, new, new.charmap[ord(c)]).max() == 0)
        print('폰트 %-20s 원본 글자 %4d 중 유지 %4d + 한글 %4d = %4d, 시트 %d→%d, 크기 %.1f→%.1fMB, 어긋남 %d, 빠진 한글 %d, 빈 한글 %d'
              % (name, len(f0.charmap), st['kept'], st['hangul'], st['kept'] + st['hangul'], st['orig_sheets'], st['sheets'], len(b) / 1e6, len(data) / 1e6, bad, len(miss), blank))
        assert bad == 0 and not miss and blank == 0
        rep[n] = data
    rep.update(build_unit_fonts(tl, raw))
    return rep


# 숫자 폰트: 점수·횟수 상자의 태그가 UnitName·Rank·Format 문장을 끼워 넣는다(닌자성 「○回」→「회」).
# 원본 글자는 전부 그대로 두고, 그 세 파일의 한글만 더한다(2026-11-16 실기에서 「?」 상자 제보).
UNIT_FONTS = ['LunchG0_LA4Packed', 'LunchG1_LA4Packed']
UNIT_FILES = ('UnitName.msbt', 'Rank.msbt', 'Format.msbt')


def build_unit_fonts(tl, raw):
    chars = set()
    for r in tl:
        if r['file'].split('/')[-1] in UNIT_FILES and not r.get('skip') and r.get('ko'):
            chars |= {c for c in TAG.sub('', r['ko']) if '가' <= c <= '힣'}
    rep = {}
    for n, b, _ in sarc_read(raw)[1]:
        name = n[:-6]
        if name not in UNIT_FONTS:
            continue
        path = os.path.join(bf.FONT_DIR, n)
        assert open(path, 'rb').read() == b
        f0 = bf.BFFNT(b)
        data, st = nf.rebuild(path, chars, keep_all=True)
        new = bf.BFFNT(data); ns = fa.decode_sheets(new); os_ = fa.decode_sheets(f0)
        bad = sum(1 for c, g in f0.charmap.items() if np.abs(fa.get_glyph(os_, f0, g).astype(int) - fa.get_glyph(ns, new, new.charmap[c]).astype(int)).max() > 24)
        miss = [c for c in chars if ord(c) not in new.charmap]
        blank = sum(1 for c in chars if fa.get_glyph(ns, new, new.charmap[ord(c)]).max() == 0)
        print('폰트 %-20s 원본 글자 %4d 전부 유지 + 한글 %d(%s), 시트 %d→%d, 어긋남 %d, 빠진 한글 %d, 빈 한글 %d'
              % (name, len(f0.charmap), st['hangul'], ''.join(sorted(chars)), st['orig_sheets'], st['sheets'], bad, len(miss), blank))
        assert bad == 0 and not miss and blank == 0 and st['sheets'] == st['orig_sheets']
        rep[n] = data
    return rep


# ---------------------------------------------------------------- 그림
def build_pack(top, rel, manifest):
    raw = open(os.path.join(top, rel), 'rb').read()
    items = [m for m in manifest if m['path'].split('//')[0] == rel]
    by_szs = {}
    for m in items:
        parts = m['path'].split('//')          # pack // szs // arc // timg/x.bflim
        by_szs.setdefault(parts[1], {}).setdefault(parts[2], {})[parts[3]] = open(os.path.join(ROOT, m['file']), 'rb').read()
    new = nl_apply.apply_pack(raw, by_szs)
    # 검증: 바꾼 szs 외에는 바이트 같고, 바뀐 szs 는 헤더(정렬값)가 원본과 같음
    A = {n: b for n, b, _ in sarc_read(raw)[1]}; B = {n: b for n, b, _ in sarc_read(new)[1]}
    assert A.keys() == B.keys()
    diff = [n for n in A if A[n] != B[n]]
    assert sorted(diff) == sorted(by_szs), diff
    for n in diff:
        assert B[n][8:16] == A[n][8:16], n
        print('그림: %s 안 %s %d장 교체, 다시 압축 %d→%d' % (rel.split('/')[-1], n.split('/')[-1], sum(len(v) for v in by_szs[n].values()), len(A[n]), len(B[n])))
    return new, by_szs


# 바깥 파일: 결과 경로(content 기준) / 원본이 본편(game)·업데이트(update) 중 어디 / 원본 경로 / 적용 방식
TARGETS = [dict(out='content/JpJapanese/Message/AllMessage.szs', src='content/JpJapanese/Message/AllMessage.szs', **{'from': 'update'}, kind='msg'),
           dict(out='content/JpJapanese/Layout/Font.szs', src='content/JpJapanese/Layout/Font.szs', **{'from': 'update'}, kind='font'),
           dict(out='content/Common/Package/Nzm_Cmn.pack', src='content/Common/Package/Nzm_Cmn.pack', **{'from': 'game'}, kind='pack'),
           dict(out='content/Common/Package/Static2.pack', src='content/Common/Package/Static2.pack', **{'from': 'update'}, kind='pack')]


def flat(rep):
    """교체 목록을 (경로 키, 바이트) 목록으로. 그림 묶음은 'szs//arc//timg' 키"""
    out = []
    for k, v in sorted(rep.items()):
        if isinstance(v, dict):
            out += [(k + '//' + k2, v2) for k2, v2 in flat(v)]
        else:
            out.append((k, v))
    return out


def save_payload(root, ver, src, files, reps):
    """배포 패처용: 바뀐 안쪽 파일만(원본 게임 파일 통째는 담지 않음) + 원본·결과 SHA-1"""
    if os.path.isdir(root):
        shutil.rmtree(root)
    os.makedirs(root)
    man = dict(version=ver, title_id='0005000010101F00', targets=[])
    for i, t in enumerate(TARGETS):
        idx, off = [], 0
        with open(os.path.join(root, 't%d.bin' % i), 'wb') as f:
            for k, b in flat(reps[t['out']]):
                f.write(b); idx.append([k, off, len(b)]); off += len(b)
        man['targets'].append(dict(t, part='t%d' % i, entries=idx, src_size=len(src[t['out']]), src_sha1=hashlib.sha1(src[t['out']]).hexdigest(),
                                   out_size=len(files[t['out']]), out_sha1=hashlib.sha1(files[t['out']]).hexdigest()))
        print('패치 데이터 %-40s 안쪽 %3d개 %.2fMB' % (t['out'].split('/')[-1], len(idx), off / 1e6))
    json.dump(man, open(os.path.join(root, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


def main():
    ver = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith('--') else 'v0.1'
    sd = sys.argv[sys.argv.index('--sd') + 1] if '--sd' in sys.argv else None
    t0 = time.time()
    tl, _ = final_texts()
    manifest = json.load(open(os.path.join(ROOT, 'work', 'gfx_out', 'manifest.json'), encoding='utf-8'))
    src = {t['out']: open(os.path.join(GAME if t['from'] == 'game' else UPD, t['src']), 'rb').read() for t in TARGETS}
    msg_rep = build_messages(tl); font_rep = build_fonts(tl)
    nzm, nzm_rep = build_pack(GAME, 'content/Common/Package/Nzm_Cmn.pack', manifest)
    st2, st2_rep = build_pack(UPD, 'content/Common/Package/Static2.pack', manifest)
    files = {
        'content/JpJapanese/Message/AllMessage.szs': nl_apply.apply_msg(src['content/JpJapanese/Message/AllMessage.szs'], msg_rep),
        'content/JpJapanese/Layout/Font.szs': nl_apply.apply_font(src['content/JpJapanese/Layout/Font.szs'], font_rep),
        'content/Common/Package/Nzm_Cmn.pack': nzm,
        'content/Common/Package/Static2.pack': st2,
    }
    for rel, data in files.items():
        if data[:4] == b'Yaz0':
            assert data[8:16] == src[rel][8:16], rel        # 압축 헤더 정렬값 = 원본
    reps = {'content/JpJapanese/Message/AllMessage.szs': msg_rep, 'content/JpJapanese/Layout/Font.szs': font_rep,
            'content/Common/Package/Nzm_Cmn.pack': nzm_rep, 'content/Common/Package/Static2.pack': st2_rep}
    for k in ('content/JpJapanese/Message/AllMessage.szs', 'content/JpJapanese/Layout/Font.szs'):
        assert sarc_read(yaz0_decompress(files[k]))   # 풀리는지
    out_root = os.path.join(ROOT, 'work', 'build', ver, 'sdcafiine', '0005000010101F00', 'NintendoLandKR')
    if os.path.isdir(os.path.dirname(os.path.dirname(out_root))):
        shutil.rmtree(os.path.dirname(os.path.dirname(out_root)))
    md5 = {}
    for rel, data in files.items():
        p = os.path.join(out_root, rel); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(data)
        md5[rel] = hashlib.md5(data).hexdigest()
        print('%-46s %10d바이트 md5 %s' % (rel, len(data), md5[rel]))
    json.dump(md5, open(os.path.join(ROOT, 'work', 'build', ver, 'md5.json'), 'w'), indent=1)
    save_payload(os.path.join(ROOT, 'work', 'build', ver, 'payload'), ver, src, files, reps)
    print('빌드 %s 끝 (%.0f초) → %s' % (ver, time.time() - t0, out_root))
    if sd:
        dst = os.path.join(sd + os.sep, 'wiiu', 'sdcafiine', '0005000010101F00', 'NintendoLandKR')
        for rel, data in files.items():
            p = os.path.join(dst, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
            shutil.copyfile(os.path.join(out_root, rel), p)
            ok = hashlib.md5(open(p, 'rb').read()).hexdigest() == md5[rel]
            print('SD %-46s %s' % (rel, '일치' if ok else '★불일치'))
            assert ok


if __name__ == '__main__':
    main()
