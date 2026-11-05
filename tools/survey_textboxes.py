"""모든 bflyt 의 글 상자(txt1)를 work/survey/textboxes.json 으로.
FLYT v2.2(0x02020000) txt1: +0x44 scale(2f) +0x4C size(2f) +0x54 bufBytes +0x56 strBytes +0x58 mat +0x5A font
 +0x5C textPos(u8) +0x5D align(u8) +0x5E flags(u16) +0x60 italic +0x64 textOff +0x70 fontSize(2f) +0x78 charSpace +0x7C lineSpace +0x80 textIDOff
"""
import sys, os, struct, json
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []; seen = set(); parts = {}
def cstr(d, o):
    return d[o:d.index(b'\0', o)].decode('ascii', 'replace')
def bflyt(path, lay, d):
    p = struct.unpack('>H', d[6:8])[0]; nb = struct.unpack('>H', d[0x10:0x12])[0]; fl = []; stack = []; last = None
    for _ in range(nb):
        mg = d[p:p+4]; sz = struct.unpack('>I', d[p+4:p+8])[0]
        if mg == b'fnl1':
            n = struct.unpack('>H', d[p+8:p+10])[0]
            fl = [cstr(d, p+12+struct.unpack('>I', d[p+12+i*4:p+16+i*4])[0]) for i in range(n)]
        elif mg in (b'pan1', b'pic1', b'txt1', b'wnd1', b'bnd1', b'prt1'):
            last = d[p+0x0C:p+0x24].split(b'\0')[0].decode()
            if mg == b'txt1':
                f = lambda o, t='>f': struct.unpack(t, d[p+o:p+o+struct.calcsize(t)])[0]
                toff, strb, idoff = f(0x64, '>I'), f(0x56, '>H'), f(0x80, '>I')
                txt = d[p+toff:p+toff+strb].decode('utf-16-be', 'replace').rstrip('\0') if toff else ''
                rows.append(dict(arc=path, layout=lay, pane=last, parents=list(stack),
                    scale=[round(f(0x44), 3), round(f(0x48), 3)], size=[round(f(0x4C), 2), round(f(0x50), 2)],
                    font=fl[f(0x5A, '>H')], fsize=[round(f(0x70), 2), round(f(0x74), 2)],
                    cspace=round(f(0x78), 2), lspace=round(f(0x7C), 2), pos=d[p+0x5C], align=d[p+0x5D],
                    flags=f(0x5E, '>H'), bufbytes=f(0x54, '>H'), textid=cstr(d, p+idoff) if idoff else '', text=txt))
        if mg == b'prt1':
            blk = d[p:p+sz]
            parts.setdefault(lay, []).append(dict(pane=last, raw=blk.hex()))
        elif mg == b'pas1':
            stack.append(last)
        elif mg == b'pae1':
            stack.pop()
        p += sz
def walk(name, data):
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        for n, b, _ in sarc_read(data)[1]: walk(name + '/' + str(n), b)
    elif name.endswith('.bflyt'):
        lay = os.path.basename(name)[:-6]
        if lay in seen: return
        seen.add(lay); bflyt(name, lay, data)
root = os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]', 'content')
for dp, dn, fn in os.walk(root):
    dn[:] = [x for x in dn if x != '.svn']
    for f in sorted(fn):
        if f.endswith(('.szs', '.pack')) and 'Message' not in dp and 'Font' not in f:
            walk(os.path.relpath(os.path.join(dp, f), root).replace(os.sep, '/'), open(os.path.join(dp, f), 'rb').read())
import re as _re
names = sorted(seen, key=len, reverse=True); prt = {}
for lay, lst in parts.items():
    for e in lst:
        b = bytes.fromhex(e['raw']); hit = [n for n in names if n.encode() in b]
        prt.setdefault(lay, []).append(dict(pane=e['pane'], layout=hit[0] if hit else None))
json.dump(rows, open(os.path.join(ROOT, 'work', 'survey', 'textboxes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(prt, open(os.path.join(ROOT, 'work', 'survey', 'layout_parts.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('parts refs', sum(len(v) for v in prt.values()), 'resolved', sum(1 for v in prt.values() for e in v if e['layout']))
import collections
print('layouts', len(seen), 'textboxes', len(rows), 'with textid', sum(1 for r in rows if r['textid']))
print(collections.Counter(r['font'] for r in rows).most_common())
print(collections.Counter((r['pos'], r['align'], r['flags']) for r in rows).most_common(12))
for r in rows[:5]: print(r)
