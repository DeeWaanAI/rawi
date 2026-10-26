#!/usr/bin/env python3
import json, os
from collections import defaultdict
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
rows = json.load(open(os.path.join(RAW, "combined.json")))

BOOST = {
 "view_grammars": ["declarative","grammar","visualization","vega","specification","interactive","tree","responsive","chart","composable"],
 "gen_views": ["generative ui","generative user interface","large language model","llm","interface generation","visualization generation","natural language","prompt","dynamic application","just-in-time","code generation","agent"],
 "binding_writeback": ["direct manipulation","editing","write-back","binding","update","data","visualization","what-if","table","propagat","two-way","bidirectional"],
 "audit_ui": ["provenance","evidence","trust","transparency","explainab","uncertainty","citation","audit","verif","interface","user study","attribution"],
 "reactive": ["reactive","incremental","self-adjusting","dataflow","notebook","propagation","invalidation","live programming","caching","change"],
}

def score(r):
    txt = ((r.get("title") or "") + " " + (r.get("abstract") or "")).lower()
    s = 0
    for k in BOOST.get(r["theme"], []):
        if k.lower() in txt: s += 2
    if r.get("cited_by"): s += min(r["cited_by"], 200)/20.0
    return s

by_theme = defaultdict(list)
for r in rows:
    r["_score"] = score(r)
    by_theme[r["theme"]].append(r)

kept = 0
for theme in ["view_grammars","gen_views","binding_writeback","audit_ui","reactive"]:
    lst = sorted(by_theme.get(theme, []), key=lambda x: x["_score"], reverse=True)
    print(f"\n===== {theme}  (candidates={len(lst)}) =====")
    for r in lst[:22]:
        if r["_score"] < 4: break
        kept += 1
        ident = r.get("doi") or ("arXiv:"+r["arxiv"] if r.get("arxiv") else r.get("oa_id",""))
        print(f"[{r['_score']:.1f}] {r.get('year')} | {(r.get('venue') or '?')[:28]} | {(r.get('title') or '')[:95]} | {ident} | cites={r.get('cited_by')}")
print("\nkept_by_score>=4:", kept)
