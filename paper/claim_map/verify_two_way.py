#!/usr/bin/env python3
"""Two-way verifier (monitor spec). Per datapoint entry:
  (a) frozen artifact value at `path` == `expect`
  (b) `marker` text appears in draft.tex (multi-line markers normalized)
Exit 0 only when every entry passes both directions. Frozen sources only."""
import json, math, re, subprocess, sys
from pathlib import Path

L2 = Path(__file__).resolve().parents[2]
MAP = L2 / "paper" / "claim_map"
dp = json.loads((MAP / "datapoints.json").read_text())
draft_raw = (L2 / "paper" / "draft.tex").read_text()
draft_norm = re.sub(r"\s+", " ", draft_raw)
fails = []

def artifact_value(e):
    src = L2 / e["source"]
    segs = e["path"]
    if e["source"] == "experiments/results/raw/e1_trace.jsonl":
        trace = [json.loads(l) for l in open(src)]
        step = segs[0].split("step:")[1]
        return [t for t in trace if t["step"] == step][0][segs[1]]
    if e["source"] == "experiments/results/raw/e2_edits.jsonl":
        rows = [json.loads(l) for l in open(src)]
        return len(rows) if segs[0] == "count" else sum(1 for r in rows if r["ok"])
    if e["source"] == "experiments/corpus/datasets/expenses/data.jsonl":
        return sum(1 for _ in open(src))
    if e["source"] == "litreview/raw/[openalex+arxiv].json":
        return (len(json.loads((L2 / "litreview/raw/openalex.json").read_text()))
                + len(json.loads((L2 / "litreview/raw/arxiv.json").read_text())))
    if e["source"].startswith("litreview/raw/"):
        return len(json.loads(src.read_text()))
    if e["source"] == "litreview/screen.py":
        scr = subprocess.run([sys.executable, str(L2 / "litreview" / "screen.py")],
                             capture_output=True, text=True).stdout
        return int(re.search(r"kept_by_score>=4: (\d+)", scr).group(1))
    if e["source"] == "view-renderer/dvr/*.py":
        return sum(sum(1 for ln in f.read_text().splitlines()
                       if ln.strip() and not ln.strip().startswith("#"))
                   for f in (L2 / "view-renderer" / "dvr").glob("*.py"))
    data = json.loads(src.read_text())
    for s in segs:
        data = data[int(s)] if isinstance(data, list) else data[s]
    return data

for e in dp["datapoints"]:
    # (a) value direction
    try:
        v = artifact_value(e)
    except Exception as ex:
        fails.append((e["id"], f"artifact error: {ex}")); continue
    exp = e["expect"]
    if isinstance(v, bool):
        ok = v == exp
    else:
        a, b = float(v), float(exp)
        ok = (math.isnan(a) and math.isnan(b)) or abs(a - b) <= 0.006
    if not ok:
        fails.append((e["id"], f"value mismatch: artifact={v} expect={exp}"))
    # (b) marker direction (in the .tex)
    marker = re.sub(r"\s+", " ", e["marker"])
    if marker not in draft_norm:
        fails.append((e["id"], f"marker not in draft: {marker[:60]!r}"))

if fails:
    for f in fails:
        print("FAIL", *f)
    sys.exit(1)
print(f"OK: {dp['count']} datapoints — artifact value == expect AND marker present in draft")
