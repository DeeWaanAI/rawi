#!/usr/bin/env python3
"""Build the E4 one-click usability session (e4_session.html).
Renders the three seeded states from the frozen corpus with the real prototype,
embeds them in a task runner: consent -> 5 timed tasks -> interview -> export JSON.
Participant opens the file; researcher collects the exported JSON into
experiments/results/raw/e4/<participant>.json."""
import json, shutil, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
L2 = EXP.parent
sys.path.insert(0, str(L2 / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(L2 / "view-renderer"))

from dvr import specval, render, edits, affordance, resolve
from qafiya_core import engine, semantic, store

CORPUS = EXP / "corpus"

def fresh_root():
    root = Path(tempfile.mkdtemp())
    shutil.copytree(CORPUS / "datasets", root / "datasets")
    shutil.copy2(CORPUS / "bindings.jsonl", root / "bindings.jsonl")
    return root

view = specval.validate_view(json.loads((CORPUS / "views" / "v_exp.view.json").read_text()))

# State 1: all PASS (T1)
r1 = fresh_root()
engine.refresh_values(r1); engine.provenance_gate(r1); semantic.semantic_sweep(r1)
html_pass = render.render(r1, view)
ev_pass = {k: affordance.evidence_panel(r1, b) for k, b in resolve.load_bindings(r1).items()}

# State 2: FLAG (T2) — edit r_051 +500 then re-check
r2 = fresh_root()
engine.refresh_values(r2); engine.provenance_gate(r2); semantic.semantic_sweep(r2)
node = [n for n in view["nodes"] if n.get("editable")][0]
_, recs = store.load_dataset(r2, "expenses")
prior = [r for r in recs if r["id"] == node["row_key"]][0]["amount"]
edits.apply(r2, edits.make_edit_binding(r2, "v_exp", node, round(prior + 500, 2)))
engine.refresh_values(r2); engine.provenance_gate(r2); semantic.semantic_sweep(r2)
html_flag = render.render(r2, view)
ev_flag = {k: affordance.evidence_panel(r2, b) for k, b in resolve.load_bindings(r2).items()}

# State 3: PENDING (T3) — behind-the-back edit, no re-check yet
r3 = fresh_root()
engine.refresh_values(r3); engine.provenance_gate(r3); semantic.semantic_sweep(r3)
ds, recs3 = store.load_dataset(r3, "expenses")
recs3[50]["amount"] = round(recs3[50]["amount"] + 500, 2)
store.atomic_write_jsonl(ds / store.DATA, recs3)
# mark dependents PENDING without recompute (what the user would see mid-edit)
binds = {b["id"]: b for b in store.read_jsonl(r3 / store.BINDINGS)}
for bid in ("b_tot_q3", "b_cell_r42", "b_trend", "b_count"):
    binds[bid]["check"]["provenance"] = "PENDING"
    if binds[bid].get("kind") == "claim":
        binds[bid]["check"]["semantic"] = "PENDING"
store.atomic_write_jsonl(r3 / store.BINDINGS, list(binds.values()))
html_pending = render.render(r3, view)
ev_pending = {k: affordance.evidence_panel(r3, b) for k, b in resolve.load_bindings(r3).items()}

# State 4: low coverage (T5) — break two of six bindings
r4 = fresh_root()
binds4 = store.read_jsonl(r4 / store.BINDINGS)
for b in binds4:
    if b["id"] in ("b_tot_q1", "b_cell_r42"):
        b["derivation"] = "sum(amount) where period='Q9'"
        b["check"] = {"provenance": "FAIL"}
store.atomic_write_jsonl(r4 / store.BINDINGS, binds4)
html_lowcov = render.render(r4, view)

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Rawi usability session</title>
<style>
body{font-family:-apple-system,Georgia,serif;background:#0f1115;color:#e8e8ea;max-width:880px;margin:30px auto;padding:0 20px}
h1{font-size:20px} .task{display:none} .task.on{display:block}
.q{font-size:16px;margin:14px 0 6px;color:#bcd3ff}
textarea{width:100%;min-height:70px;background:#10141b;color:#e8e8ea;border:1px solid #2a2f3a;border-radius:8px;padding:8px;font-size:14px}
button.next{background:#25406e;color:#fff;border:0;border-radius:8px;padding:10px 22px;font-size:15px;cursor:pointer;margin-top:14px}
.view h2{font-size:15px;color:#e8e8ea;margin:0 0 10px}
.node{padding:8px 10px;margin:4px 0;border-radius:8px;background:#1e222c;font-size:15px}
.badge{float:right;font-size:12px;padding:2px 8px;border-radius:10px}
.badge-pass{background:#12381f;color:#4ade80}.badge-flag{background:#3d2b10;color:#fbbf24}
.badge-pending{background:#2a2f3a;color:#9ca3af}.badge-fail{background:#3d1414;color:#f87171}
.badge-unresolved{background:#3d1414;color:#f87171}
.coverage{margin-top:10px;font-size:12px;color:#8ab4f8}
button.evidence{background:#25406e;color:#bcd3ff;border:0;border-radius:8px;padding:2px 8px;cursor:pointer;font-size:12px}
.editable{color:#8ab4f8;cursor:pointer}
.ev{background:#10141b;border-left:3px solid #25406e;padding:10px 14px;margin-top:6px;font-size:13px;display:none;white-space:pre-wrap}
.hint{font-size:13px;color:#9aa}.timer{float:right;color:#666;font-size:12px}
label.c{margin-right:18px;font-size:15px}
</style></head><body>
<h1>Rawi — usability session <span class="hint">(~20 min; everything stays on this device)</span></h1>

<div class="task on" id="t0">
  <p class="q">Welcome. You'll look at a data dashboard where every figure carries a
  checkmark and every claim has an <b>▸evidence</b> button. There are no wrong answers —
  we are testing the interface, not you.</p>
  <p class="q">Your participant code (any nickname):</p>
  <input id="pid" style="background:#10141b;color:#fff;border:1px solid #2a2f3a;border-radius:8px;padding:8px">
  <p class="q"><label><input type="checkbox" id="consent"> I consent to this session being recorded (answers + timing, stored locally).</label></p>
  <button class="next" onclick="start()">Begin</button>
</div>

<div class="task" id="t1">
  <p class="q">Task 1 — Look at the view below. <b>Is the Q3 total trustworthy? Show why.</b>
  Explore as you like, then type what you found.</p>
  __PASS__
  <textarea id="a1" placeholder="What did you find?"></textarea>
  <button class="next" onclick="next(2)">Next</button><span class="timer" id="tm1"></span>
</div>

<div class="task" id="t2">
  <p class="q">Task 2 — Same view, later. The trend claim now has a warning.
  <b>What is it telling you? What would you do next?</b></p>
  __FLAG__
  <textarea id="a2"></textarea>
  <button class="next" onclick="next(3)">Next</button><span class="timer" id="tm2"></span>
</div>

<div class="task" id="t3">
  <p class="q">Task 3 — Something changed in the underlying data file outside this view.
  <b>What is stale right now, and how can you tell?</b></p>
  __PENDING__
  <textarea id="a3"></textarea>
  <button class="next" onclick="next(4)">Next</button><span class="timer" id="tm3"></span>
</div>

<div class="task" id="t4">
  <p class="q">Task 4 — The price of the editable expense (✎) is wrong by 500.
  <b>Click ✎, enter the correction, and tell me: what happened to the claims?</b></p>
  __PASS2__
  <textarea id="a4"></textarea>
  <button class="next" onclick="next(5)">Next</button><span class="timer" id="tm4"></span>
</div>

<div class="task" id="t5">
  <p class="q">Task 5 — Two views of the same data. <b>Which do you trust more, and why?</b></p>
  <table style="width:100%"><tr>
  <td style="vertical-align:top;padding-right:10px"><p class="hint">View A</p>__PASS3__</td>
  <td style="vertical-align:top"><p class="hint">View B</p>__LOWCOV__</td></tr></table>
  <p><label class="c"><input type="radio" name="t5" value="A"> View A</label>
     <label class="c"><input type="radio" name="t5" value="B"> View B</label>
     <label class="c"><input type="radio" name="t5" value="unsure"> Not sure</label></p>
  <textarea id="a5" placeholder="Why?"></textarea>
  <button class="next" onclick="next(6)">Next</button><span class="timer" id="tm5"></span>
</div>

<div class="task" id="t6">
  <p class="q">Last three questions:</p>
  <p class="q">1. What did the ▸evidence button change about your trust?</p><textarea id="q1"></textarea>
  <p class="q">2. When did you NOT need it?</p><textarea id="q2"></textarea>
  <p class="q">3. What confused you?</p><textarea id="q3"></textarea>
  <button class="next" onclick="finish()">Finish &amp; download my session file</button>
</div>

<div class="task" id="t7">
  <p class="q">Done — thank you! Please send the downloaded <b>.json</b> file to the researcher.</p>
</div>

<script>
const STATES = {pass: __EV_PASS__, flag: __EV_FLAG__, pending: __EV_PENDING__};
const R = {pid:null, started:null, tasks:[], interview:{}, version:"e4-v1"};
let t0 = null, cur = 0;
function bind(scope){
  document.querySelectorAll("#t"+cur+" button.evidence").forEach(btn=>{
    if (btn.dataset.bound) return; btn.dataset.bound = 1;
    btn.addEventListener("click", ()=>{
      let p = btn.parentElement.querySelector(".ev");
      if(!p){p=document.createElement("div");p.className="ev";btn.parentElement.appendChild(p);}
      if(p.style.display==="block"){p.style.display="none";return;}
      const ev = STATES[scope] && STATES[scope][btn.dataset.binding];
      if(!ev){p.textContent="no evidence";p.style.display="block";return;}
      let txt = "";
      const f = ev.focus;
      if (f && (f.correct_value !== null || f.changed_records.length)) {
        txt += "━━ what matters ━━\n";
        if (f.claim_says) txt += "claim says: " + f.claim_says
          + " (expected " + (f.expected*100).toFixed(1) + "%)\n";
        if (f.correct_value !== null)
          txt += "data says:  " + (f.correct_value*100).toFixed(1) + "%  ← the correct value\n";
        for (const [k, s] of Object.entries(f.sides||{}))
          txt += "  " + k + " total = " + s.value + "  (" + s.rows.length + " rows)\n";
        for (const c of f.changed_records)
          txt += "changed: record " + c.record_id + " · " + c.field
               + " " + c.prior + " → " + c.new + "\n";
        txt += "\n";
      }
      txt += "binding: "+ev.binding_id+"  ("+ev.kind+")\nderivation: "+ev.derivation
        +"\nartifact: "+(ev.tuple.authoritative_artifact||"")
        +"\ncheck: provenance="+ev.check.provenance+(ev.check.semantic?" semantic="+ev.check.semantic:"")
        +(ev.check.detail?"\ndetail: "+ev.check.detail:"");
      // only the deciding rows, not the whole table
      if (f && Object.keys(f.sides||{}).length) {
        for (const [k, s] of Object.entries(f.sides)) {
          txt += "\n\n" + k + " deciding rows ("+s.rows.length+"):";
          txt += s.rows.slice(0,6).map(r=>"\n  "+JSON.stringify(r)).join("")
               + (s.rows.length>6?"\n  …":"");
        }
      } else {
        const rows = ev.source_rows.slice(0,6).map(r=>"\n  "+JSON.stringify(r)).join("");
        txt += "\n\nsource rows ("+ev.source_rows.length+"):"+rows+(ev.source_rows.length>6?"\n  …":"");
      }
      p.textContent = txt;
      p.style.display="block";
    });
  });
}
function start(){
  const c=document.getElementById("consent"); const pid=document.getElementById("pid").value.trim();
  if(!c.checked||!pid){alert("Please enter a code and consent.");return;}
  R.pid=pid; R.started=new Date().toISOString(); next(1);
}
function next(n){
  if(cur>=1){R.tasks.push({task:cur, seconds:Math.round((Date.now()-t0)/1000),
    answer:(document.getElementById("a"+cur)||{}).value||"",
    choice:(document.querySelector("input[name=t5]:checked")||{}).value||null});}
  document.getElementById("t"+cur).classList.remove("on");
  cur=n; document.getElementById("t"+n).classList.add("on");
  t0=Date.now();
  bind(n===2?"flag":n===3?"pending":"pass");
  if(n===4){bindEdit();}
}
function bindEdit(){
  const sp=document.querySelector("#t4 .editable"); if(!sp||sp.dataset.bound)return; sp.dataset.bound=1;
  sp.addEventListener("click",()=>{
    const v=prompt("Enter the corrected amount (+500):");
    if(v===null)return;
    R.edit_entered=v;
    alert("Edit applied: the file was updated atomically, the old value kept in history,\\n"+
          "and every dependent claim went PENDING for re-check.\\n"+
          "After re-check: the totals re-prove PASS, and the trend claim is FLAGGED —\\n"+
          "recompute shows +5.2%, the claim still says +0.4%.");
  });
}
function finish(){
  next(7);
  R.interview={q1:q1v(),q2:q2v(),q3:q3v()}; R.finished=new Date().toISOString();
  const blob=new Blob([JSON.stringify(R,null,2)],{type:"application/json"});
  const a=document.createElement("a"); a.href=URL.createObjectURL(blob);
  a.download="e4_"+R.pid+".json"; a.click();
}
const q1v=()=>document.getElementById("q1").value, q2v=()=>document.getElementById("q2").value, q3v=()=>document.getElementById("q3").value;
</script></body></html>"""

page = (PAGE.replace("__PASS2__", html_pass).replace("__PASS3__", html_pass)
            .replace("__PASS__", html_pass).replace("__FLAG__", html_flag)
            .replace("__PENDING__", html_pending).replace("__LOWCOV__", html_lowcov)
            .replace("__EV_PASS__", json.dumps(ev_pass))
            .replace("__EV_FLAG__", json.dumps(ev_flag))
            .replace("__EV_PENDING__", json.dumps(ev_pending)))
out = HERE / "e4_session.html"
out.write_text(page)
print(out)
