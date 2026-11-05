"""업데이트판 메시지·폰트 아카이브를 work/extract 에 푼다."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPD = os.path.join(ROOT, 'Nintendo Land [Update] [0005000e10101f00]', 'content', 'JpJapanese')
OUT = os.path.join(ROOT, 'work', 'extract')
def dump(sarc, dst):
    for n, b, _ in sarc_read(sarc)[1]:
        p = os.path.join(dst, n); os.makedirs(os.path.dirname(p), exist_ok=True); open(p, 'wb').write(b)
dump(yaz0_decompress(open(os.path.join(UPD, 'Layout', 'Font.szs'), 'rb').read()), os.path.join(OUT, 'Font'))
for n, b, _ in sarc_read(yaz0_decompress(open(os.path.join(UPD, 'Message', 'AllMessage.szs'), 'rb').read()))[1]:
    dump(b, os.path.join(OUT, 'Message', n[:-5]))
print('ok')
