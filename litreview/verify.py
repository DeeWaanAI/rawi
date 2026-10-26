#!/usr/bin/env python3
"""Verify curated included works against OpenAlex (DOI) / arXiv API; save canonical metadata.
Same approach as the Layer-1 review's verify.py."""
import json, os, re, time, urllib.parse, urllib.request
RAW = os.path.join(os.path.dirname(os.path.abspath(__file__)), "raw")
UA = {"User-Agent": "lit-review/1.0"}

def get(url, tries=3):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode("utf-8","replace")
        except Exception:
            time.sleep(1.5*(i+1))
    return None

INC = [
 # A. Declarative view grammars & interactive specs
 ("satyanarayan2017vegalite", {"doi":"10.1109/tvcg.2016.2599030"}),   # foundational, pre-window
 ("vanderplas2018altair", {"doi":"10.21105/joss.01057"}),
 ("li2020gotree", {"doi":"10.1145/3313831.3376297"}),
 ("kim2022cicero", {"doi":"10.1145/3491102.3517455"}),
 ("liu2021atlas", {"doi":"10.1109/vis49827.2021.9623315"}),
 ("annogram2025", {"doi":"10.1109/vis60296.2025.00053"}),
 ("dibia2019data2vis", {"doi":"10.1109/mcg.2019.2924636"}),
 ("narechania2020nl4dv", {"doi":"10.1109/tvcg.2020.3030378"}),
 # B. LLM-generated views / generative UI
 ("wang2023dataformulator", {"doi":"10.1109/tvcg.2023.3326585"}),
 ("wang2024dataformulator2", {"arxiv":"2408.16119"}),
 ("dibia2023lida", {"doi":"10.18653/v1/2023.acl-demo.11"}),
 ("datatales2023", {"doi":"10.1109/vis54172.2023.00055"}),
 ("chen2025geninterfaces", {"arxiv":"2508.19227"}),
 ("lee2025guidef", {"doi":"10.1145/3715668.3736365"}),
 ("peng2026guipers", {"arxiv":"2604.09876"}),
 ("legoui2026", {"arxiv":"2608.04293"}),
 ("xie2026swcontent", {"arxiv":"2603.21334"}),
 ("bespoke2024", {"doi":"10.1145/3686215.3688372"}),
 ("viseval2024", {"doi":"10.1109/tvcg.2024.3456320"}),
 ("vizgeneval2024", {"arxiv":"2401.11255"}),
 ("ross2023assistant", {"doi":"10.1145/3581641.3584037"}),
 # C. Data<->view binding, write-back, editing through views
 ("liu2018dataillustrator", {"doi":"10.1145/3173574.3173697"}),
 ("zong2020lyra2", {"doi":"10.1109/tvcg.2020.3030367"}),
 ("structgraphics2020", {"doi":"10.1109/tvcg.2020.3030476"}),
 ("directvis2026", {"doi":"10.1109/pacificvis68791.2026.00014"}),
 ("nlvkgedit2025", {"doi":"10.1145/3731443.3771344"}),
 ("conlen2018idyll", {"doi":"10.1145/3242587.3242600"}),
 # D. Evidence, provenance and audit affordances in UI
 ("hoque2024hallmark", {"doi":"10.1145/3613904.3641895"}),
 ("gao2023alce", {"arxiv":"2305.14627"}),
 ("min2023factscore", {"arxiv":"2305.14251"}),
 ("hullman2019uncertainty", {"doi":"10.1109/tvcg.2019.2934287"}),
 ("provdensity2026", {"doi":"10.24963/ijcai.2026/857"}),
 ("graspableai2021", {"doi":"10.1145/3430524.3442704"}),
 ("illusion2021", {"doi":"10.1145/3397481.3450644"}),
 ("xnli2023", {"doi":"10.1109/tvcg.2023.3240003"}),
 ("analyticprov2018", {"doi":"10.1007/978-981-10-8612-0_66"}),
 # E. Reactive / incremental recompute & invalidation
 ("reactnbfail2025", {"arxiv":"2511.21994"}),
 ("glinda2021", {"doi":"10.1145/3411764.3445267"}),
 ("ivm2018", {"doi":"10.1145/3183713.3183758"}),
 ("fkivm2023", {"doi":"10.1145/3588720"}),
 ("meerkat2024", {"arxiv":"2407.06885"}),
 ("marimolens2026", {"arxiv":"2609.19839"}),
]

def oa_by_doi(doi):
    txt = get("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
    if not txt: return None
    try: w = json.loads(txt)
    except: return None
    if w.get("error"): return None
    return canon(w)

def arxiv_by_id(aid):
    txt = get("http://export.arxiv.org/api/query?id_list="+aid)
    if not txt: return None
    m = re.search(r"<entry>(.*?)</entry>", txt, re.S)
    if not m: return None
    e = m.group(1)
    def tag(t):
        mm = re.search(rf"<{t}>(.*?)</{t}>", e, re.S); return re.sub(r"\s+"," ",mm.group(1).strip()) if mm else ""
    return {"title":tag("title"), "year":tag("published")[:4],
            "authors":re.findall(r"<name>(.*?)</name>", e)[:8],
            "venue":"arXiv", "doi":"10.48550/arXiv."+aid, "arxiv":aid, "source":"arxiv"}

def canon(w):
    auth = [a.get("author",{}).get("display_name") for a in w.get("authorships",[])][:8]
    doi = (w.get("doi") or "").replace("https://doi.org/","")
    return {"title":w.get("title"), "year":w.get("publication_year"),
            "authors":auth, "venue":((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
            "doi":doi, "arxiv":None, "cited_by":w.get("cited_by_count"), "source":"openalex"}

out = {}
for key, spec in INC:
    rec = None
    if "doi" in spec: rec = oa_by_doi(spec["doi"])
    elif "arxiv" in spec: rec = arxiv_by_id(spec["arxiv"])
    status = "OK" if rec and rec.get("title") else "MISS"
    out[key] = {"status":status, "spec":spec, "rec":rec}
    t = (rec or {}).get("title") if rec else None
    print(f"[{status}] {key}: {t} ({(rec or {}).get('year')}) | doi={(rec or {}).get('doi')}")
    time.sleep(0.25)

json.dump(out, open(os.path.join(RAW,"included_verified.json"),"w"), indent=1)
miss = [k for k,v in out.items() if v["status"]=="MISS"]
print("\nTOTAL", len(out), "OK", len(out)-len(miss), "MISS", len(miss), miss)
