#!/usr/bin/env python3
"""Build demo.html — the Layer-2 view as it appears in the AI OS.
Replays the E1 scenario on the frozen corpus: PASS baseline -> user edit ->
PENDING (stale, visible) -> recheck -> FLAG with live ▸evidence panels."""
import json, shutil, sys, tempfile
from pathlib import Path

EXP = Path(__file__).resolve().parent
L2 = EXP.parent
sys.path.insert(0, str(L2 / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(L2 / "view-renderer"))

from dvr import specval, render, edits, affordance, resolve
from qafiya_core import engine, semantic, store

CORPUS = EXP / "corpus"

root = Path(tempfile.mkdtemp())
shutil.copytree(CORPUS / "datasets", root / "datasets")
shutil.copy2(CORPUS / "bindings.jsonl", root / "bindings.jsonl")
view = specval.validate_view(json.loads((CORPUS / "views" / "v_exp.view.json").read_text()))

engine.refresh_values(root)
engine.provenance_gate(root)
semantic.semantic_sweep(root)
html_pass = render.render(root, view)

node = [n for n in view["nodes"] if n.get("editable")][0]
_, recs = store.load_dataset(root, "expenses")
prior = [r for r in recs if r["id"] == node["row_key"]][0]["amount"]
new_value = round(prior + 500.0, 2)
edits.apply(root, edits.make_edit_binding(root, "v_exp", node, new_value))
html_pending = render.render(root, view)

engine.refresh_values(root)
engine.provenance_gate(root)
semantic.semantic_sweep(root)
html_flag = render.render(root, view)

bindings = resolve.load_bindings(root)
evidence = {bid: affordance.evidence_panel(root, b) for bid, b in bindings.items()}

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>DeeWaanAI OS — Layer 2 view demo</title>
<style>
body{font-family:-apple-system,Georgia,serif;background:#0f1115;color:#e8e8ea;max-width:860px;margin:40px auto;padding:0 20px}
h1{font-size:22px} h2{font-size:16px;color:#9aa}
.state{margin:28px 0;padding:18px;border:1px solid #2a2f3a;border-radius:12px;background:#171a21}
.view h2{color:#e8e8ea;font-size:15px;margin:0 0 10px}
.node{padding:8px 10px;margin:4px 0;border-radius:8px;background:#1e222c;font-size:15px}
.badge{float:right;font-size:12px;padding:2px 8px;border-radius:10px}
.badge-pass{background:#12381f;color:#4ade80}.badge-flag{background:#3d2b10;color:#fbbf24}
.badge-pending{background:#2a2f3a;color:#9ca3af}.badge-fail{background:#3d1414;color:#f87171}
.badge-unresolved{background:#3d1414;color:#f87171}
.coverage{margin-top:10px;font-size:12px;color:#8ab4f8}
button.evidence{background:#25406e;color:#bcd3ff;border:0;border-radius:8px;padding:2px 8px;cursor:pointer;font-size:12px}
.editable{color:#8ab4f8;cursor:pointer}
.ev{background:#10141b;border-left:3px solid #25406e;padding:10px 14px;margin-top:6px;font-size:13px;display:none;white-space:pre-wrap}
.caption{font-size:13px;color:#9aa;margin-bottom:8px}
</style></head><body>
<h1>DeeWaanAI OS — a view that proves itself <span style="color:#8ab4f8">(Layer 2, live on the frozen experiment corpus)</span></h1>

<div class="state"><div class="caption">1 · Initial view — everything checks out</div>__PASS__</div>

<div class="state"><div class="caption">2 · You edit expense r_051: __PRIOR__ → __NEW__. The edit writes back to the data file; dependent claims go stale — <b>visibly</b>, never silently</div>__PENDING__</div>

<div class="state"><div class="caption">3 · Re-check: numbers re-prove ✓, but the trend claim no longer matches reality — <b>FLAG</b>. Click ▸evidence on the claim to see the binding, the source rows, and the check</div>__FLAG__</div>

<script>
const EV = __EVIDENCE__;
document.querySelectorAll("button.evidence").forEach(btn=>{
  btn.addEventListener("click",()=>{
    let p=btn.parentElement.querySelector(".ev");
    if(!p){p=document.createElement("div");p.className="ev";btn.parentElement.appendChild(p);}
    if(p.style.display==="block"){p.style.display="none";return;}
    const e=EV[btn.dataset.binding];if(!e){p.textContent="no evidence";return;}
    let txt="";
    const f=e.focus;
    if(f&&(f.correct_value!==null||f.changed_records.length)){
      txt+="━━ what matters ━━\\n";
      if(f.claim_says)txt+="claim says: "+f.claim_says+" (expected "+(f.expected*100).toFixed(1)+"%)\\n";
      if(f.correct_value!==null)txt+="data says:  "+(f.correct_value*100).toFixed(1)+"%  ← the correct value\\n";
      for(const[k,s]of Object.entries(f.sides||{}))
        txt+="  "+k+" total = "+s.value+"  ("+s.rows.length+" rows)\\n";
      for(const c of f.changed_records)
        txt+="changed: record "+c.record_id+" · "+c.field+" "+c.prior+" → "+c.new+"\\n";
      txt+="\\n";
    }
    txt+="binding: "+e.binding_id+"  ("+e.kind+")\\nderivation: "+e.derivation
      +"\\nartifact: "+(e.tuple.authoritative_artifact||"")
      +"\\ncheck: provenance="+e.check.provenance+(e.check.semantic?" semantic="+e.check.semantic:"")
      +(e.check.detail?"\\ndetail: "+e.check.detail:"");
    if(f&&Object.keys(f.sides||{}).length){
      for(const[k,s]of Object.entries(f.sides)){
        txt+="\\n\\n"+k+" deciding rows ("+s.rows.length+"):";
        txt+=s.rows.slice(0,6).map(r=>"\\n  "+JSON.stringify(r)).join("")+(s.rows.length>6?"\\n  …":"");
      }
    } else {
      const rows=e.source_rows.slice(0,6).map(r=>"\\n  "+JSON.stringify(r)).join("");
      txt+="\\n\\nsource rows ("+e.source_rows.length+"):"+rows+(e.source_rows.length>6?"\\n  …":"");
    }
    p.textContent=txt;
    p.style.display="block";
  });
});
</script></body></html>"""

page = (PAGE.replace("__PASS__", html_pass).replace("__PENDING__", html_pending)
            .replace("__FLAG__", html_flag).replace("__PRIOR__", str(prior))
            .replace("__NEW__", str(new_value))
            .replace("__EVIDENCE__", json.dumps(evidence)))
out = EXP / "demo.html"
out.write_text(page)
print(out)
