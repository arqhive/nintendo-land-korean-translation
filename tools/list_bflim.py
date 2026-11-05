import sys, os, re, collections
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
root = os.path.join(sys.argv[1], 'content'); names = []
def walk(name, data):
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        for n, b, _ in sarc_read(data)[1]: walk(name + '/' + str(n), b)
    elif name.lower().endswith('.bflim'): names.append(name)
for dp, dn, fn in os.walk(root):
    dn[:] = [d for d in dn if d != '.svn']
    for f in fn:
        if f.endswith(('.szs','.pack','.sarc')) and 'Voice' not in dp and 'Message' not in dp and 'Font' not in f:
            walk(os.path.relpath(os.path.join(dp,f), root), open(os.path.join(dp,f),'rb').read())
open(sys.argv[2],'w',encoding='utf-8').write('\n'.join(names))
base = collections.Counter(os.path.basename(n) for n in names)
print(len(names), 'unique', len(base))
suf = collections.Counter(m.group(1) for n in base for m in [re.search(r'_([A-Za-z]{2,5})(?:_\d+)?\^', n)] if m)
print(suf.most_common(60))
