#!/usr/bin/env python3
"""Why did the phase 1 judge call 47 of Jeff's 2005 list stories `not`? (2026-09-28)

For every list story Gemini called `not` in results/consensus/phase1/full.json, measures
whether the PASSAGE shown to the judge actually held his story -- the share of his story's
word bigrams found in the passage (`cov`) and the share of the passage that is his story
(`share`) -- and prints his text beside the judge's reason. No model calls.

Result on 2026-09-28: 31 of 47 fully covered, none below 60% -- the passage was right;
the RULE was wrong (docs/findings/2026-09-28-consensus-phase1.md section 7).

    python3 scripts/diagnose_phase1_list_misses.py results/consensus/phase1/list_misses.json
"""
import json,re,sys,importlib.util,collections
sys.path.insert(0,'.')  # run from the repo root
spec=importlib.util.spec_from_file_location('j','scripts/judge_labelled_spans.py'); j=importlib.util.module_from_spec(spec); spec.loader.exec_module(j)
F=json.load(open('results/consensus/phase1/full.json'))['rows']
U={u['id']:u for u in json.load(open('results/consensus/phase1/labels.json'))['units']}
lists={}
for t in ['ketubot','kiddushin','gittin','yevamot']:
    for i,s in enumerate(json.load(open(f'results/recall/{t}_jeff2005_matches.json'))): lists[s.get('id') or f'{t}_{i+1:03d}']=s
strip=lambda x:re.sub(r'[֑-ׇ]','',re.sub('<[^>]+>','',x or ''))
words=lambda x:re.findall(r'[א-ת]+',strip(x))
texts={}
out=[]
for r in F:
    if r['kind']!='list': continue
    g=r['answers']['gemini']
    if g.get('verdict')!='not': continue
    u=U[r['id']]; t=u['tractate']
    if t not in texts: texts[t]=j.Text(t)
    T=texts[t]
    jw=words(lists[u['key']]['text']); pw=[]
    for c in u['cells']: pw+=words(T.seg[tuple(c)].get('hebrew',''))
    js=set(zip(jw,jw[1:])); ps=set(zip(pw,pw[1:]))
    cov=len(js&ps)/max(1,len(js)); share=len(js&ps)/max(1,len(ps))
    out.append(dict(id=u['key'],ref=u['list_ref'],cells=len(u['cells']),jw=len(jw),pw=len(pw),cov=round(cov,2),share=round(share,2),reason=g['reason'],rules=g['rules'],jtext=' '.join(jw[:25])))
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False,indent=1)
print('n',len(out))
print('coverage of his text inside passage: <0.6:',sum(o['cov']<0.6 for o in out),' 0.6-0.9:',sum(0.6<=o['cov']<0.9 for o in out),' >=0.9:',sum(o['cov']>=0.9 for o in out))
print('his story share of passage: <0.3:',sum(o['share']<0.3 for o in out),' 0.3-0.7:',sum(0.3<=o['share']<0.7 for o in out),' >=0.7:',sum(o['share']>=0.7 for o in out))
print('his words median',sorted(o['jw'] for o in out)[len(out)//2], 'passage words median',sorted(o['pw'] for o in out)[len(out)//2])
print(collections.Counter(tuple(sorted(o['rules'])) for o in out).most_common(6))
