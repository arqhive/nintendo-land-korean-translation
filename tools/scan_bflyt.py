import sys, os, re, struct, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
root = os.path.join(sys.argv[1], 'content')
fonts = collections.Counter(); jp_tx = []; ntxt = 0; seen = set()
JP = re.compile('[぀-ヿ一-鿿]')
def bflyt(name, d):
    global ntxt
    e = '>'; p = struct.unpack(e+'H', d[6:8])[0]; nb = struct.unpack(e+'H', d[0x10:0x12])[0]
    fl = []
    for _ in range(nb):
        mg = d[p:p+4]; sz = struct.unpack(e+'I', d[p+4:p+8])[0]
        if mg == b'fnl1':
            n = struct.unpack(e+'H', d[p+8:p+10])[0]
            for i in range(n):
                o = struct.unpack(e+'I', d[p+12+i*4:p+16+i*4])[0]
                s = p+12+o; fl.append(d[s:d.index(b'\0', s)].decode())
        elif mg == b'txt1':
            ntxt += 1
            font_idx = struct.unpack(e+'H', d[p+0x4C+4:p+0x4C+6])[0] if False else None
            seg = d[p:p+sz]
            for m in re.finditer(rb'(?:(?:[\x30][\x40-\xff]|[\x4e-\x9f][\x00-\xff]|\xff[\x00-\xef])){2,}', seg):
                try: t = m.group().decode('utf-16-be')
                except: continue
                if JP.search(t): jp_tx.append((name, t))
        p += sz
    for f in fl: fonts[f] += 1
def walk(name, data):
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        for n, b, _ in sarc_read(data)[1]: walk(name + '/' + str(n), b)
    elif name.endswith('.bflyt'):
        k = os.path.basename(name)
        if k in seen: return
        seen.add(k); bflyt(name, data)
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d != '.svn']
    for f in fn:
        if f.endswith(('.szs','.pack','.sarc')) and 'Voice' not in dp and 'Message' not in dp and 'Font' not in f:
            walk(os.path.relpath(os.path.join(dp,f), root), open(os.path.join(dp,f),'rb').read())
print('bflyt', len(seen), 'txt1', ntxt); print('fonts', fonts.most_common())
print('jp in layout', len(jp_tx)); [print('  ', os.path.basename(a), repr(b[:40])) for a, b in jp_tx[:30]]
