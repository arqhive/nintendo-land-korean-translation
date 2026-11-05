"""4단계 전수 조사 1패스: 일본판 본편·업데이트의 모든 파일(code·content·meta)을 묶음(Yaz0·SARC) 안쪽까지 펼쳐
잎 파일마다 (경로, 크기, 매직, 확장자, 일본어 문자열 검사 결과)를 work/survey/all_files.jsonl 에 쓴다.

일본어 검사: UTF-16BE, UTF-16LE, UTF-8, Shift-JIS 네 가지로 풀어
  가나가 하나 이상 섞인 2자 이상 일본어 덩어리 (가나·한자·일본어 부호)
를 센다. 한자만인 덩어리는 이진 잡음이 많아 4자 이상만 센다.
"""
import os, sys, json, re, struct, hashlib, time
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import yaz0_decompress, sarc_read

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = [('game', os.path.join(ROOT, 'Nintendo Land [Game] [0005000010101f00]')),
       ('update', os.path.join(ROOT, 'Nintendo Land [Update] [0005000e10101f00]'))]
OUT = os.path.join(ROOT, 'work', 'survey', 'all_files.jsonl')

JP = re.compile('[぀-ヿ一-鿿　-〿！-～]{2,}')
KANA = re.compile('[぀-ヿ]')
KANJI4 = re.compile('[一-鿿]{4,}')


def good(m, enc):
    """잡음 거르기: 가나 2자 이상·3자 이상. UTF-16 은 두 바이트가 모두 영문 범위인 글자(영어 두 글자가
    한자처럼 읽힌 것)가 30%를 넘으면 버린다. 가나가 한 종류 글자만 반복되면(무늬 데이터) 버린다."""
    kana = [c for c in m if '぀' <= c <= 'ヿ']
    if len(m) < 3 or len(kana) < 2 or len(set(kana)) < 2:
        return False
    if enc.startswith('utf16'):
        asc = sum(1 for c in m if 0x20 <= (ord(c) >> 8) <= 0x7E and 0x20 <= (ord(c) & 0xFF) <= 0x7E)
        if asc / len(m) > 0.3:
            return False
    return True


def jp_hits(b):
    res = {}
    for enc, data in (('utf16be', b[:len(b) // 2 * 2]), ('utf16le', b[:len(b) // 2 * 2]), ('utf8', b), ('sjis', b)):
        codec = {'utf16be': 'utf-16-be', 'utf16le': 'utf-16-le', 'utf8': 'utf-8', 'sjis': 'shift_jis'}[enc]
        s = data.decode(codec, 'ignore') if enc.startswith('utf16') else data.decode(codec, 'replace')
        if enc == 'utf16be' and len(b) > 1:
            s += '\n' + b[1:1 + (len(b) - 1) // 2 * 2].decode('utf-16-be', 'ignore')
        if enc == 'utf16le' and len(b) > 1:
            s += '\n' + b[1:1 + (len(b) - 1) // 2 * 2].decode('utf-16-le', 'ignore')
        found = [m for m in JP.findall(s) if good(m, enc)]
        if found:
            res[enc] = dict(n=len(found), sample=found[:12])
    return res


def leaf(fh, top, path, data, depth=0):
    magic = data[:4]
    if magic == b'Yaz0':
        try:
            return leaf(fh, top, path, yaz0_decompress(data), depth)
        except Exception as ex:
            rec(fh, top, path, data, 'Yaz0-ERR:' + str(ex)); return
    if data[:2] == bytes((0x78, 0x9c)):
        import zlib
        try:
            return leaf(fh, top, path, zlib.decompress(data), depth)
        except Exception:
            pass
    if magic == b'SARC':
        try:
            files = sarc_read(data)[1]
        except Exception as ex:
            rec(fh, top, path, data, 'SARC-ERR:' + str(ex)); return
        rec(fh, top, path, b'', 'container:SARC:%d' % len(files))
        for n, b, h in files:
            leaf(fh, top, path + '//' + (n if n else '#%08x' % h), b, depth + 1)
        return
    rec(fh, top, path, data, None)


SKIP_SCAN = ('.msbt',)        # 메시지는 따로 전수 추출(messages_ja.json)


def rec(fh, top, path, data, note):
    ext = os.path.splitext(path.split('//')[-1])[1].lower() or '(없음)'
    r = dict(src=top, path=path, ext=ext, size=len(data), magic=data[:8].hex(), md5=hashlib.md5(data).hexdigest() if data else '')
    if note:
        r['note'] = note
    elif ext not in SKIP_SCAN and data:
        h = jp_hits(data)
        if h:
            r['jp'] = h
    fh.write(json.dumps(r, ensure_ascii=False) + '\n')


def main():
    t0 = time.time(); n = 0
    with open(OUT, 'w', encoding='utf-8') as fh:
        for top, base in SRC:
            for dp, dn, fn in os.walk(base):
                dn.sort()
                for f in sorted(fn):
                    p = os.path.join(dp, f)
                    rel = os.path.relpath(p, base).replace(os.sep, '/')
                    leaf(fh, top, rel, open(p, 'rb').read())
                    n += 1
                    if n % 50 == 0:
                        print('%d 파일, %.0f초' % (n, time.time() - t0), flush=True)
    print('끝', n, '%.0f초' % (time.time() - t0))


if __name__ == '__main__':
    main()
