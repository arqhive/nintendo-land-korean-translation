"""다시 번역(11/17)에서 손대지 않을 줄: 사용자가 직접 고치라고 한 줄(커밋 316c63b 등).
work/tl/retl/keep.json 에 [id…] 로 적는다. retl_merge.py 는 이 줄을 바꾸려 하면 멈춘다.
"""
import os, sys, json, subprocess
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMMITS = ['316c63b']
keep = set()
for c in COMMITS:
    for g in os.listdir(os.path.join(ROOT, 'translation', 'ko')):
        p = 'translation/ko/' + g
        a = subprocess.run(['git', '-C', ROOT, 'show', c + '^:' + p], capture_output=True).stdout
        b = subprocess.run(['git', '-C', ROOT, 'show', c + ':' + p], capture_output=True).stdout
        if not a or not b:
            continue
        A = {e['id']: e['ko'] for e in json.loads(a)}; B = {e['id']: e['ko'] for e in json.loads(b)}
        for i in B:
            if A.get(i) != B[i]:
                keep.add(i); print(g, i, repr(B[i]))
# 커밋 기록 밖에서 사용자가 정한 줄(대화로 지시): 4210 「3안」, 4213
keep |= {4210, 4213}
json.dump(sorted(keep), open(os.path.join(ROOT, 'work', 'tl', 'retl', 'keep.json'), 'w'), indent=0)
print('지킬 줄', len(keep), sorted(keep))
