"""BFLIM·BFRES(FTEX) 텍스처 → RGBA (눈으로 확인용). 밉맵 0만.

BFLIM(Wii U): 이미지 데이터 + 끝 0x28바이트 = FLIM 헤더(0x14) + imag 블록
  imag: u16 w, u16 h, u16 align, u8 format, u8 swz(tileMode = &0x1F, swizzle = ((>>5)&7)<<8), u32 imageSize
FTEX(BFRES v3): 'FTEX' + GX2Surface(16 u32 + mipOffset 13) ... +0xB0 데이터 오프셋(자기 기준 상대)
"""
import struct
import numpy as np
import addrlib, gtx2, gtx_lib

FLIM_FMT = {0: 0x01, 1: 0x01, 2: 0x02, 3: 0x07, 4: 0x07, 5: 0x08, 7: 0x0A, 8: 0x0B, 9: 0x1A,
            12: 0x31, 13: 0x32, 14: 0x33, 15: 0x34, 16: 0x34, 17: 0x35, 20: 0x41A, 21: 0x431,
            22: 0x432, 23: 0x433, 24: 0x19}


def flim_info(d):
    f = d[-0x28:]
    assert f[:4] == b'FLIM', f[:4]
    w, h, align, fmt, swz = struct.unpack('>HHHBB', f[0x1C:0x24])
    size = struct.unpack('>I', f[0x24:0x28])[0]
    return dict(width=w, height=h, flim_format=fmt, format=FLIM_FMT.get(fmt), tileMode=swz & 0x1F,
                swizzle=((swz >> 5) & 7) << 8, imageSize=size, data=d[:size])


def ftex_list(d):
    """bfres 안의 FTEX 들: [(offset, surface dict, data bytes, name)]"""
    out = []
    p = 0
    while True:
        p = d.find(b'FTEX', p)
        if p < 0:
            break
        try:
            v = struct.unpack('>16I', d[p + 4:p + 4 + 64])
            s = dict(zip(gtx_lib.GTX_FIELDS, v))
            if not (1 <= s['width'] <= 8192 and 1 <= s['height'] <= 8192 and s['imageSize'] > 0 and s['tileMode'] < 16):
                p += 4; continue
            noff = struct.unpack('>i', d[p + 0xA8:p + 0xAC])[0]
            doff = struct.unpack('>i', d[p + 0xB0:p + 0xB4])[0]
            name_p = p + 0xA8 + noff
            name = d[name_p:d.index(b'\0', name_p)].decode('ascii', 'replace') if 0 < name_p < len(d) else '?'
            dp = p + 0xB0 + doff
            out.append((p, s, d[dp:dp + s['imageSize']], name))
        except Exception:
            pass
        p += 4
    return out


def _pitch(fmt, w, h, tm):
    info = addrlib.getSurfaceInfo(fmt, w, h, 1, 1, tm, 0, 0)
    return info.pitch, info.height


def decode(raw, W, H, fmt, tm, swz):
    fmt6 = fmt & 0x3F
    bpp = addrlib.surfaceGetBitsPerPixel(fmt)
    bcn = fmt6 in gtx2.BCN
    pitch, ph = _pitch(fmt, W, H, tm)
    w, h = ((W + 3) // 4, (H + 3) // 4) if bcn else (W, H)
    if tm == 4:
        m = gtx2.addr_map(w, h, bpp, pitch, ph, swz)
        bpe = bpp // 8
        need = int(m.max()) + bpe
        buf = np.frombuffer(raw, np.uint8)
        if len(buf) < need:
            buf = np.concatenate([buf, np.zeros(need - len(buf), np.uint8)])
        lin = buf[m[..., None] + np.arange(bpe)]
    else:
        out = addrlib.deswizzle(W, H, H, fmt, tm, swz, pitch, bpp, raw)
        bpe = bpp // 8
        lin = np.frombuffer(out, np.uint8)[:w * h * bpe].reshape(h, w, bpe)
    return _to_rgba(lin, fmt6, W, H)


def _to_rgba(lin, fmt6, W, H):
    full = lambda a: np.full(a.shape[:2], 255, np.uint8)
    if fmt6 == 0x1A:
        return lin[:H, :W, :4].copy()
    if fmt6 == 0x01:
        g = lin[:H, :W, 0]; return np.dstack([g, g, g, full(g)])
    if fmt6 == 0x02:                    # LA4: 상위 4비트 알파? 하위 L
        v = lin[:H, :W, 0]; l = (v & 0xF) * 17; a = (v >> 4) * 17; return np.dstack([l, l, l, a])
    if fmt6 == 0x07:
        l = lin[:H, :W, 0]; a = lin[:H, :W, 1]; return np.dstack([l, l, l, a])
    if fmt6 == 0x08:
        v = lin[:H, :W, 0].astype(np.uint16) | (lin[:H, :W, 1].astype(np.uint16) << 8)
        r = ((v >> 11) & 31) * 255 // 31; g = ((v >> 5) & 63) * 255 // 63; b = (v & 31) * 255 // 31
        return np.dstack([r, g, b, full(r)]).astype(np.uint8)
    if fmt6 in (0x0A, 0x0B):
        v = lin[:H, :W, 0].astype(np.uint16) | (lin[:H, :W, 1].astype(np.uint16) << 8)
        if fmt6 == 0x0A:
            r = (v & 31) * 255 // 31; g = ((v >> 5) & 31) * 255 // 31; b = ((v >> 10) & 31) * 255 // 31; a = (v >> 15) * 255
        else:
            r = (v & 15) * 17; g = ((v >> 4) & 15) * 17; b = ((v >> 8) & 15) * 17; a = (v >> 12) * 17
        return np.dstack([r, g, b, a]).astype(np.uint8)
    if fmt6 == 0x19:
        v = lin[:H, :W, :4].astype(np.uint32)
        v = v[..., 0] | (v[..., 1] << 8) | (v[..., 2] << 16) | (v[..., 3] << 24)
        r = (v & 1023) >> 2; g = ((v >> 10) & 1023) >> 2; b = ((v >> 20) & 1023) >> 2
        return np.dstack([r, g, b, np.full(r.shape, 255)]).astype(np.uint8)
    if fmt6 == 0x31:
        rgb = gtx_lib.bc1_decode_blocks(np.ascontiguousarray(lin))[:H, :W]; return np.dstack([rgb, full(rgb)])
    if fmt6 == 0x32:
        return gtx2._bc2_decode(lin)[:H, :W]
    if fmt6 == 0x33:
        a = gtx_lib.bc4_decode_blocks(np.ascontiguousarray(lin[:, :, 0:8]))
        rgb = gtx_lib.bc1_decode_blocks(np.ascontiguousarray(lin[:, :, 8:16]))
        return np.dstack([rgb, a])[:H, :W]
    if fmt6 == 0x34:
        g = gtx_lib.bc4_decode_blocks(np.ascontiguousarray(lin))[:H, :W]; return np.dstack([g, g, g, full(g)])
    if fmt6 == 0x35:
        r = gtx_lib.bc4_decode_blocks(np.ascontiguousarray(lin[:, :, 0:8]))[:H, :W]
        g = gtx_lib.bc4_decode_blocks(np.ascontiguousarray(lin[:, :, 8:16]))[:H, :W]
        return np.dstack([r, g, np.zeros_like(r), full(r)])
    raise NotImplementedError('format 0x%x' % fmt6)
