#!/usr/bin/env python3
"""Does a passage look speech-only because its span stops before the action?

Re-runs the quasi-speech-act screen on the 13 entries it called speech-only that
the earlier PR #36 screen had cleared, this time with up to 2 extra segments of
following context. An entry that FLIPS to non_speech_event was never a criteria
case -- it is a Boundaries defect wearing one. PR #36 found this confound by hand
in 3 of its 6; this measures it.

Result 2026-09-03: 9 of 13 flip. See
docs/findings/2026-09-03-quasi-speech-acts-and-the-span-confound.md

Usage: python3 scripts/test_span_extension_confound.py
"""
import json,os,re,sys,pathlib
sys.path.insert(0,'.')
ROOT=pathlib.Path('.')
for line in open('.env'):
    if '=' in line and not line.strip().startswith('#'):
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
from google import genai
from google.genai import types
import importlib.util
spec=importlib.util.spec_from_file_location("m","scripts/screen_quasi_speech_acts.py")
# reuse just the PROMPT text
src=open('scripts/screen_quasi_speech_acts.py').read()
PROMPT=src.split('PROMPT = """')[1].split('"""')[0]
TAG=re.compile(r"<[^>]+>")
clean=lambda s: TAG.sub("",s or "").strip()

targets=[("ketubot","Ketubot 105a",13,13),("ketubot","Ketubot 10a",9,10),("ketubot","Ketubot 111a",10,11),
("ketubot","Ketubot 50b",9,10),("ketubot","Ketubot 53a",12,12),("ketubot","Ketubot 65a",5,5),
("ketubot","Ketubot 65a",10,10),("ketubot","Ketubot 66b",9,9),("ketubot","Ketubot 69a",10,10),
("kiddushin","Kiddushin 40b",7,7),("kiddushin","Kiddushin 44b",6,6),("kiddushin","Kiddushin 50a",5,5),
("kiddushin","Kiddushin 72b",10,10)]
G={t:json.load(open(f'results/canonical/{t}_canonical.json')) for t in ('ketubot','kiddushin')}
client=genai.Client(api_key=os.environ['GOOGLE_API_KEY'])
from concurrent.futures import ThreadPoolExecutor
def run(t):
    tract,ref,a,b=t
    page=next(p for p in G[tract]['pages'] if p['ref']==ref)
    segs={s['index']:s for s in page['segments']}
    idxs=[j for j in range(a,b+3) if j in segs]          # +2 segments of context
    he="\n".join(clean(segs[j]['hebrew']) for j in idxs)
    en="\n".join(clean(segs[j]['english']) for j in idxs)
    p=PROMPT.format(hebrew=he[:12000],english=en[:12000])
    r=client.models.generate_content(model='gemini-3-flash-preview',contents=p,
        config=types.GenerateContentConfig(max_output_tokens=8192,temperature=0.1,
        response_mime_type='application/json',thinking_config=types.ThinkingConfig(thinking_level='LOW')))
    txt="".join(x.text for x in r.candidates[0].content.parts if x.text and not getattr(x,'thought',False))
    i,j=txt.find('{'),txt.rfind('}')
    v=json.loads(txt[i:j+1])
    return (ref,a,b,len(idxs)-(b-a+1),v.get('verdict'),v.get('evidence_english','')[:70])
with ThreadPoolExecutor(max_workers=6) as ex: rows=list(ex.map(run,targets))
flip=0
for ref,a,b,extra,vd,ev in rows:
    mark='FLIPS' if vd=='non_speech_event' else 'holds'
    if vd=='non_speech_event': flip+=1
    print(f"{mark:6} {ref:14} {a}-{b} (+{extra} seg)  {ev}")
print(f"\n{flip}/13 flip when the span is extended by up to 2 segments")
