import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from nlib import *
base = sys.argv[1]
d = yaz0_decompress(open(os.path.join(base, 'content/JpJapanese/Layout/Font.szs'), 'rb').read())
_, files = sarc_read(d)
FMT = {0:'RGBA8',1:'RGB8',2:'RGBA5551',3:'RGB565',4:'RGBA4',5:'LA8',6:'LA4',7:'A8',8:'L4',9:'A4',10:'ETC1',11:'ETC1A4',12:'BC1',13:'BC2',14:'BC3',15:'BC4L',16:'BC4A',17:'BC5'}
for n, b, _ in files:
    e = '>' if b[4:6] == b'\xfe\xff' else '<'
    hl, ver, fsize, nblk = struct.unpack(e+'HIIH', b[6:18]) if False else (struct.unpack(e+'H', b[6:8])[0], struct.unpack(e+'I', b[8:12])[0], struct.unpack(e+'I', b[12:16])[0], struct.unpack(e+'H', b[16:18])[0])
    p = hl; allc=set(); codes = 0; ranges = []; info = {}
    while p < len(b) - 8:
        mg = b[p:p+4]; sz = struct.unpack(e+'I', b[p+4:p+8])[0]
        if mg == b'FINF':
            ft, h, w, asc = struct.unpack(e+'BBBB', b[p+8:p+12])
            lf, alt = struct.unpack(e+'HH', b[p+12:p+16])
            info['finf'] = dict(type=ft, height=h, width=w, ascent=asc, linefeed=lf)
        elif mg == b'TGLP':
            cw, ch, nsh, maxw = struct.unpack(e+'BBBB', b[p+8:p+12])
            shsz, base_, fmt, cols, rows, sw, sh = struct.unpack(e+'IHHHHHH', b[p+12:p+28])
            info['tglp'] = dict(cell=(cw, ch), sheets=nsh, sheet=(sw, sh), fmt=fmt, grid=(cols, rows), per_sheet=cols*rows, cap=cols*rows*nsh, sheet_bytes=shsz)
        elif mg == b'CMAP':
            cb, ce, meth = struct.unpack(e+'HHH', b[p+8:p+14])
            q = p+20
            if meth == 0: c = ce-cb+1
            elif meth == 1: c = sum(1 for i in range(ce-cb+1) if struct.unpack(e+'H', b[q+i*2:q+2+i*2])[0] != 0xFFFF)
            else:
                c = struct.unpack(e+'H', b[q:q+2])[0]
                allc.update(struct.unpack(e+'H', b[q+2+i*4:q+4+i*4])[0] for i in range(c))
            if meth != 2: allc.update(range(cb, ce+1))
            codes += c; ranges.append((hex(cb), hex(ce), meth, c))
        p += sz
        if sz == 0: break
    hg = sum(1 for c in allc if 0xAC00<=c<=0xD7A3); kj = sum(1 for c in allc if 0x4E00<=c<=0x9FFF); kana=sum(1 for c in allc if 0x3040<=c<=0x30FF)
    print('==', n, len(b), 'ver', hex(ver), info, 'codes', codes, 'hangul', hg, 'kanji', kj, 'kana', kana)
    print('   cmap', ranges[:6], '...' if len(ranges)>12 else '', len(ranges))
