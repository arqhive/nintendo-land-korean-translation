import sys, os, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
def flat(name, data, out):
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        for n, b, _ in sarc_read(data)[1]: flat(name + '/' + str(n), b, out)
    else: out[name] = hashlib.md5(data).hexdigest()
for rel in sys.argv[3:]:
    A, B = {}, {}
    flat('', open(os.path.join(sys.argv[1], rel), 'rb').read(), A)
    flat('', open(os.path.join(sys.argv[2], rel), 'rb').read(), B)
    print('==', rel, len(A), len(B))
    for k in sorted(set(A) | set(B)):
        if A.get(k) != B.get(k): print('  ', 'A' if k in A else '-', 'B' if k in B else '-', k)
