"""4단계 그림 전수: 일본판 본편·업데이트 안의 모든 BFLIM 과 BFRES(FTEX) 를 풀어
같은 그림(MD5)은 한 번만, work/survey/tex/img/<번호>.png 로 저장하고 목록 work/survey/tex/index.jsonl 을 만든다.
업데이트에 같은 경로가 있으면 업데이트 쪽이 실제로 쓰이므로 둘 다 기록(src 칸).
"""
import os, sys, json, hashlib, time
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import yaz0_decompress, sarc_read
import texdec
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = [('game', os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]')),
       ('update', os.path.join(ROOT, 'Nintendo Land [Update] [0005000e10101f00]'))]
OUT = os.path.join(ROOT, 'work', 'survey', 'tex')
IMG = os.path.join(OUT, 'img')
os.makedirs(IMG, exist_ok=True)
seen = {}
idx = open(os.path.join(OUT, 'index.jsonl'), 'w', encoding='utf-8')


def save(src, path, name, raw, W, H, fmt, tm, swz, kind):
    h = hashlib.md5(raw).hexdigest()
    r = dict(src=src, path=path, name=name, kind=kind, w=W, h=H, fmt=fmt, tm=tm, md5=h)
    if h in seen:
        r['dup_of'] = seen[h]
    else:
        n = len(seen); seen[h] = n; r['id'] = n
        try:
            img = texdec.decode(raw, W, H, fmt, tm, swz)
            Image.fromarray(img, 'RGBA').save(os.path.join(IMG, '%05d.png' % n))
        except Exception as ex:
            r['err'] = str(ex)
    idx.write(json.dumps(r, ensure_ascii=False) + '\n')


def walk(src, path, data):
    if data[:4] == b'Yaz0':
        data = yaz0_decompress(data)
    if data[:2] == bytes((0x78, 0x9c)):
        import zlib
        try:
            data = zlib.decompress(data)
        except Exception:
            pass
    if data[:4] == b'SARC':
        for n, b, hh in sarc_read(data)[1]:
            walk(src, path + '//' + (n or '#%08x' % hh), b)
        return
    low = path.lower()
    if low.endswith('.bflim') and data[-0x28:-0x24] == b'FLIM':
        i = texdec.flim_info(data)
        if i['format'] is None:
            idx.write(json.dumps(dict(src=src, path=path, kind='bflim', err='flim fmt %d' % i['flim_format'])) + '\n'); return
        save(src, path, os.path.basename(path), i['data'], i['width'], i['height'], i['format'], i['tileMode'], i['swizzle'], 'bflim')
    elif data[:4] == b'FRES':
        for off, s, raw, name in texdec.ftex_list(data):
            save(src, path, name, raw, s['width'], s['height'], s['format'], s['tileMode'], s['swizzle'], 'ftex')
    elif b'Gfx2' == data[:4]:
        idx.write(json.dumps(dict(src=src, path=path, kind='gtx', note='GTX 따로 확인')) + '\n')


t0 = time.time(); n = 0
for src, base in SRC:
    for dp, dn, fn in os.walk(base):
        dn.sort()
        for f in sorted(fn):
            if not f.lower().endswith(('.szs', '.pack', '.sarc', '.bflim', '.bfres', '.arc', '.bfma')):
                continue
            p = os.path.join(dp, f)
            walk(src, os.path.relpath(p, base).replace(os.sep, '/'), open(p, 'rb').read())
            n += 1
            if n % 20 == 0:
                print('%d 묶음, 고유 그림 %d, %.0f초' % (n, len(seen), time.time() - t0), flush=True)
idx.close()
print('끝: 묶음 %d, 고유 그림 %d, %.0f초' % (n, len(seen), time.time() - t0))
