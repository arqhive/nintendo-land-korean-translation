"""레이아웃 이름을 주면 txt1 글 상자마다 (pane 이름, 폰트, 기본 글)을 보여 준다."""
import sys, os, struct, re
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
want = sys.argv[1]
def bflyt(name, d):
    p = struct.unpack('>H', d[6:8])[0]; nb = struct.unpack('>H', d[0x10:0x12])[0]; fl = []; rows = []
    for _ in range(nb):
        mg = d[p:p+4]; sz = struct.unpack('>I', d[p+4:p+8])[0]
        if mg == b'fnl1':
            n = struct.unpack('>H', d[p+8:p+10])[0]
            for i in range(n):
                o = struct.unpack('>I', d[p+12+i*4:p+16+i*4])[0]; s = p+12+o; fl.append(d[s:d.index(b'\0', s)].decode())
        elif mg == b'txt1':
            pname = d[p+0x0C:p+0x24].split(b'\0')[0].decode()
            sx, sy = struct.unpack('>ff', d[p+0x48:p+0x50])
            buf, strl, mat, fi = struct.unpack('>HHHH', d[p+0x54:p+0x5C])
            toff = struct.unpack('>I', d[p+0x64:p+0x68])[0]
            fw, fh = struct.unpack('>ff', d[p+0x80:p+0x88]) if False else (0, 0)
            txt = d[p+toff:p+toff+strl].decode('utf-16-be', 'replace').rstrip('\0') if toff else ''
            rows.append((pname, fi, txt, sx, sy))
        p += sz
    print('==', name)
    for pname, fi, txt, sx, sy in rows: print('   %-28s %-26s %6.0fx%-5.0f %r' % (pname, fl[fi] if fi < len(fl) else fi, sx, sy, txt[:40]))
def walk(name, data):
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        for n, b, _ in sarc_read(data)[1]: walk(name + '/' + str(n), b)
    elif name.endswith(want + '.bflyt'): bflyt(name, data); raise SystemExit
root = os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]', 'content')
for dp, dn, fn in os.walk(root):
    dn[:] = [x for x in dn if x != '.svn']
    for f in fn:
        if f.endswith(('.szs', '.pack')) and 'Message' not in dp and 'Font' not in f:
            walk(f, open(os.path.join(dp, f), 'rb').read())
