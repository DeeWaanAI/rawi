#!/usr/bin/env python3
"""E2 — round-trip correctness: the 100 frozen scripted edits are applied
through the view one by one; after each edit the Layer-1 gate must re-prove.
Writes results/raw/e2_edits.jsonl (one line per edit)."""
import json, shutil, sys, tempfile, time
from pathlib import Path

EXP = Path(__file__).resolve().parent
L2 = EXP.parent
sys.path.insert(0, str(L2 / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(L2 / "view-renderer"))

from dvr import edits
from qafiya_core import engine, store

CORPUS = EXP / "corpus"
OUT = EXP / "results" / "raw"

def main():
    root = Path(tempfile.mkdtemp())
    shutil.copytree(CORPUS / "datasets", root / "datasets")
    shutil.copy2(CORPUS / "bindings.jsonl", root / "bindings.jsonl")
    script = json.loads((CORPUS / "edit_script.json").read_text())["edits"]

    rows = []
    t0 = time.perf_counter()
    for e in script:
        eb = {"id": f"b_e2_{e['seq']:03d}", "kind": "edit",
              "target": {"view": "v_exp", "node": "cell:direct"},
              "sources": [],
              "writeback": {"dataset": "ds:expenses", "record_id": e["record_id"],
                            "field": "amount", "op": "set", "value": e["value"]},
              "provenance": {"created_by": "e2-script", "created_at": "2026-10-19T00:00Z"}}
        edits.apply(root, eb)
        engine.refresh_values(root)
        gate = engine.provenance_gate(root)
        _, recs = store.load_dataset(root, "expenses")
        actual = [r for r in recs if r["id"] == e["record_id"]][0]["amount"]
        rows.append({"seq": e["seq"], "record_id": e["record_id"], "value": e["value"],
                     "file_value": actual, "gate_exit": gate,
                     "ok": gate == 0 and actual == e["value"]})
    dt = time.perf_counter() - t0
    with open(OUT / "e2_edits.jsonl", "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    (OUT / "e2_meta.json").write_text(json.dumps(
        {"edits": len(rows), "ok": sum(r["ok"] for r in rows),
         "wall_s": round(dt, 2)}, indent=2))
    ok = sum(r["ok"] for r in rows)
    print(f"E2: {ok}/{len(rows)} edits re-proved at Layer 1 ({dt:.1f}s)")
    return 0 if ok == len(rows) else 1

if __name__ == "__main__":
    sys.exit(main())
