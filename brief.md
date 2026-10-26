# Layer 2 — View Renderer · Design Brief

**Status:** draft for owner confirmation — no code will be written until approved.
**Paper title:** *Verifiable Generative Views: Rendering, Editing, and Auditing LLM-Generated Interfaces over Bound Data.*
**Builds on:** Qafiya spec v1.1 (`01-data-layer-qafiya/spec/spec.md`), consumed as a contract — never modified. Precedents cited per the Layer-2 literature review (`litreview/review.md`, refs [#] below point to its reference list).

---

## 1. What we are building, in one paragraph

A renderer that takes three inputs — a **view spec** (declarative JSON), a set of **Qafiya bindings**, and the **frozen datasets** — and draws an interactive view (table, list, tree, deck). Every data-bearing node in the view carries a `binding_ref`, never a value. The renderer resolves values by evaluating each binding's `derivation` over its `sources` at render time. A user edit never touches data directly: it emits an `edit` binding whose `writeback` clause is applied by qafiya-core, triggering transitive invalidation of dependent bindings. Every claim node shows an **▸evidence affordance** that reveals the binding, the source rows, and the last two-layer check result.

The one-sentence contribution: **render = proof source, edit = binding, audit = recomputable check — in one artifact.**

## 2. The view grammar (the design artifact)

A view is a single JSON document. Small, closed, versioned — same discipline as Qafiya's schema and derivation sets.

```jsonc
{
  "spec": "dvr/1.0",
  "id": "v_q3",
  "kind": "table",                    // table | list | tree | deck
  "title": { "text": "Q3 expenses" }, // static text, no binding needed
  "nodes": [
    {
      "id": "cell:total",
      "role": "value",                // value | label | claim | structure
      "binding_ref": "b_7f3a",        // <-- the only way data enters a view
      "editable": true                // iff binding has a writeback-able source field
    },
    {
      "id": "claim:trend",
      "role": "claim",
      "binding_ref": "b_9c11",        // a kind=claim binding; renders with ▸evidence
      "editable": false
    }
  ]
}
```

Design decisions, each tied to a literature finding:

1. **Nodes carry `binding_ref`, never values.** Grammars like Vega-Lite [1], Altair [2], GoTree [3], Cicero [4] embed or inline data. We inherit their compositional spec style but change what a node *carries*. This is the layer's core differentiator.
2. **Four view kinds, closed set.** `table`, `list`, `tree`, `deck` — covers the layer's mission without reopening grammar design each time; new kinds require a spec version bump (same rule as Qafiya block types). GoTree [3] proves a small grammar covers tree rendering; Cicero [4] proves responsiveness composes declaratively.
3. **Roles, not widgets.** A node is `value | label | claim | structure`. `claim` nodes get the evidence affordance automatically; `value` nodes may be `editable`. This keeps the grammar about *data accountability*, not pixel layout — the pixel layer is a rendering concern, replaceable.
4. **A view is a pure function** of (spec + bindings + current dataset) — Qafiya invariant 9 made concrete. No state hidden in the renderer. This is what makes round-trip correctness testable (§5, E2).
5. **Emission cost paid once.** The model emits the spec + bindings once; rendering, editing, re-checking are deterministic and local. Contrasts with generative-UI systems (Generative Interfaces [15], Software as Content [19], Bespoke [20]) where every interaction is a new prompt — the cost gap our literature review found unmeasured [13, 14].

## 3. The three mechanics

### 3.1 Render (proof source)
Renderer resolves each `binding_ref` → evaluates `derivation` over `sources` → draws. If a binding fails to resolve or fails Qafiya Layer-1 check, the node renders as an explicit **unresolved/stale state**, never as a guessed number (Qafiya §3.1: gaps are hard stops). A view with 30% coverage renders differently — visibly — from one with 100% (coverage is first-class, per Qafiya §4).

### 3.2 Edit (binding, not mutation)
A cell edit emits `{kind:"edit", writeback:{dataset, record_id, field, op}}` and hands it to qafiya-core: atomic write-temp-then-rename, `history.jsonl` logs the prior value, §6 transitive invalidation marks dependent bindings PENDING, the view re-resolves. Differentiator: direct-manipulation tools (Data Illustrator [22], Lyra 2 [23], DirectVis [25]) edit the *visualization*; we edit the *record through a provenance object*, and staleness becomes visible rather than silent — the failure mode documented in reactive notebooks [37].

### 3.3 Audit (▸evidence affordance)
Every `claim` node shows ▸evidence. Clicking reveals three things, all live: (a) the binding object, (b) the verbatim source rows, (c) the last check result (PASS / FAIL / FLAG / PENDING) with detail. Differentiator: HaLLMark [28] shows provenance for writing; ALCE [29]/FActScore [30] score faithfulness post-hoc. Ours is a *recomputable check behind the affordance* — and the design anticipates the documented risks: illusion of explanatory depth [34] and the transparency penalty [32] motivate keeping the affordance one click deep and the summary one line long.

## 4. Architecture

```
view-renderer/
  spec.md            # dvr/1.0 grammar formalized (MUST/SHOULD/MAY)
  renderer/          # spec + bindings + datasets -> interactive HTML view
    resolve.py       # binding_ref -> value via qafiya-core eval
    render.py        # pure: (spec, resolved, check-state) -> HTML
    affordance.py    # ▸evidence panel data assembly
  edits.py           # UI event -> edit binding -> qafiya-core writeback
  state.py           # check-state badges: PASS/FAIL/FLAG/PENDING per node
tests/               # see §5
experiments/         # frozen runs, spine script recompute (Qafiya discipline)
```

No new data model. No persistence across sessions (Layer 4). No query understanding (Layer 5). The renderer consumes Qafiya spec v1.1 and qafiya-core's `gate`, `edit`, `invalidate` API only.

## 5. Test plan — functionality first, then limits

Two tiers. **Tier A (functional)** proves the system works. **Tier B (limits)** proves where it provably cannot work — per PROJECT.md rule 5, negative results are reported as results.

### Tier A — functional tests (unit + integration, all automated)

| # | Test | Pass criterion |
|---|---|---|
| F1 | Grammar validation: reject spec with embedded value, missing `binding_ref`, unknown kind/role | 100% of malformed fixtures rejected with named errors |
| F2 | Resolution: each node value equals `eval(derivation, sources)` from qafiya-core | equality on all fixtures, incl. NaN/missing-source cases rendering as unresolved |
| F3 | Purity: same (spec, bindings, dataset) rendered twice → byte-identical HTML | diff = 0 |
| F4 | Edit path: UI edit → edit binding → file updated atomically → history entry written | file value = edit; history contains prior value; no partial writes under simulated crash (kill mid-write) |
| F5 | Invalidation visibility: after F4, dependent claim node shows PENDING until re-check, then correct state | badge sequence observed: PASS → PENDING → FLAG/PASS |
| F6 | ▸evidence: every claim node exposes binding + source rows + check result; verbatim excerpts match source bytes | excerpt equality check |
| F7 | Coverage display: view reports bound/unbound share | matches hand-computed fixture ratio |
| F8 | Contract compliance: renderer uses only Qafiya spec v1.1 entities + qafiya-core public API | static import/usage audit |

### Tier B — limits and stress (each is a paper result, pass or fail)

| # | Probe | What we measure / expect |
|---|---|---|
| L1 | **Round-trip correctness** (experiment E2): N random valid edits through views | target: 100% re-prove at Layer 1; any miss is a reported defect with repro |
| L2 | **Stale-detection honesty**: edit data *behind the renderer's back* (direct file edit) | renderer must show PENDING/FAIL on next check — never silently green (the reactive-notebook failure mode [37]) |
| L3 | **Shared-error blindness** (Qafiya provable limit 1): inject a wrong value where claim and data agree | system *cannot* catch it — we measure and report this as a known limit, not a bug |
| L4 | **Scale ceiling**: nodes per view, bindings per dataset (10, 100, 1k, 10k) | render time + memory curve; state the number where it degrades past usability |
| L5 | **Concurrency**: two edits to the same record in flight | atomicity holds or one edit is rejected — report which |
| L6 | **Grammar expressiveness ceiling**: attempt N real-world view requests from the experiment corpus | report % expressible in dvr/1.0 without extension; unexpressible ones listed honestly |
| L7 | **Coverage honesty**: view over partially-bound data | low coverage is loud (rendered, stated), never smoothed over |

### Tier C — the four frozen paper experiments (from INSTRUCTIONS.md)

| # | Experiment | Frozen artifact | Headline metric |
|---|---|---|---|
| E1 | **C6 durability end-to-end**: scripted real user edit → file → invalidation → flag | run log + diffs + check states | closes Qafiya's open claim; pass/fail with the full trace |
| E2 | **Round-trip correctness**: N ≥ 100 random edits through views | edit script + recompute log | % re-proved at Layer 1 (target 100%) |
| E3 | **Rendering cost**: spec-once vs per-keystroke prompting | token counts per interaction script | tokens/interaction ratio, with the interaction script frozen |
| E4 | **Evidence-affordance usability** (n ≥ 5, qualitative) | session transcripts + task sheets | can users find and correctly interpret PASS/FLAG/FAIL? — designed against illusion-of-depth [34] / transparency-penalty [32] findings |

All Tier C experiments follow the Qafiya discipline: frozen inputs before runs, a `spine.py` recomputing every headline number from raw artifacts, and if the spine fails the number does not go in the paper.

## 6. Deliverable order

`brief.md` (this file) → **owner confirmation** → `spec.md` (dvr/1.0 formal) → prototype (`view-renderer/`, Tier A green) → Tier B limits → frozen Tier C experiments → paper draft (.tex, HBR register, before/after examples in every experiment section).

## 7. What this brief deliberately excludes

Query understanding, model choice, session persistence, multi-user sync, mobile/native rendering, and any modification of Qafiya. If a test reveals the Qafiya contract is insufficient, we report the gap upward instead of patching around it.

---
*Awaiting owner confirmation. No code written yet.*
