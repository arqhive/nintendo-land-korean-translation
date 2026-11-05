"""6단계 그림: GPT 결과 → 게임 BFLIM 7+2장 (원본과 같은 형식·타일 배치·헤더).

입력: graphics/GPT_요청/<폴더>/결과.png
출력: work/gfx_out/<텍스처 이름>.bflim  +  graphics/비교/최종_*.png (원본 | 한글, 게임에서 보이는 모양)
      work/gfx_out/manifest.json — 각 bflim 이 들어갈 묶음 경로(빌드 때 사용)

규칙(원본에서 역산, 2026-11-06):
  기술 띠(BC5 740×180): 부호 거리 sd(글자 안 +, 밖 -)
      R = 글자 안 255, 밖 0~20px 0, 그보다 멀면 255 (가장자리는 1px 부드럽게)
      G = sd > -9 이면 255, -9~-13 에서 0으로 선형
  큰 로고(BC3) = 결과 그대로(알파 250 이상은 255), 작은 로고(RGBA8) = 큰 로고를 알파 고려해 축소(LANCZOS, 0.3배)
  그림자(BC4) = 작은 로고 알파를 0.39배 BOX 축소, (3,3)/(4,2)에 놓고 가우스 0.5 (work/shadow_fit.json)
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
from scipy import ndimage
from nlib import yaz0_decompress, sarc_read
import texdec, gtx2, gtx_lib, addrlib, bc1

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPT = os.path.join(ROOT, 'graphics', 'GPT_요청')
OUT = os.path.join(ROOT, 'work', 'gfx_out')
CMP = os.path.join(ROOT, 'graphics', '비교')
GAME = os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]')
UPD = os.path.join(ROOT, 'Nintendo Land [Update] [0005000e10101f00]')

WAZA = 'content/Common/Package/Nzm_Cmn.pack//Common/Layout/Nzm_Waza_00.szs//Nzm_Waza_00.arc//timg/'
LOGO0 = 'content/Common/Package/Static2.pack//Common/Layout/AttractionLogo_00.szs//AttractionLogo_00.arc//timg/'
LOGO1 = 'content/Common/Package/Static2.pack//Common/Layout/AttractionLogo_01.szs//AttractionLogo_01.arc//timg/'


def leaf(path):
    """'a//b//c' 경로의 잎 바이트. 바깥 파일은 업데이트에 있으면 업데이트 쪽."""
    parts = path.split('//')
    top = os.path.join(UPD, parts[0]) if os.path.exists(os.path.join(UPD, parts[0])) else os.path.join(GAME, parts[0])
    data = open(top, 'rb').read()
    for p in parts[1:]:
        if data[:4] == b'Yaz0':
            data = yaz0_decompress(data)
        data = {n: b for n, b, _ in sarc_read(data)[1]}[p]
    return data, top


# ---------------------------------------------------------------- 인코딩
def _store(lin, W, H, fmt, tm, swz, size):
    """lin: (h, w, bpe) 선형 배치 → 저장 배치 바이트(원본 이미지 크기 size)"""
    bpp = addrlib.surfaceGetBitsPerPixel(fmt)
    pitch, ph = texdec._pitch(fmt, W, H, tm)
    h, w, bpe = lin.shape
    assert tm == 4, tm
    m = gtx2.addr_map(w, h, bpp, pitch, ph, swz)
    buf = np.zeros(max(size, int(m.max()) + bpe), np.uint8)
    buf[(m[..., None] + np.arange(bpe)).reshape(-1)] = lin.reshape(-1)
    return bytes(buf[:size])


def _pad4(img):
    H, W = img.shape[:2]
    h, w = -(-H // 4) * 4, -(-W // 4) * 4
    if (h, w) == (H, W):
        return img
    out = np.zeros((h, w) + img.shape[2:], img.dtype); out[:H, :W] = img
    out[H:, :W] = img[H - 1:H, :]; out[:, W:] = out[:, W - 1:W]
    return out


def encode(img, fmt, W, H, tm, swz, size):
    f6 = fmt & 0x3F
    if f6 == 0x1A:                                          # RGBA8
        return _store(img[:H, :W].astype(np.uint8), W, H, fmt, tm, swz, size)
    p = _pad4(img)
    bh, bw = p.shape[0] // 4, p.shape[1] // 4
    if f6 == 0x34:                                          # BC4 (1채널)
        lin = gtx_lib.bc4_encode_blocks(np.ascontiguousarray(p if p.ndim == 2 else p[..., 0]))
    elif f6 == 0x35:                                        # BC5 (R, G)
        r = gtx_lib.bc4_encode_blocks(np.ascontiguousarray(p[..., 0]))
        g = gtx_lib.bc4_encode_blocks(np.ascontiguousarray(p[..., 1]))
        lin = np.concatenate([r, g], -1)
    elif f6 == 0x33:                                        # BC3 = 알파 BC4 + 색 BC1
        a = gtx_lib.bc4_encode_blocks(np.ascontiguousarray(p[..., 3]))
        px = p[..., :3].reshape(bh, 4, bw, 4, 3).transpose(0, 2, 1, 3, 4).reshape(-1, 16, 3).astype(np.float32)
        c = bc1.encode_blocks(px).reshape(bh, bw, 8)
        lin = np.concatenate([a, c], -1)
    else:
        raise NotImplementedError(hex(fmt))
    return _store(lin, W, H, fmt, tm, swz, size)


def build_flim(orig, img):
    i = texdec.flim_info(orig)
    data = encode(img, i['format'], i['width'], i['height'], i['tileMode'], i['swizzle'], i['imageSize'])
    out = data + orig[i['imageSize']:]
    assert len(out) == len(orig)
    return out


def decode_flim(b):
    i = texdec.flim_info(b)
    return texdec.decode(i['data'], i['width'], i['height'], i['format'], i['tileMode'], i['swizzle'])


# ---------------------------------------------------------------- 만들기
def waza_channels(fill_png):
    f = np.asarray(Image.open(fill_png).convert('L')) > 127
    sd = ndimage.distance_transform_edt(f) - ndimage.distance_transform_edt(~f)
    sd = sd + np.where(f, -0.5, 0.5)                          # 경계를 픽셀 가장자리로
    inside = np.clip(sd + 0.5, 0, 1)
    far = np.clip(-(sd + 20) + 0.5, 0, 1)
    R = np.clip(np.maximum(inside, far) * 255, 0, 255)
    G = np.clip((sd + 13) / 4, 0, 1) * 255
    out = np.zeros(f.shape + (4,), np.uint8)
    out[..., 0] = R; out[..., 1] = G; out[..., 3] = 255
    return out


def fill_holes(rgba):
    """로고 안쪽에 갇힌 투명 구멍(GPT 결과에 생김, 원본엔 없음)을 둘레 색(흰 테두리판) 중앙값으로 메움."""
    a = rgba[..., 3] > 128
    holes = ndimage.binary_fill_holes(a) & ~a
    lab, k = ndimage.label(holes)
    out = rgba.copy()
    for i in range(1, k + 1):
        h = lab == i
        ring = ndimage.binary_dilation(h, iterations=3) & ~h & a
        col = np.percentile(rgba[ring][:, :3], 90, axis=0).astype(np.uint8)   # 둘레의 밝은 쪽(흰 판) 색
        grow = ndimage.binary_dilation(h, iterations=1) & (rgba[..., 3] < 255)
        # 구멍 둘레 3px 안의 무채색 회색 선(GPT 가 그린 구멍 테두리)도 판 색으로. 채도 있는 글자 색은 그대로
        rgb = rgba[..., :3].astype(int)
        gray = (rgb.max(-1) - rgb.min(-1) < 24) & (rgb.mean(-1) < col.mean() - 8)
        edge = ndimage.binary_dilation(h, iterations=3) & gray
        out[h | grow | edge, :3] = col; out[h | grow | edge, 3] = 255
        # 그래도 남은 점: 구멍 둘레 8px 안에서 판 색보다 어두운 작은 덩어리(15픽셀 미만)만 판 색으로
        near = ndimage.binary_dilation(h, iterations=8)
        dark = near & (out[..., :3].astype(int).mean(-1) < col.mean() - 6)
        dl, dk = ndimage.label(dark)
        if dk:
            sz = ndimage.sum(dark, dl, range(1, dk + 1))
            small = np.isin(dl, np.nonzero(sz < 15)[0] + 1)
            out[small, :3] = col
            print('   남은 점 %d개(%d픽셀) 지움' % (int((sz < 15).sum()), int(small.sum())))
        print('   구멍 메움 %d픽셀, 색 %s' % (h.sum(), tuple(col)))
    return out


def premul_resize(im, size):
    a = np.asarray(im.convert('RGBA')).astype(np.float32) / 255
    pm = a.copy(); pm[..., :3] *= pm[..., 3:4]
    r = np.stack([np.asarray(Image.fromarray((pm[..., k] * 255).astype(np.uint8)).resize(size, Image.LANCZOS)).astype(np.float32) / 255 for k in range(4)], -1)
    al = np.clip(r[..., 3:4], 1e-6, 1)
    rgb = np.where(r[..., 3:4] > 0, r[..., :3] / al, 0)
    return np.clip(np.concatenate([rgb, r[..., 3:4]], -1) * 255 + 0.5, 0, 255).astype(np.uint8)


def shadow(small_rgba, fit, W, H):
    al = Image.fromarray(small_rgba[..., 3]).resize((fit['w'], fit['h']), Image.BOX)
    can = Image.new('L', (W, H), 0); can.paste(al, (fit['dx'], fit['dy']))
    if fit['blur']:
        can = can.filter(ImageFilter.GaussianBlur(fit['blur']))
    g = np.asarray(can)
    return np.dstack([g, g, g, np.full_like(g, 255)])


def main():
    os.makedirs(OUT, exist_ok=True); os.makedirs(CMP, exist_ok=True)
    fit = json.load(open(os.path.join(ROOT, 'work', 'shadow_fit.json')))
    jobs = []           # (이름, 묶음 경로, 새 이미지)
    for k, d in enumerate(('01_매의눈', '02_호로쿠다마', '03_세갈래수리검')):
        jobs.append(('Nh_NzmWaza_%02d^t.bflim' % k, WAZA + 'Nh_NzmWaza_%02d^t.bflim' % k, waza_channels(os.path.join(GPT, d, '결과.png'))))
    for num, d, big_name, small_name, sh_name, fkey in (
            ('09', '04_타카마루의수리검도장', 'Te_AttractionLogoLJP_09^q.bflim', 'Te_AttractionLogoJP_09^l.bflim', 'Nt_AttractionLogoShJP_09^s.bflim', '6187'),
            ('05', '05_동물의숲사탕축제', 'Te_AttractionLogoLJP_05^q.bflim', 'Te_AttractionLogoJP_05^l.bflim', 'Nt_AttractionLogoShJP_05^s.bflim', '6190')):
        big = np.asarray(Image.open(os.path.join(GPT, d, '결과.png')).convert('RGBA')).copy()
        big[..., 3] = np.where(big[..., 3] >= 250, 255, big[..., 3])
        big = fill_holes(big)
        jobs.append((big_name, LOGO1 + big_name, big))
        so = texdec.flim_info(leaf(LOGO0 + small_name)[0])
        small = premul_resize(Image.fromarray(big), (so['width'], so['height']))
        jobs.append((small_name, LOGO0 + small_name, small))
        sho = texdec.flim_info(leaf(LOGO0 + sh_name)[0])
        sh = shadow(small, fit[fkey], sho['width'], sho['height'])
        jobs.append((sh_name, LOGO0 + sh_name, sh))
        jobs.append((sh_name, LOGO1 + sh_name, sh))      # 01 묶음에도 같은 그림자
    manifest = []
    for name, path, img in jobs:
        orig, top = leaf(path)
        new = build_flim(orig, img)
        back = decode_flim(new); want = img
        i = texdec.flim_info(orig)
        f6 = i['format'] & 0x3F
        ch = {0x35: [0, 1], 0x34: [0], 0x33: [0, 1, 2, 3], 0x1A: [0, 1, 2, 3]}[f6]
        if f6 in (0x33, 0x1A):
            m = want[..., 3] > 0
            err = np.abs(back[..., :4].astype(int) - want[..., :4].astype(int))[m].max(-1).mean()
        else:
            err = np.abs(back[..., ch].astype(int) - want[..., ch].astype(int)).mean()
        fn = os.path.join(OUT, path.replace('/', '_').replace('content_Common_Package_', ''))
        open(fn, 'wb').write(new)
        manifest.append(dict(name=name, path=path, file=os.path.relpath(fn, ROOT), fmt=hex(i['format']), size=[i['width'], i['height']], roundtrip_err=round(float(err), 2)))
        print('%-36s %-6s %4dx%-4d 왕복 평균 오차 %.2f' % (name, hex(i['format']), i['width'], i['height'], err))
    json.dump(manifest, open(os.path.join(OUT, 'manifest.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    sheet(jobs)


def look(name, rgba):
    """게임에서 보이는 모양 흉내: 기술 띠는 G=검은 테두리, R&G=흰 글자 / 나머지는 회색 바탕 합성"""
    if name.startswith('Nh_'):
        R, G = rgba[..., 0].astype(int), rgba[..., 1].astype(int)
        img = np.full(R.shape + (3,), 120, np.uint8)
        a = G / 255.0; img = (img * (1 - a[..., None])).astype(np.uint8)
        w = (np.minimum(R, G) / 255.0)[..., None]
        img = (img * (1 - w) + 255 * w).astype(np.uint8)
        return Image.fromarray(img)
    if name.startswith('Nt_'):
        return Image.fromarray(rgba[..., 0]).convert('RGB')
    im = Image.fromarray(rgba, 'RGBA'); bg = Image.new('RGBA', im.size, (90, 90, 90, 255)); bg.alpha_composite(im); return bg.convert('RGB')


def sheet(jobs):
    UI = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
    seen = set(); rows = []
    for name, path, img in jobs:
        if name in seen:
            continue
        seen.add(name)
        o = look(name, decode_flim(leaf(path)[0])); n = look(name, decode_flim(build_flim(leaf(path)[0], img)))
        sc = 1 if o.width >= 300 else (300 // o.width)
        o = o.resize((o.width * sc, o.height * sc), Image.NEAREST); n = n.resize(o.size, Image.NEAREST)
        can = Image.new('RGB', (o.width * 2 + 30, o.height + 26), (30, 30, 30)); dr = ImageDraw.Draw(can)
        can.paste(o, (0, 26)); can.paste(n, (o.width + 30, 26)); dr.text((4, 3), name + ' 원본', font=UI, fill=(255, 220, 90)); dr.text((o.width + 34, 3), '한글(게임 형식으로 넣고 다시 푼 것)', font=UI, fill=(255, 220, 90))
        rows.append(can)
    W = max(r.width for r in rows); out = Image.new('RGB', (W, sum(r.height + 8 for r in rows)), (0, 0, 0)); y = 0
    for r in rows:
        out.paste(r, (0, y)); y += r.height + 8
    out.save(os.path.join(CMP, '최종_원본_한글.png'))


if __name__ == '__main__':
    main()
