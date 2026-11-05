import sys, os, collections, re
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
base = sys.argv[1]; root = os.path.join(base, 'content')
ext = collections.Counter(); lang = collections.Counter(); bflim = 0; samples = []
def walk(name, data, depth=0):
    global bflim
    if data[:4] == b'Yaz0': data = yaz0_decompress(data)
    if data[:4] == b'SARC':
        try: _, fs = sarc_read(data)
        except Exception as ex: print('ERR', name, ex); return
        for n, b, _ in fs: walk(name + '/' + str(n), b, depth+1)
    else:
        e = os.path.splitext(name)[1].lower(); ext[e] += 1
        if e == '.bflim':
            bflim += 1
            m = re.search(r'(?i)(_jp|_jpn|jpja|japan|_ja\b|_en\b|_us|_eu|usen|euen)', name)
            if m: lang[m.group(1).lower()] += 1; samples.append(name)
for dp, dn, fn in os.walk(root):
    if '.svn' in dp: continue
    for f in fn:
        if f.endswith(('.szs', '.pack', '.sarc')) and 'Voice' not in dp and 'Message' not in dp and 'Font' not in f:
            walk(os.path.relpath(os.path.join(dp, f), root), open(os.path.join(dp, f), 'rb').read())
print(ext.most_common(40)); print('bflim', bflim, 'lang-named', lang); print('\n'.join(samples[:40]))
