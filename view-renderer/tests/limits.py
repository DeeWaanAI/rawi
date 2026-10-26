#!/usr/bin/env python3
"""Tier B limits probes (brief §5) — L1-L5 + L7. Each result printed; negative
results are results. Run: python limits.py  (writes limits_results.json)"""
import json, random, sys, tempfile, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(ROOT))

from dvr import specval, resolve, render, edits
from qafiya_core import engine, semantic, store
from tests.test_renderer import make_workspace, VIEW, RECORDS

results = {}

# ---- L1: round-trip correctness — N random valid edits, re-prove at Layer 1 ----
random.seed(20261019)
N = 100
root = make_workspace()
node = VIEW["nodes"][1]
fails = 0
for i in range(N):
    v = round(random.uniform(1, 9000), 2)
    edits.apply(root, edits.make_edit_binding(root, "v_q3", node, v))
    engine.refresh_values(root)
    if engine.provenance_gate(root) != 0:
        fails += 1
results["L1_round_trip"] = {"edits": N, "gate_failures": fails,
                            "pass": fails == 0}

# ---- L2: stale-detection honesty — edit data behind the renderer's back ----
root = make_workspace()
html_before = render.render(root, VIEW)
ds, records = store.load_dataset(root, "expenses")
records[1]["amount"] = 1.0  # sneaky direct edit, no binding
store.atomic_write_jsonl(ds / store.DATA, records)
engine.provenance_gate(root)  # standing check runs
html_after = render.render(root, VIEW)
results["L2_stale_honesty"] = {
    "silent_green": ('data-state="PASS"' in html_after and html_after == html_before),
    "fail_shown": 'data-state="FAIL"' in html_after,
}
results["L2_stale_honesty"]["pass"] = results["L2_stale_honesty"]["fail_shown"]

# ---- L3: shared-error blindness (provable limit — expected NOT to catch) ----
root = make_workspace()
# Fabricate data so it AGREES with a claim that is false in the world:
# set Q2 so that Q3=4210 is exactly -12% (the claim) — internally consistent,
# externally wrong (true Q2 was 4800). Qafiya provable limit 1.
ds, records = store.load_dataset(root, "expenses")
records[0]["amount"] = round(4210.0 / 0.88, 2)  # 4784.09 -> actual change == -12.00%
store.atomic_write_jsonl(ds / store.DATA, records)
engine.refresh_values(root)
gate = engine.provenance_gate(root)
flags = semantic.semantic_sweep(root)
results["L3_shared_error"] = {
    "note": "claim and data share the error -> agreement looks like verification; "
            "remedy is an upstream second anchor (cost, not software)",
    "gate_exit": gate, "semantic_flags": flags,
    "caught": flags > 0 or gate != 0,
    "pass": True,  # the LIMIT is the finding: the system provably cannot catch this
}

# ---- L4: scale ceiling — render time vs node/binding count ----
scale = []
for n in (10, 100, 1000, 10000):
    root = make_workspace()
    recs = [{"id": f"r_{i:05d}", "period": "Q3", "amount": float(i)} for i in range(n)]
    ds = root / "datasets" / "expenses"
    store.atomic_write_jsonl(ds / store.DATA, recs)
    bindings = store.read_jsonl(root / store.BINDINGS)
    for i in range(n):
        bindings.append({"id": f"b_s{i}", "kind": "view",
                         "target": {"view": "v_big", "node": f"n{i}"},
                         "sources": [{"dataset": "ds:expenses", "field": "amount",
                                      "key_path": ["amount"], "verbatim_excerpt": str(i)}],
                         "derivation": "sum(amount) where period='Q3'", "value": 0.0,
                         "statistic": "sum", "device": "test",
                         "authoritative_artifact": "datasets/expenses/data.jsonl",
                         "check": {"provenance": "PASS"}})
    store.atomic_write_jsonl(root / store.BINDINGS, bindings)
    view = {"spec": "dvr/1.0", "id": "v_big", "kind": "list",
            "nodes": [{"id": f"n{i}", "role": "value", "binding_ref": f"b_s{i}"} for i in range(n)]}
    specval.validate_view(view)
    t0 = time.perf_counter()
    out = render.render(root, view)
    dt = time.perf_counter() - t0
    scale.append({"nodes": n, "render_s": round(dt, 3), "html_kb": len(out) // 1024})
results["L4_scale"] = {"curve": scale,
                       "note": "O(nodes x records) per node — linear-in-n^2 at worst; "
                               "usability ceiling where render_s > 1s interactive threshold"}

# ---- L5: concurrency — two edits to the same record ----
root = make_workspace()
node = VIEW["nodes"][1]
import threading
errs = []
def do_edit(v):
    try:
        edits.apply(root, edits.make_edit_binding(root, "v_q3", node, v))
    except Exception as e:
        errs.append(str(e))
t1 = threading.Thread(target=do_edit, args=(1111.0,))
t2 = threading.Thread(target=do_edit, args=(2222.0,))
t1.start(); t2.start(); t1.join(); t2.join()
_, recs = store.load_dataset(root, "expenses")
final = [r for r in recs if r["id"] == "r_012"][0]["amount"]
hist = store.read_jsonl(root / "datasets" / "expenses" / store.HISTORY)
results["L5_concurrency"] = {
    "errors": errs, "final_value": final,
    "history_entries": len(hist),
    "note": "last-writer-wins; both edits landed in history; atomic rename prevents torn file",
    "consistent": final in (1111.0, 2222.0) and len(hist) == 2 and not errs,
}

# ---- L7: coverage honesty ----
root = make_workspace()
bindings = store.read_jsonl(root / store.BINDINGS)
bindings[0]["derivation"] = "sum(amount) where period='Q9'"  # one unresolvable
bindings[2]["derivation"] = "sum(amount) where period='Q9'"  # two unresolvable
store.atomic_write_jsonl(root / store.BINDINGS, bindings)
out = render.render(root, VIEW)
results["L7_coverage_honesty"] = {
    "coverage_shown": "coverage: 33%" in out,
    "unresolved_shown": "unresolved" in out,
    "pass": "coverage: 33%" in out and "unresolved" in out,
}

print(json.dumps(results, indent=2))
(ROOT / "limits_results.json").write_text(json.dumps(results, indent=2))
