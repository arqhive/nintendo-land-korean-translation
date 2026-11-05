import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
want = sys.argv[1]
def walk(name, data):
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        for n, b, _ in sarc_read(data)[1]: walk(name + '/' + str(n), b)
    elif name.endswith(want + '.bflyt'):
        d = data; print('ver', hex(struct.unpack('>I', d[8:12])[0]))
        p = struct.unpack('>H', d[6:8])[0]; nb = struct.unpack('>H', d[0x10:0x12])[0]
        for _ in range(nb):
            mg = d[p:p+4]; sz = struct.unpack('>I', d[p+4:p+8])[0]
            if mg == b'txt1':
                print(d[p+0x0C:p+0x24].split(b'\0')[0], sz)
                for o in range(0x54, min(sz, 0xA8), 16): print('   %02x' % o, d[p+o:p+o+16].hex(' '))
            p += sz
        raise SystemExit
root = os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]', 'content')
for dp, dn, fn in os.walk(root):
    dn[:] = [x for x in dn if x != '.svn']
    for f in fn:
        if f.endswith(('.szs', '.pack')) and 'Message' not in dp and 'Font' not in f:
            walk(f, open(os.path.join(dp, f), 'rb').read())
