import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
base = sys.argv[1]
d = yaz0_decompress(open(os.path.join(base, 'content/JpJapanese/Message/AllMessage.szs'), 'rb').read())
ok = bad = 0
for n, b, _ in sarc_read(d)[1]:
    for x, bb, _ in sarc_read(b)[1]:
        m = msbt_read(bb)
        if msbt_write(m, m['texts']) == bb: ok += 1
        else: bad += 1; print('DIFF', x)
print('msbt same', ok, 'diff', bad)
