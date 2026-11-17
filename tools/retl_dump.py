"""다시 번역(11/17)용: 묶음의 한 구간을 원문·영어판·지금 번역·용어집 맞는 말과 함께 찍는다.
사용: python -I tools/retl_dump.py <묶음> <시작> <개수>
결과는 화면에만 찍는다(원문이 들어 있어 파일로 남기지 않음).
"""
import os, sys, json, re
sys.stdout.reconfigure(encoding='utf-8')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
g, start, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pk = json.load(open(os.path.join(ROOT, 'work', 'tl', 'packet_%s.json' % g), encoding='utf-8'))
ko = {x['id']: x['ko'] for x in json.load(open(os.path.join(ROOT, 'translation', 'ko', '%s.json' % g), encoding='utf-8'))}
gl = [x for x in json.load(open(os.path.join(ROOT, 'translation', 'glossary.json'), encoding='utf-8')) if len(x['ja']) >= 2]
SP = {'모니타→플레이어': '모니타', '시스템 안내→플레이어': '안내', '알림(큰 글씨)→플레이어': '큰글씨', '석상 명판+모니타→플레이어': '석상',
      '모니타 공주→플레이어': '공주', '모니타(수련)→플레이어': '수련', '다크 모니타→플레이어': '다크', '가짜 공주→플레이어': '가짜공주'}
print('총 %d줄 중 %d~%d' % (len(pk), start, min(len(pk), start + n) - 1))
def cut(s):
    s = repr(s)[1:-1]
    return s if len(s) <= 300 else s[:300] + ' …(%d자 생략)' % (len(s) - 300)


for i, x in enumerate(pk[start:start + n], start):
    hits = sorted({'%s=%s' % (t['ja'], t['ko']) for t in gl if t['ja'] in x['ja']})
    sp = SP.get(x['speaker'], x['speaker'] or '-')
    lim = '%s×%s' % (x['max_chars'], x['max_lines'])
    print('#%d id=%d [%s] %s %s%s' % (i, x['id'], sp, x['file'][:-5] + ':' + (x['label'] or ''), lim, ' 음성' if x.get('voiced') else ''))
    print('  ja:', cut(x['ja']))
    if x['en']:
        print('  en:', cut(x['en']))
    print('  ko:', cut(ko.get(x['id'], '')))
    if hits:
        print('  용어:', ' · '.join(hits))
