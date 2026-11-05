import sys, os, hashlib
def tree(r):
    out = {}
    for dp, dn, fn in os.walk(r):
        dn[:] = [d for d in dn if d != '.svn']
        for f in fn:
            p = os.path.join(dp, f); out[os.path.relpath(p, r).replace(os.sep,'/')] = p
    return out
def h(p): return hashlib.md5(open(p,'rb').read()).hexdigest()
a, b = tree(sys.argv[1]), tree(sys.argv[2])
only_a = sorted(set(a)-set(b)); only_b = sorted(set(b)-set(a)); same=diff=0; dl=[]
for k in sorted(set(a)&set(b)):
    if os.path.getsize(a[k]) == os.path.getsize(b[k]) and h(a[k]) == h(b[k]): same += 1
    else: diff += 1; dl.append(k)
print('same', same, 'diff', diff, 'onlyA', len(only_a), 'onlyB', len(only_b))
print('DIFF:', *dl[:60], sep='\n  ')
print('ONLY A:', *only_a[:40], sep='\n  ')
print('ONLY B:', *only_b[:60], sep='\n  ')
