# -*- coding: utf-8 -*-
"""닌텐도 랜드(Wii U) 한글 패치 적용기 — 가지고 있는 일본판 게임 파일로 한글판 파일 4개를 만든다.

  패치하기.bat 에 게임 폴더를 끌어다 놓거나(본편·업데이트 폴더 둘 다, 또는 둘이 든 상위 폴더 하나), 실행한 뒤 경로를 입력한다.

필요한 원본(복호화된 일본판):
  본편   0005000010101F00  content/Common/Package/Nzm_Cmn.pack
  업데이트 0005000E10101F00 (v32)  content/JpJapanese/Message/AllMessage.szs, content/JpJapanese/Layout/Font.szs,
                                  content/Common/Package/Static2.pack
결과(원본 파일은 바뀌지 않는다):
  출력/sdcafiine/0005000010101F00/NintendoLandKR/content/...   Wii U 실기(SDCafiine)용
  출력/cemu/NintendoLand_Korean/                              Cemu 그래픽팩용
"""
import os, sys, json, time, hashlib, shutil, traceback

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(HERE, 'lib'))
import nl_apply

PAYLOAD = os.path.join(HERE, 'payload')
OUT = os.path.join(TOP, '출력')


def sha1(b):
    return hashlib.sha1(b).hexdigest()


def find_sources(paths, targets):
    """끌어다 놓은 폴더들 아래에서 원본 파일을 찾는다. 같은 이름이 본편·업데이트에 다 있으므로 크기·SHA-1 로 고른다."""
    found = {}
    want = {}
    for t in targets:
        want.setdefault(os.path.basename(t['src']).lower(), []).append(t)
    for base in paths:
        for dp, dn, fn in os.walk(base):
            for f in fn:
                for t in want.get(f.lower(), []):
                    if t['out'] in found:
                        continue
                    p = os.path.join(dp, f)
                    if os.path.getsize(p) != t['src_size']:
                        continue
                    if sha1(open(p, 'rb').read()) == t['src_sha1']:
                        found[t['out']] = p
    return found


def load_entries(t):
    rep = {}
    with open(os.path.join(PAYLOAD, t['part'] + '.bin'), 'rb') as f:
        for key, off, size in t['entries']:
            f.seek(off); data = f.read(size)
            if t['kind'] == 'pack':
                szs, arc, timg = key.split('//')
                rep.setdefault(szs, {}).setdefault(arc, {})[timg] = data
            else:
                rep[key] = data
    return rep


def link_or_copy(src, dst):
    if os.path.exists(dst):
        os.remove(dst)
    try:
        os.link(src, dst)
    except OSError:
        shutil.copyfile(src, dst)


def main():
    man = json.load(open(os.path.join(PAYLOAD, 'manifest.json'), encoding='utf-8'))
    targets = man['targets']
    print('닌텐도 랜드 한글 패치 %s\n' % man['version'])
    args = [a.strip().strip('"') for a in sys.argv[1:] if a.strip()]
    if not args:
        print('일본판 「Nintendo Land」의 본편·업데이트(v32) 게임 폴더 경로를 입력하세요.\n'
              '둘이 함께 든 상위 폴더 하나를 넣어도 되고, 폴더를 이 창에 끌어다 놓아도 됩니다.\n'
              '두 폴더를 따로 넣으려면 경로 사이를 | 로 나누세요.')
        args = [a.strip().strip('"') for a in input('> ').split('|') if a.strip()]
    for a in args:
        if not os.path.isdir(a):
            print('[오류] 폴더가 아닙니다: %s' % a); return 1
    # 1) 원본 찾기·확인
    print('[1/3] 원본 찾기·확인 (조금 걸립니다)')
    found = find_sources(args, targets)
    miss = [t for t in targets if t['out'] not in found]
    for t in targets:
        if t['out'] in found:
            print('  %-16s 일치  %s' % (os.path.basename(t['out']), found[t['out']]))
    if miss:
        for t in miss:
            where = '본편(0005000010101F00)' if t['from'] == 'game' else '업데이트 v32(0005000E10101F00)'
            print('[오류] %s 원본을 찾지 못했습니다 — %s 의 %s 가 필요합니다.' % (os.path.basename(t['out']), where, t['src']))
        print('\n  일본판(타이틀 ID 0005000010101F00)이 아니거나, 업데이트가 v32 가 아니거나, 이미 패치한 파일일 수 있습니다.')
        return 1
    # 2) 만들기
    print('\n[2/3] 한글판 만들기 (그림 묶음은 다시 압축하느라 1~2분 걸립니다)')
    sd = os.path.join(OUT, 'sdcafiine', man['title_id'], 'NintendoLandKR')
    for t in targets:
        tm = time.time()
        src = open(found[t['out']], 'rb').read()
        rep = load_entries(t)
        if t['kind'] == 'msg':
            data = nl_apply.apply_msg(src, rep)
        elif t['kind'] == 'font':
            data = nl_apply.apply_font(src, rep)
        else:
            data = nl_apply.apply_pack(src, rep)
        if len(data) != t['out_size'] or sha1(data) != t['out_sha1']:
            print('[오류] %s 결과가 기준과 다릅니다. 패치 파일이 손상됐을 수 있습니다.' % os.path.basename(t['out'])); return 1
        p = os.path.join(sd, t['out']); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data)
        print('  %-16s 교체 %3d개 · %.0f초 · 결과 확인 일치' % (os.path.basename(t['out']), len(t['entries']), time.time() - tm))
    # 3) Cemu 그래픽팩
    print('\n[3/3] Cemu 그래픽팩')
    gp = os.path.join(OUT, 'cemu', 'NintendoLand_Korean')
    if os.path.isdir(gp):
        shutil.rmtree(gp)
    os.makedirs(gp, exist_ok=True)
    shutil.copyfile(os.path.join(HERE, 'rules.txt'), os.path.join(gp, 'rules.txt'))
    for t in targets:
        d = os.path.join(gp, t['out']); os.makedirs(os.path.dirname(d), exist_ok=True)
        link_or_copy(os.path.join(sd, t['out']), d)
    print('  %s' % gp)
    print('\n완료.\n  Wii U(SDCafiine): 출력\\sdcafiine 폴더 안의 내용을 SD 카드 wiiu\\sdcafiine\\ 에 복사합니다.'
          '\n  Cemu: 출력\\cemu\\NintendoLand_Korean 폴더를 Cemu 의 graphicPacks 폴더에 넣고 그래픽팩에서 켭니다.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n중단했습니다.'); sys.exit(1)
    except Exception:
        traceback.print_exc(); print('[오류] 예상하지 못한 문제가 생겼습니다.'); sys.exit(1)
