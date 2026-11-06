"""원본 파일 + 바뀐 안쪽 파일 → 한글판 파일. 빌드(tools/build.py)와 배포 패처(patcher/patch.py)가 같이 쓴다.
같은 코드를 쓰므로 패처 결과는 빌드 결과와 바이트까지 같다(패처는 결과 SHA-1 로 다시 확인).
의존: nlib(파이썬 표준 라이브러리만).

  apply_msg(원본 szs, {"바깥.sarc/안쪽 경로.msbt": 바이트})      AllMessage.szs (SARC 두 겹)
  apply_font(원본 szs, {"이름.bffnt": 바이트})                      Font.szs
  apply_pack(원본 pack, {"szs 경로": {"arc 이름": {"timg/x.bflim": 바이트}}})   그림 묶음
"""
import os, struct
from nlib import yaz0_decompress, yaz0_compress, yaz0_compress_best, yaz0_align, sarc_read, sarc_write, sarc_layout, sarc_patch_same_size


def ext_align(data):
    """원본 SARC 의 확장자별 정렬(오프셋이 허용하는 최대 정렬 중 최소값)"""
    info, files = sarc_read(data); lay = dict(sarc_layout(data)); al = {}
    for n, s in lay.items():
        ex = os.path.splitext(n)[1]
        a = next(a for a in (0x2000, 0x1000, 0x800, 0x400, 0x200, 0x100, 0x80, 0x40, 0x20, 0x10, 8, 4) if s % a == 0)
        al[ex] = min(al.get(ex, 0x2000), a)
    return info, files, al


def repack(orig, replace):
    """원본 SARC 와 같은 정렬·순서로 다시 묶기(replace 에 없는 파일은 원본 그대로)"""
    info, files, al = ext_align(orig)
    return sarc_write([(n, replace.get(n, b)) for n, b, _ in files], info['mult'], info['endian'],
                      info['data_off'], lambda n, b: al[os.path.splitext(n)[1]], info['ver'])


def apply_msg(src_szs, rep):
    raw = yaz0_decompress(src_szs)
    outer = {}
    for on, ob, _ in sarc_read(raw)[1]:
        inner = {k.split('/', 1)[1]: v for k, v in rep.items() if k.split('/', 1)[0] == on}
        outer[on] = repack(ob, inner) if inner else ob
    return yaz0_compress(repack(raw, outer), align=yaz0_align(src_szs))


def apply_font(src_szs, rep):
    raw = yaz0_decompress(src_szs)
    return yaz0_compress(repack(raw, rep), align=yaz0_align(src_szs))


def apply_pack(src_pack, rep):
    rp = {}
    files = {n: b for n, b, _ in sarc_read(src_pack)[1]}
    for szs, arcs in rep.items():
        d = yaz0_decompress(files[szs])
        sub = {n: b for n, b, _ in sarc_read(d)[1]}
        arc_rep = {arc: sarc_patch_same_size(sub[arc], timgs) for arc, timgs in arcs.items()}
        nd = sarc_patch_same_size(d, arc_rep)                       # .arc 도 길이 같음 → 제자리
        rp[szs] = yaz0_compress_best(nd, 256, align=yaz0_align(files[szs]))   # 정렬값은 원본대로(0 이면 실기 오류)
    return repack(src_pack, rp)
