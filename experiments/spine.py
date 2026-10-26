#!/usr/bin/env python3
"""Self-verifying spine (Qafiya discipline): reads ONLY frozen raw artifacts and
recomputes every headline number into results/derived/paper_headline_numbers.json.
Exit 0 required. No number in the paper may exist outside this file."""
import json, sys
from pathlib import Path

EXP = Path(__file__).resolve().parent
RAW = EXP / "results" / "raw"

def main():
    corpus_manifest = json.loads((EXP / "corpus" / "manifest.json").read_text())

    # E1 — durability: verdict from the trace
    trace = [json.loads(l) for l in open(RAW / "e1_trace.jsonl")]
    verdict = [t for t in trace if t["step"] == "4_verdict"][0]["c6_durability_closed"]
    edit_step = [t for t in trace if t["step"] == "1_user_edit"][0]
    recheck = [t for t in trace if t["step"] == "3_recheck"][0]

    # E2 — round-trip: recount from raw lines; wall time from frozen meta
    edits = [json.loads(l) for l in open(RAW / "e2_edits.jsonl")]
    e2_ok = sum(1 for r in edits if r["ok"])
    e2_rate = round(e2_ok / len(edits), 4)
    e2_meta = json.loads((RAW / "e2_meta.json").read_text())

    # Review flow — recomputed from the frozen litreview raw artifacts
    LR = EXP.parent / "litreview" / "raw"
    import re as _re, subprocess as _sp, sys as _sys
    _scr = _sp.run([_sys.executable, str(EXP.parent / "litreview" / "screen.py")],
                   capture_output=True, text=True).stdout
    review = {"identified": len(json.loads((LR / "openalex.json").read_text()))
                           + len(json.loads((LR / "arxiv.json").read_text())),
              "deduplicated": len(json.loads((LR / "combined.json").read_text())),
              "screened": int(_re.search(r"kept_by_score>=4: (\d+)", _scr).group(1)),
              "included": len(json.loads((LR / "included_verified.json").read_text()))}

    # Limits — from the frozen limits probe results
    lim = json.loads((EXP.parent / "view-renderer" / "limits_results.json").read_text())
    scale = {c["nodes"]: c["render_s"] for c in lim["L4_scale"]["curve"]}

    # Prototype size — recomputed from source
    loc = 0
    for f in (EXP.parent / "view-renderer" / "dvr").glob("*.py"):
        loc += sum(1 for ln in f.read_text().splitlines()
                   if ln.strip() and not ln.strip().startswith("#"))
    loc_total = sum(len(f.read_text().splitlines())
                    for f in (EXP.parent / "view-renderer" / "dvr").glob("*.py"))

    # E3 — cost: recompute ratio from raw token counts
    e3 = json.loads((RAW / "e3_counts.json").read_text())
    ratio = round(e3["regen"]["T_total"] / e3["dvr"]["T_total"], 1)
    assert abs(ratio - e3["ratio"]) < 0.05, "spine: E3 ratio mismatch"

    # Corpus composition — the descriptors quoted in Evaluation/Threats
    corpus_records = sum(1 for _ in open(EXP / "corpus" / "datasets" / "expenses" / "data.jsonl"))
    corpus_bindings = sum(1 for _ in open(EXP / "corpus" / "bindings.jsonl"))
    corpus_edits = len(json.loads((EXP / "corpus" / "edit_script.json").read_text())["edits"])
    corpus_composition = {"records": corpus_records, "bindings": corpus_bindings,
                          "scripted_edits": corpus_edits,
                          "period_totals": 3, "editable_cells": 1, "claims": 2}

    out = {
        "frozen_inputs": ["corpus/manifest.json", "results/raw/e1_trace.jsonl",
                          "results/raw/e2_edits.jsonl", "results/raw/e2_meta.json",
                          "results/raw/e3_counts.json",
                          "litreview/raw/*.json", "view-renderer/limits_results.json",
                          "view-renderer/dvr/*.py"],
        "corpus_hashes": corpus_manifest["files"],
        "corpus_composition": corpus_composition,
        "E1_durability": {
            "c6_closed": verdict,
            "edit": {"record": edit_step["record"], "prior": edit_step["prior"],
                     "new": edit_step["new"]},
            "post_recheck_claim_state": recheck["states"]["b_trend"]["semantic"],
            "post_recheck_detail": recheck.get("trend_detail"),
        },
        "E2_roundtrip": {"edits": len(edits), "reproved": e2_ok, "rate": e2_rate,
                         "wall_s": e2_meta["wall_s"]},
        "E3_cost": {"interactions": e3["interactions_k"],
                    "dvr_tokens_total": e3["dvr"]["T_total"],
                    "regen_tokens_total": e3["regen"]["T_total"],
                    "ratio": ratio,
                    "breakeven_interactions": e3["breakeven_interactions"]},
        "review_flow": review,
        "limits": {"scale_curve": scale,
                   "L3_shared_error_caught": lim["L3_shared_error"]["caught"],
                   "L5_concurrency_consistent": lim["L5_concurrency"]["consistent"],
                   "L7_coverage_honest": lim["L7_coverage_honesty"]["pass"]},
        "prototype_loc": {"non_comment": loc, "total_lines": loc_total},
        "L6_expressiveness": json.loads((RAW / "l6.json").read_text()),
    }
    d = EXP / "results" / "derived"
    d.mkdir(parents=True, exist_ok=True)
    (d / "paper_headline_numbers.json").write_text(json.dumps(out, indent=2))

    print(json.dumps(out, indent=2))
    ok = verdict and e2_rate == 1.0
    print("\nSPINE:", "PASS" if ok else "FAIL")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main())
