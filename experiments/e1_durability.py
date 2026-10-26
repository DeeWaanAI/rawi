#!/usr/bin/env python3
"""E1 — C6 durability end-to-end (closes the Qafiya paper's open claim).

Scripted as a real user-driven edit: render -> user edits cell r_042 ->
file write -> transitive invalidation -> visible flag -> re-check -> final state.
Every step logged with before/after HTML states and hashes.
Reads ONLY the frozen corpus (copies it to a scratch root; corpus untouched).
Writes results/raw/e1_trace.jsonl."""
import json, shutil, sys, tempfile
from pathlib import Path

EXP = Path(__file__).resolve().parent
L2 = EXP.parent
sys.path.insert(0, str(L2 / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(L2 / "view-renderer"))

from dvr import specval, render, edits, resolve
from qafiya_core import engine, semantic, store

CORPUS = EXP / "corpus"
OUT = EXP / "results" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

def snapshot(root, view):
    html = render.render(root, view)
    bindings = resolve.load_bindings(root)
    states = {bid: dict(b.get("check") or {}) for bid, b in bindings.items()}
    return html, states

def main():
    root = Path(tempfile.mkdtemp())
    shutil.copytree(CORPUS / "datasets", root / "datasets")
    shutil.copy2(CORPUS / "bindings.jsonl", root / "bindings.jsonl")
    view = specval.validate_view(json.loads((CORPUS / "views" / "v_exp.view.json").read_text()))
    trace = []

    def step(name, **kw):
        trace.append({"step": name, **kw})

    # 0. initial checks establish the green baseline
    engine.refresh_values(root)
    gate0 = engine.provenance_gate(root)
    sem0 = semantic.semantic_sweep(root)
    html0, states0 = snapshot(root, view)
    step("0_baseline", gate_exit=gate0, semantic_flags=sem0,
         states={k: v.get("provenance") for k, v in states0.items()},
         html=html0)

    # 1. user edits the editable cell (record r_042 -> new amount)
    node = [n for n in view["nodes"] if n.get("editable")][0]
    target_record = node["row_key"]
    _, before_recs = store.load_dataset(root, "expenses")
    prior = [r for r in before_recs if r["id"] == target_record][0]["amount"]
    new_value = round(prior + 500.0, 2)  # a real, user-sized correction
    eb = edits.make_edit_binding(root, "v_exp", node, new_value)
    step("1_user_edit", edit_binding=eb["id"], record=target_record,
         prior=prior, new=new_value)

    # 2. write-back applied atomically; invalidation fires
    updated, n_inv = edits.apply(root, eb)
    _, after_recs = store.load_dataset(root, "expenses")
    file_value = [r for r in after_recs if r["id"] == target_record][0]["amount"]
    hist = store.read_jsonl(root / "datasets" / "expenses" / store.HISTORY)
    html1, states1 = snapshot(root, view)
    step("2_writeback_invalidation", file_value=file_value, history_entry=hist[-1],
         invalidated=n_inv, html_after_edit=html1,
         states={k: v.get("provenance") for k, v in states1.items()})

    # 3. re-render (refresh) + re-check: what does the claim say now?
    engine.refresh_values(root)
    gate1 = engine.provenance_gate(root)
    flags1 = semantic.semantic_sweep(root)
    html2, states2 = snapshot(root, view)
    claim = resolve.load_bindings(root)["b_trend"]
    step("3_recheck", gate_exit=gate1, semantic_flags=flags1,
         trend_claim=claim["assertion"]["statement"],
         trend_detail=claim["check"].get("detail"),
         states={k: dict(v) for k, v in states2.items()}, html_final=html2)

    # 4. durability verdict: the whole chain landed
    verdict = (gate0 == 0 and file_value == new_value and n_inv >= 4
               and states1["b_trend"].get("provenance") == "PENDING"
               and gate1 == 0)
    step("4_verdict", c6_durability_closed=bool(verdict))

    with open(OUT / "e1_trace.jsonl", "w") as f:
        for t in trace:
            f.write(json.dumps(t) + "\n")
    print(f"E1 verdict: C6 durability {'CLOSED' if verdict else 'FAILED'}")
    print(f"  edit r_042: {prior} -> {new_value}; invalidated={n_inv}; "
          f"trend claim now: {claim['check'].get('semantic')} ({claim['check'].get('detail')})")
    return 0 if verdict else 1

if __name__ == "__main__":
    sys.exit(main())
