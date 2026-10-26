#!/usr/bin/env python3
"""L6 expressiveness probe (revision instruction 5): can dvr/1.0 express the six
shell-relevant view requests? For each request we write the dvr/1.0 spec we would
emit and run the real validator. Expressible = validates AND renders with the
prototype. Not expressible = requires elements the grammar does not have; the gap
is named honestly. Corpus frozen in l6_requests/; results to results/raw/l6.json."""
import json, shutil, sys, tempfile
from pathlib import Path

EXP = Path(__file__).resolve().parent
L2 = EXP.parent
sys.path.insert(0, str(L2 / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(L2 / "view-renderer"))

from dvr import specval, render

CORPUS = EXP / "corpus"
REQ = EXP / "l6_requests"
REQ.mkdir(exist_ok=True)

# dvr/1.0 attempts for the six shell-relevant requests
ATTEMPTS = {
 "prompt_answer": {
   "spec": "dvr/1.0", "id": "v_pa", "kind": "list",
   "title": {"text": "Q&A"},
   "nodes": [
     {"id": "q", "role": "label", "text": "How much did we spend in Q3?"},
     {"id": "a", "role": "claim", "binding_ref": "b_trend"}]},
 "data_table": {
   "spec": "dvr/1.0", "id": "v_dt", "kind": "table",
   "columns": [{"id": "col:amount", "label": "Amount", "source_field": "amount"}],
   "nodes": [{"id": "cell:total_q3", "role": "value", "binding_ref": "b_tot_q3",
              "column": "col:amount"}]},
 "claim_with_evidence": {
   "spec": "dvr/1.0", "id": "v_ce", "kind": "list",
   "nodes": [{"id": "claim:trend", "role": "claim", "binding_ref": "b_trend"}]},
 "action_confirmation": None,   # needs action/approve-reject elements: Layer 3, not dvr/1.0
 "memory_inspection": {
   "spec": "dvr/1.0", "id": "v_mem", "kind": "tree",
   "nodes": [
     {"id": "root", "role": "structure", "text": "sessions"},
     {"id": "s1", "role": "value", "binding_ref": "b_tot_q3", "path": "root"}]},
 "connection_manager": None,    # needs live status controls/indicators: not a data view
}

GAP_REASON = {
 "action_confirmation": "requires an action element (approve/reject buttons emitting "
                        "effects, not data edits) — Layer 3 territory; dvr/1.0 renders "
                        "data, it does not act",
 "connection_manager": "requires live status indicators and controls (connect, retry) "
                       "bound to service state, not to dataset bindings",
}

def main():
    root = Path(tempfile.mkdtemp())
    shutil.copytree(CORPUS / "datasets", root / "datasets")
    shutil.copy2(CORPUS / "bindings.jsonl", root / "bindings.jsonl")

    results = {}
    for name, spec in ATTEMPTS.items():
        (REQ / f"{name}.json").write_text(json.dumps(
            {"request": name, "dvr_spec": spec}, indent=2) + "\n")
        if spec is None:
            results[name] = {"expressible": False, "gap": GAP_REASON[name]}
            continue
        try:
            specval.validate_view(spec)
            out = render.render(root, spec)
            results[name] = {"expressible": True, "html_bytes": len(out)}
        except Exception as e:
            results[name] = {"expressible": False,
                             "gap": f"validator/renderer rejected: {e}"}

    n_ok = sum(1 for r in results.values() if r["expressible"])
    summary = {"requests": len(results), "expressible": n_ok,
               "rate": round(n_ok / len(results), 4), "per_request": results,
               "note": "gaps are Layer-3 action elements and live service controls; "
                       "both are out of dvr/1.0 scope by design (spec §8 non-goals)"}
    out = EXP / "results" / "raw"
    out.mkdir(parents=True, exist_ok=True)
    (out / "l6.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
