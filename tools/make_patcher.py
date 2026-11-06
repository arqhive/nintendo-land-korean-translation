"""배포용 패처 꾸리기.

  python -I tools/build.py v0.1                 # 먼저 빌드(패치 데이터 work/build/<버전>/payload 도 같이 만듦)
  python -I tools/make_patcher.py v0.1 [--python <내장 파이썬 폴더>]

출력: work/release/ALCJ_KPatch_<버전>/  (패치하기.bat · README_KO.txt · python · licenses · patcher)
      work/release/ALCJ_KPatch_<버전>.zip
패치 데이터 = 바뀐 안쪽 파일만(MSBT 262·BFFNT 4·BFLIM 11). 원본 게임 파일 통째는 담지 않는다.
패처는 빌드와 같은 tools/nl_apply.py 로 다시 만들고 결과 SHA-1 을 빌드본과 대조한다.
"""
import os, sys, shutil, zipfile, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = os.path.join(ROOT, 'work', 'release')
PY_DEFAULT = r'G:\KoreanTranslation\[Wii U] 환영이문록\work\python_embed'


def zip_dir(zpath, top):
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for r, _, fs in os.walk(top):
            for f in sorted(fs):
                fp = os.path.join(r, f)
                if '__pycache__' in fp:
                    continue
                z.write(fp, os.path.relpath(fp, os.path.dirname(top)).replace(os.sep, '/'))
    return os.path.getsize(zpath)


def main():
    ver = sys.argv[1]
    py = sys.argv[sys.argv.index('--python') + 1] if '--python' in sys.argv else PY_DEFAULT
    assert os.path.isfile(os.path.join(py, 'python.exe')), '내장 파이썬이 없음: %s' % py
    payload = os.path.join(ROOT, 'work', 'build', ver, 'payload')
    man = json.load(open(os.path.join(payload, 'manifest.json'), encoding='utf-8'))
    assert man['version'] == ver, (man['version'], ver)
    name = 'ALCJ_KPatch_%s' % ver
    top = os.path.join(REL, name)
    if os.path.exists(top):
        shutil.rmtree(top)
    pdir = os.path.join(top, 'patcher')
    shutil.copytree(payload, os.path.join(pdir, 'payload'))
    os.makedirs(os.path.join(pdir, 'lib'))
    for f in ('nlib.py', 'nl_apply.py'):
        shutil.copyfile(os.path.join(ROOT, 'tools', f), os.path.join(pdir, 'lib', f))
    for f in ('patch.py', 'rules.txt'):
        shutil.copyfile(os.path.join(ROOT, 'patcher', f), os.path.join(pdir, f))
    shutil.copyfile(os.path.join(ROOT, 'patcher', '패치하기.bat'), os.path.join(top, '패치하기.bat'))
    readme = open(os.path.join(ROOT, 'patcher', 'README_KO.txt'), encoding='utf-8').read().replace('{VER}', ver)
    open(os.path.join(top, 'README_KO.txt'), 'w', encoding='utf-8').write(readme)
    shutil.copytree(py, os.path.join(top, 'python'), ignore=shutil.ignore_patterns('__pycache__'))
    shutil.copytree(os.path.join(ROOT, 'licenses'), os.path.join(top, 'licenses'))
    zp = os.path.join(REL, name + '.zip')
    size = zip_dir(zp, top)
    pay = sum(os.path.getsize(os.path.join(r, f)) for r, _, fs in os.walk(os.path.join(pdir, 'payload')) for f in fs)
    print('%s  패치 데이터 %.1fMB · zip %.1fMB' % (zp, pay / 1e6, size / 1e6))
    shutil.copyfile(os.path.join(top, 'README_KO.txt'), os.path.join(REL, 'README_KO.txt'))


if __name__ == '__main__':
    main()
