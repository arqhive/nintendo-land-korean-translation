import sys, os, hashlib
root = sys.argv[1]; out = []
for dp, dn, fn in os.walk(root):
    dn.sort(); dn[:] = [d for d in dn if d != '.svn']
    for f in sorted(fn):
        p = os.path.join(dp, f); h = hashlib.md5()
        with open(p, 'rb') as fh:
            for ch in iter(lambda: fh.read(1 << 22), b''): h.update(ch)
        out.append('%s  %12d  %s' % (h.hexdigest(), os.path.getsize(p), os.path.relpath(p, root).replace(os.sep, '/')))
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out) + '\n'); print(sys.argv[2], len(out))
