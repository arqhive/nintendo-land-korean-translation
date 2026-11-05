"""work/extract/Message 의 MSBT 전부를 work/survey/messages_ja.json 으로(라벨·원문)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__)); sys.stdout.reconfigure(encoding='utf-8')
from nlib import *
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, 'work', 'extract', 'Message'); out = []
for dp, dn, fn in os.walk(src):
    for f in sorted(fn):
        p = os.path.join(dp, f); rel = os.path.relpath(p, src).replace(os.sep, '/')
        m = msbt_read(open(p, 'rb').read())
        for i, t in enumerate(m['texts']):
            out.append(dict(file=rel, idx=i, label=m['labels'].get(i), ja=msbt_text_to_str(t, m['endian'])))
os.makedirs(os.path.join(ROOT, 'work', 'survey'), exist_ok=True)
json.dump(out, open(os.path.join(ROOT, 'work', 'survey', 'messages_ja.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(out))
