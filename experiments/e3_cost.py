#!/usr/bin/env python3
"""E3 — rendering cost: spec-once (DVR) vs per-keystroke prompting (generative UI).
Token evidence with the ACTUAL Qwen2.5 tokenizer (same as the Qafiya efficiency
experiment — cross-paper comparable). Offline, deterministic, disclosed method:

  Arm DVR (ours):  model emits spec+bindings ONCE (T_spec); all K interactions
                   (render, edit, re-check) are local -> 0 further model tokens.
  Arm REGEN:       every interaction re-prompts the model with the dataset and
                   regenerates the full UI -> K x (T_in + T_out) tokens.
                   T_out estimated by generating a self-contained HTML table
                   from the corpus data (a faithful stand-in for generative-UI
                   output, disclosed as an estimate, not an API measurement).

Interaction script: the frozen 100-edit script (edit_script.json) => K=100.
Writes results/raw/e3_counts.json (the frozen evidence artifact)."""
import json, sys
from pathlib import Path
from tokenizers import Tokenizer

EXP = Path(__file__).resolve().parent
TOK = Tokenizer.from_file(str(EXP / "e3_cost" / "tokenizer" / "qwen25_tokenizer.json"))
CORPUS = EXP / "corpus"
OUT = EXP / "results" / "raw"
OUT.mkdir(parents=True, exist_ok=True)

def ntok(s: str) -> int:
    return len(TOK.encode(s).ids)

def regen_html(records) -> str:
    rows = "".join(f"<tr><td>{r['id']}</td><td>{r['date']}</td><td>{r['period']}</td>"
                   f"<td>{r['amount']}</td><td>{r['category']}</td></tr>" for r in records)
    return ("<table><thead><tr><th>id</th><th>date</th><th>period</th>"
            f"<th>amount</th><th>category</th></tr></thead><tbody>{rows}</tbody></table>")

def main():
    records = [json.loads(l) for l in open(CORPUS / "datasets" / "expenses" / "data.jsonl")]
    view = (CORPUS / "views" / "v_exp.view.json").read_text()
    bindings = (CORPUS / "bindings.jsonl").read_text()
    data_slim = (CORPUS / "datasets" / "expenses" / "data.jsonl").read_text()
    k = len(json.loads((CORPUS / "edit_script.json").read_text())["edits"])

    # Arm DVR: one emission = system-ish prompt + dataset + spec + bindings out
    prompt_tpl = "Render an interactive view over this dataset. Data:\n{DATA}\n"
    t_dvr_in = ntok(prompt_tpl.replace("{DATA}", data_slim))
    t_spec_out = ntok(view + bindings)
    t_dvr_total = t_dvr_in + t_spec_out  # once; interactions cost 0 model tokens

    # Arm REGEN: per interaction, dataset in + full UI out
    t_regen_in = ntok(prompt_tpl.replace("{DATA}", data_slim))
    t_regen_out = ntok(regen_html(records))
    t_regen_total = k * (t_regen_in + t_regen_out)

    out = {
        "tokenizer": "Qwen/Qwen2.5-7B-Instruct tokenizer.json",
        "method": "offline deterministic count; REGEN output estimated by a faithful "
                  "HTML stand-in, disclosed as estimate; no live API calls",
        "interactions_k": k,
        "dvr": {"T_in_once": t_dvr_in, "T_spec_once": t_spec_out, "T_total": t_dvr_total,
                "T_per_interaction": 0},
        "regen": {"T_in_per": t_regen_in, "T_out_per": t_regen_out,
                  "T_per_interaction": t_regen_in + t_regen_out, "T_total": t_regen_total},
        "ratio": round(t_regen_total / t_dvr_total, 1),
        "breakeven_interactions": round(t_dvr_total / (t_regen_in + t_regen_out), 2),
    }
    (OUT / "e3_counts.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0

if __name__ == "__main__":
    sys.exit(main())
