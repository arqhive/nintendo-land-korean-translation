"""Nintendo Land 한글화 공용: Yaz0 압축 풀기/묶기, SARC 읽기/쓰기."""
import struct


def yaz0_decompress(data: bytes) -> bytes:
    assert data[:4] == b'Yaz0', data[:4]
    size = struct.unpack('>I', data[4:8])[0]
    out = bytearray(size)
    src, dst = 16, 0
    n_data = len(data)
    while dst < size:
        code = data[src]; src += 1
        if code == 0xFF and dst + 8 <= size and src + 8 <= n_data:      # 8바이트 그대로
            out[dst:dst + 8] = data[src:src + 8]; src += 8; dst += 8
            continue
        for bit in range(8):
            if dst >= size:
                break
            if code & (0x80 >> bit):
                out[dst] = data[src]; src += 1; dst += 1
            else:
                b1 = data[src]; b2 = data[src + 1]; src += 2
                dist = ((b1 & 0x0F) << 8 | b2) + 1
                n = b1 >> 4
                if n == 0:
                    n = data[src] + 0x12; src += 1
                else:
                    n += 2
                s0 = dst - dist
                if dist >= n:
                    out[dst:dst + n] = out[s0:s0 + n]
                elif dist == 1:
                    out[dst:dst + n] = bytes((out[s0],)) * n
                else:
                    pat = bytes(out[s0:dst])
                    rep = (pat * (n // dist + 1))[:n]
                    out[dst:dst + n] = rep
                dst += n
    return bytes(out)


def sarc_read(data: bytes):
    """반환: (헤더 정보 dict, [(이름, 바이트, 이름해시), ...])"""
    assert data[:4] == b'SARC'
    bom = data[6:8]
    e = '>' if bom == b'\xfe\xff' else '<'
    hdr_len, _, file_size, data_off, ver = struct.unpack(e + 'HHIIH', data[4:18])
    p = hdr_len
    assert data[p:p + 4] == b'SFAT'
    sfat_len, count, mult = struct.unpack(e + 'HHI', data[p + 4:p + 12])
    nodes = []
    q = p + sfat_len
    for i in range(count):
        h, attr, s, en = struct.unpack(e + 'IIII', data[q + i * 16:q + i * 16 + 16])
        nodes.append((h, attr, s, en))
    q += count * 16
    assert data[q:q + 4] == b'SFNT'
    sfnt_len = struct.unpack(e + 'H', data[q + 4:q + 6])[0]
    names_base = q + sfnt_len
    files = []
    for h, attr, s, en in nodes:
        if attr & 0x01000000:
            no = names_base + (attr & 0xFFFF) * 4
            name = data[no:data.index(b'\0', no)].decode('utf-8')
        else:
            name = None
        files.append((name, data[data_off + s:data_off + en], h))
    info = dict(endian=e, mult=mult, data_off=data_off, ver=ver, count=count)
    return info, files


def msbt_read(data: bytes):
    """반환: dict(endian, enc, sections=[(magic, bytes)], labels={idx:label}, texts=[raw utf16 bytes])"""
    assert data[:8] == b'MsgStdBn'
    e = '>' if data[8:10] == b'\xfe\xff' else '<'
    enc = data[0x0C]
    nsec = struct.unpack(e + 'H', data[0x0E:0x10])[0]
    p = 0x20
    secs = []
    for _ in range(nsec):
        magic = data[p:p + 4]
        size = struct.unpack(e + 'I', data[p + 4:p + 8])[0]
        secs.append((magic, data[p + 16:p + 16 + size]))
        p = (p + 16 + size + 15) & ~15
    out = dict(endian=e, enc=enc, sections=secs, labels={}, texts=[], raw_header=data[:0x20])
    for magic, s in secs:
        if magic == b'LBL1':
            n = struct.unpack(e + 'I', s[:4])[0]
            for i in range(n):
                cnt, off = struct.unpack(e + 'II', s[4 + i * 8:12 + i * 8])
                q = off
                for _ in range(cnt):
                    ln = s[q]; lab = s[q + 1:q + 1 + ln].decode('ascii'); idx = struct.unpack(e + 'I', s[q + 1 + ln:q + 5 + ln])[0]
                    out['labels'][idx] = lab; q += 5 + ln
        elif magic == b'TXT2':
            n = struct.unpack(e + 'I', s[:4])[0]
            offs = [struct.unpack(e + 'I', s[4 + i * 4:8 + i * 4])[0] for i in range(n)] + [len(s)]
            out['texts'] = [s[offs[i]:offs[i + 1]] for i in range(n)]
    return out


def msbt_text_to_str(raw: bytes, e='>'):
    """UTF-16 텍스트를 사람이 읽는 문자열로. 태그는 {grp:typ:hexparams}로, 끝 \0 제거."""
    out = []; i = 0; u = 'utf-16-be' if e == '>' else 'utf-16-le'
    while i + 1 < len(raw):
        c = struct.unpack(e + 'H', raw[i:i + 2])[0]
        if c == 0x0E:
            g, t, ln = struct.unpack(e + 'HHH', raw[i + 2:i + 8])
            out.append('{%d:%d:%s}' % (g, t, raw[i + 8:i + 8 + ln].hex())); i += 8 + ln
        elif c == 0x0F:
            g, t = struct.unpack(e + 'HH', raw[i + 2:i + 6]); out.append('{/%d:%d}' % (g, t)); i += 6
        elif c == 0:
            i += 2
            if i < len(raw): out.append('{NUL}')
        else:
            out.append(raw[i:i + 2].decode(u)); i += 2
    return ''.join(out)


def sarc_hash(name: str, mult=101):
    h = 0
    for c in name.encode('utf-8'):
        h = (h * mult + (c if c < 128 else c - 256)) & 0xFFFFFFFF
    return h


def sarc_write(files, mult=101, endian='>', data_off=None, align=None, ver=0x100):
    """files: [(이름, 바이트)] 원래 순서(해시 정렬 기준). align: 파일별 정렬 함수 또는 숫자."""
    e = endian
    ents = sorted(((sarc_hash(n, mult), n, b) for n, b in files), key=lambda x: x[0])
    sfnt = bytearray(); name_off = []
    for _, n, _ in ents:
        name_off.append(len(sfnt) // 4)
        sfnt += n.encode('utf-8') + b'\0'
        while len(sfnt) % 4: sfnt += b'\0'
    hdr_len = 0x14; sfat_len = 0x0C
    head = hdr_len + sfat_len + 16 * len(ents) + 8 + len(sfnt)
    if data_off is None: data_off = head
    assert data_off >= head
    body = bytearray(); nodes = []
    for (h, n, b), no in zip(ents, name_off):
        a = align(n, b) if callable(align) else (align or 4)
        while len(body) % a: body += b'\0'
        s = len(body); body += b; nodes.append((h, 0x01000000 | no, s, len(body)))
    out = bytearray()
    out += b'SARC' + struct.pack(e + 'HH', hdr_len, 0xFEFF) + struct.pack(e + 'IIH', data_off + len(body), data_off, ver) + b'\0\0'
    out += b'SFAT' + struct.pack(e + 'HHI', sfat_len, len(ents), mult)
    for nd in nodes: out += struct.pack(e + 'IIII', *nd)
    out += b'SFNT' + struct.pack(e + 'HH', 8, 0) + sfnt
    out += b'\0' * (data_off - len(out))
    out += body
    return bytes(out)


def sarc_layout(data: bytes):
    """원본 SARC의 파일별 정렬값 추정용: [(이름, 시작오프셋)]"""
    info, files = sarc_read(data)
    e = info['endian']; p = 0x14 + 0x0C
    res = []
    for i, (n, b, h) in enumerate(files):
        s = struct.unpack(e + 'I', data[p + i * 16 + 8:p + i * 16 + 12])[0]
        res.append((n, s))
    return res


def msbt_write(m, texts=None):
    """msbt_read 결과로 다시 쓰기. texts를 주면 TXT2를 그 원시 바이트 목록으로 교체."""
    e = m['endian']
    secs = []
    for magic, s in m['sections']:
        if magic == b'TXT2' and texts is not None:
            n = len(texts); off = 4 + 4 * n; tbl = b''; body = b''
            for t in texts:
                tbl += struct.pack(e + 'I', off + len(body)); body += t
            s = struct.pack(e + 'I', n) + tbl + body
        secs.append((magic, s))
    out = bytearray()
    for magic, s in secs:
        out += magic + struct.pack(e + 'I', len(s)) + b'\0' * 8 + s
        while len(out) % 16: out += b'\xab'
    hdr = bytearray(m['raw_header'])
    struct.pack_into(e + 'I', hdr, 0x12, 0x20 + len(out))
    return bytes(hdr) + bytes(out)


def yaz0_compress(data: bytes, chain=24) -> bytes:
    """탐욕 LZ77(3바이트 해시 체인). 출력은 표준 Yaz0(정렬 0)."""
    n = len(data)
    out = bytearray(b'Yaz0' + struct.pack('>I', n) + b'\0' * 8)
    heads = {}
    src = 0
    mv = memoryview(data)
    while src < n:
        code_pos = len(out); out.append(0); code = 0
        for bit in range(8):
            if src >= n:
                break
            best_len = 0; best_dist = 0
            if src + 3 <= n:
                key = bytes(mv[src:src + 3])
                cand = heads.get(key)
                if cand:
                    maxl = min(0x111, n - src)
                    for p in reversed(cand[-chain:]):
                        d = src - p
                        if d > 0x1000:
                            break
                        l = 3
                        while l < maxl and data[p + l] == data[src + l]:
                            l += 1
                        if l > best_len:
                            best_len, best_dist = l, d
                            if l == maxl:
                                break
            if best_len >= 3:
                d = best_dist - 1
                if best_len >= 0x12:
                    out += bytes([d >> 8, d & 0xFF, best_len - 0x12])
                else:
                    out += bytes([((best_len - 2) << 4) | (d >> 8), d & 0xFF])
                for k in range(best_len):
                    q = src + k
                    if q + 3 <= n:
                        heads.setdefault(bytes(mv[q:q + 3]), []).append(q)
                src += best_len
            else:
                code |= 0x80 >> bit
                out.append(data[src])
                if src + 3 <= n:
                    heads.setdefault(bytes(mv[src:src + 3]), []).append(src)
                src += 1
            # 체인이 너무 길어지면 앞부분 정리
        out[code_pos] = code
    return bytes(out)


def str_to_msbt(s: str, e='>'):
    """msbt_text_to_str 의 역. 끝에 \0 을 붙인다."""
    import re as _re
    u = 'utf-16-be' if e == '>' else 'utf-16-le'
    out = bytearray(); i = 0
    while i < len(s):
        if s[i] == '{':
            j = s.index('}', i); tag = s[i + 1:j]
            if tag == 'NUL':
                out += b'\0\0'
            elif tag.startswith('/'):
                g, t = map(int, tag[1:].split(':'))
                out += struct.pack(e + 'HHH', 0x0F, g, t)
            else:
                g, t, h = tag.split(':'); prm = bytes.fromhex(h)
                out += struct.pack(e + 'HHHH', 0x0E, int(g), int(t), len(prm)) + prm
            i = j + 1
        else:
            out += s[i].encode(u); i += 1
    out += b'\0\0'
    return bytes(out)


def sarc_patch_same_size(data: bytes, rep: dict) -> bytes:
    """SARC 안 파일을 같은 길이 바이트로 제자리 덮어쓰기(배치·정렬·헤더 그대로). rep = {이름: 바이트}"""
    info, files = sarc_read(data)
    e = info['endian']; out = bytearray(data); p = 0x14 + 0x0C
    names = [n for n, _, _ in files]
    for k, v in rep.items():
        i = names.index(k)
        s, en = struct.unpack(e + 'II', data[p + i * 16 + 8:p + i * 16 + 16])
        assert en - s == len(v), (k, en - s, len(v))
        out[info['data_off'] + s:info['data_off'] + en] = v
    return bytes(out)
