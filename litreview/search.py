#!/usr/bin/env python3
"""Systematic multi-database search for the Layer-2 'verifiable generative views' review.
Reuses the Qafiya (Layer-1) review pipeline: OpenAlex (primary, DOIs) + arXiv (preprints),
stdlib only. Writes raw JSON per source and a combined, deduplicated candidate list."""
import json, time, urllib.parse, urllib.request, re, sys, os

OUT = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(OUT, "raw")
os.makedirs(RAW, exist_ok=True)
UA = {"User-Agent": "lit-review/1.0 (research; mailto:youssef.hariri@example.org)"}
YEAR_FROM, YEAR_TO = 2018, 2026

def get(url, tries=4, sleep=1.5):
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:
            code = getattr(e, "code", None)
            if code == 429:
                time.sleep(sleep * (i + 2)); continue
            time.sleep(sleep)
    return None

# ---- Concept queries (view-renderer focused) ----
OPENALEX_QUERIES = {
 # A. Declarative view grammars & interactive specs
 "view_grammars": ['"declarative visualization grammar"', '"grammar of graphics" interactive',
                   '"declarative" "visualization" specification', '"Vega-Lite"',
                   '"tree visualization" grammar', '"responsive visualization"'],
 # B. LLM-generated views / generative UI
 "gen_views": ['"generative user interface"', '"large language model" visualization generation',
               '"natural language" "visualization" authoring "large language model"',
               '"large language model" user interface generation',
               '"dynamic application" interface generation', 'model-generated interface',
               '"just-in-time" interface'],
 # C. Data<->view binding, write-back, editing through views
 "binding_writeback": ['direct manipulation editing visualization', '"write-back" data visualization',
                       '"editing" visualization "data" update', 'bidirectional data binding visualization',
                       '"data binding" user interface', 'interactive data editing table view',
                       '"what-if" analysis visualization direct manipulation'],
 # D. Evidence, provenance and audit affordances in UI
 "audit_ui": ['provenance visualization user interface', '"data provenance" "user interface"',
              'explainable AI interface user study', 'citation display generated text interface',
              'uncertainty visualization communication', '"trust" "transparency" interface AI output',
              '"evidence" interface "language model"'],
 # E. Reactive / incremental recompute & invalidation
 "reactive": ['reactive programming user interface', 'incremental computation self-adjusting',
              '"reactive notebook"', 'dataflow reactive web application', 'incremental view maintenance',
              '"live programming" data'],
}

def openalex_search():
    all_rows = {}
    for theme, queries in OPENALEX_QUERIES.items():
        for q in queries:
            params = {
                "filter": f"title_and_abstract.search:{q},from_publication_date:{YEAR_FROM}-01-01,to_publication_date:{YEAR_TO}-12-31",
                "per-page": "25", "sort": "relevance_score:desc",
            }
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
            txt = get(url)
            if not txt:
                print(f"[openalex] FAIL {theme} :: {q}", file=sys.stderr); continue
            try:
                data = json.loads(txt)
            except Exception:
                print(f"[openalex] JSONERR {theme} :: {q}", file=sys.stderr); continue
            for w in data.get("results", []):
                doi = (w.get("doi") or "").replace("https://doi.org/", "")
                key = doi or w.get("id")
                inv = w.get("abstract_inverted_index") or {}
                pos = {}
                for word, idxs in inv.items():
                    for i in idxs: pos[i] = word
                abstract = " ".join(pos[i] for i in sorted(pos))[:600]
                all_rows[key] = {
                    "source": "openalex", "theme": theme, "query": q,
                    "title": w.get("title"), "year": w.get("publication_year"),
                    "venue": ((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                    "doi": doi, "arxiv": None,
                    "cited_by": w.get("cited_by_count"),
                    "abstract": abstract,
                    "oa_id": w.get("id"),
                }
            time.sleep(0.4)
    return all_rows

def arxiv_search():
    rows = {}
    arq = {
      "view_grammars": 'abs:"declarative visualization" OR abs:"grammar of graphics" OR ti:"Vega-Lite"',
      "gen_views": 'abs:"generative user interface" OR abs:"generative UI" OR (abs:"large language model" AND abs:"user interface generation") OR abs:"dynamic application"',
      "binding_writeback": 'abs:"direct manipulation" AND abs:"visualization" AND abs:"editing"',
      "audit_ui": 'abs:"provenance" AND abs:"visualization" AND abs:"interface"',
      "reactive": 'abs:"reactive programming" AND abs:"user interface"',
    }
    for theme, q in arq.items():
        url = "http://export.arxiv.org/api/query?search_query=" + urllib.parse.quote(q) + "&start=0&max_results=30"
        txt = get(url)
        if not txt:
            print(f"[arxiv] FAIL {theme}", file=sys.stderr); continue
        entries = re.findall(r"<entry>(.*?)</entry>", txt, re.S)
        for e in entries:
            def tag(t):
                m = re.search(rf"<{t}>(.*?)</{t}>", e, re.S); return m.group(1).strip() if m else ""
            idurl = tag("id")
            m = re.search(r"arxiv.org/abs/([\d.v]+)", idurl)
            aid = m.group(1) if m else idurl
            title = re.sub(r"\s+", " ", tag("title"))
            summ = re.sub(r"\s+", " ", tag("summary"))[:600]
            pub = tag("published")[:10]
            yr = int(pub[:4]) if pub[:4].isdigit() else None
            authors = re.findall(r"<name>(.*?)</name>", e)
            if yr and yr < YEAR_FROM: continue
            rows["arxiv:"+aid] = {
                "source": "arxiv", "theme": theme, "query": q,
                "title": title, "year": yr, "venue": "arXiv",
                "doi": "", "arxiv": aid, "cited_by": None,
                "abstract": summ, "authors": authors[:6],
            }
        time.sleep(1.0)
    return rows

def main():
    oa = openalex_search()
    ax = arxiv_search()
    with open(os.path.join(RAW, "openalex.json"), "w") as f: json.dump(list(oa.values()), f, indent=1)
    with open(os.path.join(RAW, "arxiv.json"), "w") as f: json.dump(list(ax.values()), f, indent=1)
    combined = {}
    for r in list(oa.values()) + list(ax.values()):
        t = re.sub(r"[^a-z0-9 ]", "", (r["title"] or "").lower()).strip()
        key = t[:60]
        if key in combined:
            if r.get("arxiv") and not combined[key].get("arxiv"):
                combined[key]["arxiv"] = r["arxiv"]
        else:
            combined[key] = dict(r)
    with open(os.path.join(RAW, "combined.json"), "w") as f: json.dump(list(combined.values()), f, indent=1)
    print(f"openalex_raw={len(oa)} arxiv_raw={len(ax)} deduped={len(combined)}")
    from collections import Counter
    print("by_theme:", dict(Counter(r['theme'] for r in combined.values())))

if __name__ == "__main__":
    main()
