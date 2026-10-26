#!/usr/bin/env python3
"""Build paper/claim_map/datapoints.json in the monitor-required schema:
{id, claim, source (frozen raw artifact only), path (JSON key path), expect,
marker (text that must appear in draft.tex)}.
Every headline number in the paper, data-first from frozen artifacts."""
import json, re, subprocess, sys
from pathlib import Path

L2 = Path(__file__).resolve().parents[2]
MAP = L2 / "paper" / "claim_map"
RAW = L2 / "experiments" / "results" / "raw"
LR = L2 / "litreview" / "raw"

entries = []
def add(id, claim, source, path, expect, marker):
    entries.append({"id": id, "claim": claim, "source": source, "path": path,
                    "expect": expect, "marker": marker})

e3 = json.loads((RAW / "e3_counts.json").read_text())
add("DP-E3-1", "DVR total tokens for 100 interactions", "experiments/results/raw/e3_counts.json",
    ["dvr", "T_total"], e3["dvr"]["T_total"], "4{,}732")
add("DP-E3-2", "REGEN total tokens for 100 interactions", "experiments/results/raw/e3_counts.json",
    ["regen", "T_total"], e3["regen"]["T_total"], "639{,}300")
add("DP-E3-3", "cost ratio REGEN/DVR", "experiments/results/raw/e3_counts.json",
    ["ratio"], e3["ratio"], "135$\\times$")
add("DP-E3-4", "breakeven interactions", "experiments/results/raw/e3_counts.json",
    ["breakeven_interactions"], e3["breakeven_interactions"], "0.74")
add("DP-E3-5", "REGEN per-interaction tokens", "experiments/results/raw/e3_counts.json",
    ["regen", "T_per_interaction"], e3["regen"]["T_per_interaction"], "6{,}393")
add("DP-E3-6", "interaction count K", "experiments/results/raw/e3_counts.json",
    ["interactions_k"], e3["interactions_k"], "100 interactions")

trace = [json.loads(l) for l in open(RAW / "e1_trace.jsonl")]
edit = [t for t in trace if t["step"] == "1_user_edit"][0]
wb = [t for t in trace if t["step"] == "2_writeback_invalidation"][0]
verdict = [t for t in trace if t["step"] == "4_verdict"][0]
add("DP-E1-1", "E1 edited record prior value", "experiments/results/raw/e1_trace.jsonl",
    ["step:1_user_edit", "prior"], edit["prior"], "820.89")
add("DP-E1-2", "E1 edited record new value", "experiments/results/raw/e1_trace.jsonl",
    ["step:1_user_edit", "new"], edit["new"], "1{,}320.89")
add("DP-E1-3", "E1 invalidated binding count", "experiments/results/raw/e1_trace.jsonl",
    ["step:2_writeback_invalidation", "invalidated"], wb["invalidated"], "four\ndependent bindings")
add("DP-E1-4", "E1 durability verdict", "experiments/results/raw/e1_trace.jsonl",
    ["step:4_verdict", "c6_durability_closed"], verdict["c6_durability_closed"], "open claim is closed")

e2 = [json.loads(l) for l in open(RAW / "e2_edits.jsonl")]
meta = json.loads((RAW / "e2_meta.json").read_text())
add("DP-E2-1", "E2 edit count", "experiments/results/raw/e2_edits.jsonl",
    ["count"], len(e2), "100/100")
add("DP-E2-2", "E2 re-proved count", "experiments/results/raw/e2_edits.jsonl",
    ["ok_count"], sum(1 for r in e2 if r["ok"]), "100\\% round-trip")
add("DP-E2-3", "E2 wall time s", "experiments/results/raw/e2_meta.json",
    ["wall_s"], meta["wall_s"], "1.0\\,s wall time")

n_corpus = sum(1 for _ in open(L2 / "experiments/corpus/datasets/expenses/data.jsonl"))
add("DP-COR-1", "corpus record count", "experiments/corpus/datasets/expenses/data.jsonl",
    ["count"], n_corpus, "63\nrecords")

lim = json.loads((L2 / "view-renderer" / "limits_results.json").read_text())
curve = lim["L4_scale"]["curve"]
markers = {10: "0.03\\,s at 100", 100: "0.03\\,s at 100", 1000: "2.5\\,s at 1{,}000",
           10000: "123\\,s at\n10{,}000"}
for i, c in enumerate(curve):
    add(f"DP-L4-{i}", f"render seconds at {c['nodes']} nodes", "view-renderer/limits_results.json",
        ["L4_scale", "curve", str(i), "render_s"], c["render_s"], markers[c["nodes"]])
add("DP-L3-1", "L3 shared-error fabrication caught?", "view-renderer/limits_results.json",
    ["L3_shared_error", "caught"], lim["L3_shared_error"]["caught"], "does not and cannot\ncatch")
add("DP-L5-1", "L5 concurrency consistent", "view-renderer/limits_results.json",
    ["L5_concurrency", "consistent"], lim["L5_concurrency"]["consistent"], "last-writer-wins")
add("DP-L7-1", "L7 coverage honesty", "view-renderer/limits_results.json",
    ["L7_coverage_honesty", "pass"], lim["L7_coverage_honesty"]["pass"], "33\\%")

l6 = json.loads((RAW / "l6.json").read_text())
add("DP-L6-1", "L6 requests attempted", "experiments/results/raw/l6.json",
    ["requests"], l6["requests"], "six shell-relevant")
add("DP-L6-2", "L6 expressible count", "experiments/results/raw/l6.json",
    ["expressible"], l6["expressible"], "4 of 6")
add("DP-L6-3", "L6 expressible rate", "experiments/results/raw/l6.json",
    ["rate"], l6["rate"], "66.7\\%")

loc_nc = loc_tot = 0
for f in (L2 / "view-renderer" / "dvr").glob("*.py"):
    lines = f.read_text().splitlines()
    loc_tot += len(lines)
    loc_nc += sum(1 for ln in lines if ln.strip() and not ln.strip().startswith("#"))
add("DP-LOC-1", "prototype non-comment LOC", "view-renderer/dvr/*.py",
    ["non_comment_loc"], loc_nc, "$\\sim$300 LOC")

n_oa = len(json.loads((LR / "openalex.json").read_text()))
n_ax = len(json.loads((LR / "arxiv.json").read_text()))
n_dd = len(json.loads((LR / "combined.json").read_text()))
n_inc = len(json.loads((LR / "included_verified.json").read_text()))
scr = subprocess.run([sys.executable, str(L2 / "litreview" / "screen.py")],
                     capture_output=True, text=True).stdout
n_scr = int(re.search(r"kept_by_score>=4: (\d+)", scr).group(1))
add("DP-REV-1", "review identified records", "litreview/raw/[openalex+arxiv].json",
    ["count"], n_oa + n_ax, "797 records")
add("DP-REV-2", "review deduplicated records", "litreview/raw/combined.json",
    ["count"], n_dd, "749")
add("DP-REV-3", "review screened records", "litreview/screen.py",
    ["kept"], n_scr, "110 screened")
add("DP-REV-4", "review included works", "litreview/raw/included_verified.json",
    ["count"], n_inc, "42 synthesised")

out = {"schema": "datapoints-v2-monitor", "generated": "2026-10-26",
       "paper": "paper/draft.tex", "count": len(entries), "datapoints": entries}
(MAP / "datapoints.json").write_text(json.dumps(out, indent=1))
print(f"datapoints: {len(entries)}")
