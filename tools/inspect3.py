import sys, os, collections, re
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
base = sys.argv[1]
d = yaz0_decompress(open(os.path.join(base, 'content/JpJapanese/Message/AllMessage.szs'), 'rb').read())
_, outer = sarc_read(d)
tot = 0; chars = collections.Counter(); tags = collections.Counter(); secs = collections.Counter(); enc = collections.Counter(); nch = 0
per = []
for n, b, _ in outer:
    _, inner = sarc_read(b)
    cnt = 0; cc = 0
    for x, bb, _ in inner:
        m = msbt_read(bb); enc[(m['endian'], m['enc'])] += 1
        secs[tuple(s[0].decode() for s in m['sections'])] += 1
        for t in m['texts']:
            s = msbt_text_to_str(t, m['endian'])
            for tg in re.findall(r'\{/?(\d+:\d+)', s): tags[tg] += 1
            plain = re.sub(r'\{[^}]*\}', '', s)
            chars.update(plain); cc += len(plain.replace('\n',''))
            cnt += 1
    per.append((n, len(inner), cnt, cc)); tot += cnt; nch += cc
for p in per: print(p)
print('total msgs', tot, 'chars', nch, 'unique', len(chars))
print('enc', enc); print('secs', secs); print('tags', tags.most_common(40))
