import sys, struct, zlib, re
sys.stdout.reconfigure(encoding="utf-8")
d = open(sys.argv[1], 'rb').read()
shoff = struct.unpack('>I', d[0x20:0x24])[0]; shnum = struct.unpack('>H', d[0x30:0x32])[0]; shstr = struct.unpack('>H', d[0x32:0x34])[0]
secs = []
for i in range(shnum):
    o = shoff + i * 40
    name, typ, flags, addr, off, size = struct.unpack('>IIIIII', d[o:o+24])
    raw = d[off:off+size]
    if flags & 0x08000000 and size >= 4: raw = zlib.decompress(raw[4:])
    secs.append((name, typ, flags, addr, raw))
strtab = secs[shstr][4]
jp = re.compile('[\u3040-\u30ff\u4e00-\u9fff]{2,}')
for name, typ, flags, addr, raw in secs:
    nm = strtab[name:strtab.index(b'\0', name)].decode()
    hits8 = [m for m in jp.findall(raw.decode('utf-8', 'ignore'))]
    hits16 = jp.findall(raw[: len(raw)//2*2].decode('utf-16-be', 'ignore')) + jp.findall(raw[1: 1+(len(raw)-1)//2*2].decode('utf-16-be', 'ignore'))
    try: sj = jp.findall(raw.decode('shift_jis', 'ignore'))
    except Exception: sj = []
    if hits8 or hits16 or sj:
        print(nm, len(raw), 'utf8', len(hits8), hits8[:8], 'utf16', len(hits16), hits16[:8], 'sjis', len(sj), sj[:8])
