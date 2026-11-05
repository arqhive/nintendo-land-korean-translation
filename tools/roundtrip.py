import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
def best_align(n, s):
    for a in (0x2000, 0x1000, 0x800, 0x400, 0x200, 0x100, 0x80, 0x40, 0x20, 0x10, 8, 4):
        if s % a == 0: return a
def rt(data, label):
    info, files = sarc_read(data)
    lay = dict(sarc_layout(data))
    # 정렬 추정: 실제 오프셋이 허용하는 최대 정렬은 과대추정이므로, 확장자별 최소값을 쓴다
    ext_al = {}
    for n, s in lay.items():
        ex = os.path.splitext(n)[1]; ext_al[ex] = min(ext_al.get(ex, 0x2000), best_align(n, s))
    new = sarc_write([(n, b) for n, b, _ in files], info['mult'], info['endian'], info['data_off'], lambda n, b: ext_al[os.path.splitext(n)[1]], info['ver'])
    ok = new == data
    print('%-40s files=%3d  same=%s  len %d/%d align=%s' % (label, len(files), ok, len(new), len(data), ext_al))
    return files
base = sys.argv[1]
d = yaz0_decompress(open(os.path.join(base, 'content/JpJapanese/Message/AllMessage.szs'), 'rb').read())
outer = rt(d, 'AllMessage(outer)')
for n, b, _ in outer: rt(b, n)
f = yaz0_decompress(open(os.path.join(base, 'content/JpJapanese/Layout/Font.szs'), 'rb').read())
rt(f, 'Font')
