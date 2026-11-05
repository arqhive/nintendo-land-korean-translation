import sys, os, collections
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
base = sys.argv[1]
for rel in ['content/JpJapanese/Message/AllMessage.szs', 'content/JpJapanese/Layout/Font.szs']:
    raw = open(os.path.join(base, rel), 'rb').read()
    d = yaz0_decompress(raw)
    info, files = sarc_read(d)
    print('==', rel, len(raw), '->', len(d), info)
    c = collections.Counter(os.path.splitext(n)[1] for n, _, _ in files)
    print('  ext:', dict(c))
    for n, b, h in files[:400]:
        print('   %-60s %8d %s' % (n, len(b), b[:4]))
