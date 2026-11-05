import sys, os, collections, struct
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
base = sys.argv[1]
d = yaz0_decompress(open(os.path.join(base, 'content/JpJapanese/Message/AllMessage.szs'), 'rb').read())
_, outer = sarc_read(d)
for n, b, _ in outer:
    _, inner = sarc_read(b)
    c = collections.Counter(os.path.splitext(x)[1] for x, _, _ in inner)
    print('==', n, len(inner), dict(c))
    for x, bb, _ in inner[:12]:
        print('   %-50s %7d %s' % (x, len(bb), bb[:8]))
