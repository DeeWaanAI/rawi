#!/usr/bin/env python3
"""Freeze the Tier-C experiment corpus. Run ONCE; artifacts are inputs, never
regenerated mid-analysis. Writes corpus/ with dataset, bindings, view, edit script."""
import json, random, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CORPUS = ROOT / "corpus"
random.seed(20261019)  # frozen seed

# --- dataset: 60 expense records across Q1-Q3 2026 ---
cats = ["travel", "food", "tools", "other"]
periods = {"Q1": ("2026-0%d", [1, 2, 3]), "Q2": ("2026-0%d", [4, 5, 6]), "Q3": ("2026-0%d", [7, 8, 9])}
records = []
i = 0
for period, (fmt, months) in periods.items():
    for m in months:
        for k in range(7):  # 21 records per period -> 63 total
            i += 1
            records.append({
                "id": f"r_{i:03d}",
                "date": f"2026-{m:02d}-{random.randint(1,28):02d}",
                "period": period,
                "amount": round(random.uniform(40, 900), 2),
                "category": random.choice(cats),
            })

schema = {"dataset": "expenses", "id_field": "id",
          "fields": {"id": "id", "date": "timestamp", "period": "enum[Q1,Q2,Q3]",
                     "amount": "number", "category": "enum[travel,food,tools,other]"},
          "derivations": ["sum", "avg", "count", "min", "max"]}

def s(period):
    return round(sum(r["amount"] for r in records if r["period"] == period), 2)

q2, q3 = s("Q2"), s("Q3")
trend = round((q3 - q2) / q2, 4)

# --- bindings: totals per period, a record-level cell, and two claims ---
bindings = []
for p in ("Q1", "Q2", "Q3"):
    bindings.append({
        "id": f"b_tot_{p.lower()}", "kind": "view",
        "target": {"view": "v_exp", "node": f"cell:total_{p.lower()}"},
        "sources": [{"dataset": "ds:expenses", "filter": f"period={p}", "field": "amount",
                     "key_path": ["amount"], "verbatim_excerpt": str(s(p))}],
        "derivation": f"sum(amount) where period='{p}'", "value": s(p), "statistic": "sum",
        "device": "local", "authoritative_artifact": "datasets/expenses/data.jsonl",
        "provenance": {"created_by": "experiment-freeze", "created_at": "2026-10-19T00:00Z"},
        "check": {"provenance": "PENDING"}})
bindings.append({
    "id": "b_cell_r42", "kind": "view", "target": {"view": "v_exp", "node": "cell:r_042"},
    "sources": [{"dataset": "ds:expenses", "filter": "period=Q3", "field": "amount",
                 "key_path": ["amount"], "verbatim_excerpt": str(records[50]["amount"])}],
    "derivation": "sum(amount) where period='Q3'", "value": q3, "statistic": "sum",
    "device": "local", "authoritative_artifact": "datasets/expenses/data.jsonl",
    "provenance": {"created_by": "experiment-freeze", "created_at": "2026-10-19T00:00Z"},
    "check": {"provenance": "PENDING"}})
bindings.append({
    "id": "b_trend", "kind": "claim", "target": {"view": "v_exp", "node": "claim:trend"},
    "sources": [{"dataset": "ds:expenses", "field": "amount", "key_path": ["amount"],
                 "verbatim_excerpt": str(q2)}],
    "derivation": "sum(amount) where period='Q3'", "value": q3, "statistic": "sum",
    "device": "local", "authoritative_artifact": "datasets/expenses/data.jsonl",
    "assertion": {"statement": f"Q3 spend changed {trend:+.1%} vs Q2",
                  "predicate": "direction", "expected": trend, "tolerance": 0.005,
                  "both_sides": {"Q2": {"derivation": "sum(amount) where period='Q2'"},
                                 "Q3": {"derivation": "sum(amount) where period='Q3'"}}},
    "provenance": {"created_by": "experiment-freeze", "created_at": "2026-10-19T00:00Z"},
    "check": {"provenance": "PENDING", "semantic": "PENDING"}})
bindings.append({
    "id": "b_count", "kind": "claim", "target": {"view": "v_exp", "node": "claim:count"},
    "sources": [{"dataset": "ds:expenses", "filter": "period=Q3", "field": "amount",
                 "key_path": ["amount"], "verbatim_excerpt": "21"}],
    "derivation": "count(amount) where period='Q3'", "value": 21.0, "statistic": "count",
    "device": "local", "authoritative_artifact": "datasets/expenses/data.jsonl",
    "assertion": {"statement": "Q3 has 21 expense records", "predicate": "value",
                  "expected": 21.0, "tolerance": 0.0,
                  "both_sides": {"Q3": {"derivation": "count(amount) where period='Q3'"},
                                 "ref": {"derivation": "count(amount) where period='Q3'"}}},
    "provenance": {"created_by": "experiment-freeze", "created_at": "2026-10-19T00:00Z"},
    "check": {"provenance": "PENDING", "semantic": "PENDING"}})

view = {"spec": "dvr/1.0", "id": "v_exp", "kind": "table",
        "title": {"text": "2026 expenses"},
        "columns": [{"id": "col:amount", "label": "Amount", "source_field": "amount"}],
        "nodes": [
            {"id": "cell:total_q1", "role": "value", "binding_ref": "b_tot_q1", "column": "col:amount"},
            {"id": "cell:total_q2", "role": "value", "binding_ref": "b_tot_q2", "column": "col:amount"},
            {"id": "cell:total_q3", "role": "value", "binding_ref": "b_tot_q3", "column": "col:amount"},
            {"id": "cell:r_042", "role": "value", "binding_ref": "b_cell_r42",
             "column": "col:amount", "row_key": records[50]["id"], "editable": True},
            {"id": "claim:trend", "role": "claim", "binding_ref": "b_trend"},
            {"id": "claim:count", "role": "claim", "binding_ref": "b_count"},
            {"id": "lbl", "role": "label", "text": "Every figure is bound to frozen data."},
        ]}

# --- frozen edit script for E2: 100 random edits to random records ---
rng = random.Random(20261019)
edit_script = [{"seq": k, "record_id": rng.choice(records)["id"],
                "value": round(rng.uniform(10, 1000), 2)} for k in range(100)]

# --- write corpus ---
ds = CORPUS / "datasets" / "expenses"
ds.mkdir(parents=True, exist_ok=True)
def dump(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n")
(ds / "schema.json").write_text(json.dumps(schema, indent=2) + "\n")
(ds / "data.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
(CORPUS / "bindings.jsonl").write_text("".join(json.dumps(b) + "\n" for b in bindings))
dump(CORPUS / "views" / "v_exp.view.json", view)
dump(CORPUS / "edit_script.json", {"seed": 20261019, "edits": edit_script})

# manifest with hashes — the freeze receipt
files = ["datasets/expenses/schema.json", "datasets/expenses/data.jsonl",
         "bindings.jsonl", "views/v_exp.view.json", "edit_script.json"]
manifest = {"frozen_at": "2026-10-19", "files": {}}
for f in files:
    manifest["files"][f] = hashlib.sha256((CORPUS / f).read_bytes()).hexdigest()
dump(CORPUS / "manifest.json", manifest)
print(f"frozen: {len(records)} records, {len(bindings)} bindings, {len(edit_script)} scripted edits")
print(f"Q2={q2} Q3={q3} trend={trend:+.2%}")
for f, h in manifest["files"].items():
    print(f"  {h[:12]}  {f}")
