# DVR — Declarative View Renderer Specification

**Version:** 1.0 — **FROZEN** (declared 2026-10-20, per monitor request; the contract L3, L4, L6 mock against) · **Product:** DeeWaanAI Rawi — View Renderer (Layer 2) · **Builds on:** Qafiya spec v1.1 (consumed, never modified; vendored qafiya-core pinned at tag **v0.2.0**, commit `a25a299`, spec v1.3 with hash-chained history).
**Normative language:** MUST / SHOULD / MAY as in RFC 2119.
**Thesis:** *A view node carries a `binding_ref`, never a value — so the rendered view is simultaneously the proof source, the edit target, and the audit pointer.*

## 1. Entities

| Entity | Form | Role |
|---|---|---|
| **View spec** | `views/<name>.view.json` | Declarative JSON document; the only input describing structure. |
| **Node** | object in `nodes[]` | One rendered element; carries at most one `binding_ref`. |
| **Binding** | Qafiya spec §2 | External, owned by Layer 1; the renderer resolves and references it, never defines it. |
| **Check state** | Qafiya `binding.check` | Rendered as a visible badge; never suppressed. |

## 2. The view grammar

```jsonc
{
  "spec": "dvr/1.0",                 // MUST match exactly
  "id": "v_q3",                      // MUST be stable, unique, prefixed v_
  "kind": "table",                   // MUST be in the closed kind set (§2.1)
  "title": { "text": "Q3 expenses" },// MAY be present; static text only
  "columns": [                       // REQUIRED iff kind=table
    { "id": "col:date", "label": "Date", "source_field": "date" }
  ],
  "nodes": [                         // MUST be non-empty
    {
      "id": "cell:total",            // unique within the view
      "role": "value",               // closed role set (§2.2)
      "binding_ref": "b_7f3a",       // REQUIRED for value/claim; FORBIDDEN for label/structure
      "column": "col:amount",        // table nodes SHOULD name their column
      "row_key": "r_012",            // row-addressed nodes MUST name the record id
      "editable": true               // MAY be true only for role=value
    }
  ]
}
```

### 2.1 Closed kind set
`kind ∈ { table, list, tree, deck }`. No others. A new kind requires a spec version bump.

### 2.2 Closed role set
`role ∈ { value, label, claim, structure }`.
- `value` — a resolved datum; MAY be `editable` iff its binding has a writeback-able source field (single-record `filter` selecting exactly one record).
- `claim` — renders assertion text with the **▸evidence affordance** (§4); `editable` MUST be false.
- `label` / `structure` — static; MUST NOT carry `binding_ref`.

### 2.3 Well-formedness rules (validator-enforced)
1. Every node `id` is unique within the view.
2. A `value` or `claim` node references **exactly one** existing binding (Qafiya invariant 1).
3. No node contains a literal value for data: fields like `value`, `data`, `number` are FORBIDDEN on nodes. Values exist only behind `binding_ref`.
4. `editable: true` requires `role: value` and a resolvable single-record target.
5. Unknown keys, kinds, or roles are rejected with named errors (fail loud, never guess).

## 3. Rendering

1. A view is a **pure function** of `(spec, bindings, datasets)`: identical inputs MUST produce byte-identical output (Qafiya invariant 9).
2. The renderer MUST resolve each node's displayed value by evaluating the binding's `derivation` over current dataset contents via qafiya-core's `derivations.evaluate` — it MUST NOT print `binding.value` without recompute.
3. A binding that fails to resolve (missing source, derivation error, quarantined artifact) MUST render as an explicit **unresolved state** — never as a guessed or cached number (Qafiya §3.1: gaps are hard stops).
4. Each node MUST render its check badge: `PASS | FAIL | FLAG | PENDING | UNRESOLVED`. Staleness is a visible state, never an implicit assumption.
5. The view MUST report **coverage**: the share of data-bearing nodes whose binding resolved and passed Layer 1. Low coverage is displayed, not smoothed over (Qafiya §4).

## 4. The evidence affordance

Every `claim` node MUST expose ▸evidence. Activating it reveals, all resolved live at click time:
1. the binding object (id, derivation, sources, statistic/device/artifact tuple);
2. the **verbatim source rows** matching the binding's filter;
3. the last check result (Layer 1 + Layer 2 states, checked_at, detail).

The affordance SHOULD be one click deep and its summary one line (guard against illusion-of-explanatory-depth and transparency-penalty findings — litreview refs [32], [34]).

## 5. Edits

1. A user edit MUST NOT mutate data directly. It MUST produce an `edit` binding:
   `{ id, kind:"edit", target:{view,node}, writeback:{dataset, record_id, field, op:"set", value}, provenance:{created_by, created_at} }`.
2. The edit binding is handed to `qafiya_core.engine.apply_edit`, which guarantees atomic write-back, history logging, and §6 transitive invalidation.
3. After an edit the renderer MUST re-resolve affected nodes and re-render badges; a claim's assertion text MUST never be altered by the renderer (that is what the semantic layer flags).
4. Only `op: "set"` is supported in dvr/1.0 (mirrors qafiya-core v1).

## 6. Kinds — minimal semantics

| Kind | Node addressing | Notes |
|---|---|---|
| `table` | `row_key` + `column` | columns declared in `columns[]`; editable cells are `value` nodes |
| `list` | `row_key` (or order) | ordered values |
| `tree` | `path` (parent/child ids) | folder/sub-folder hierarchies per layer mission |
| `deck`  | `slide:N` + slot | ordered slides; each slot is a node |

All kinds share §2–§5 unchanged; the kind only affects layout.

## 7. Invariants (testable properties)

1. No rendered number exists in the view spec (validator-enforced).
2. Every rendered value traces to exactly one binding (resolution-enforced).
3. Byte-identical re-render under unchanged inputs (purity).
4. Every edit leaves an `edit` binding and a history entry.
5. After any edit, every transitively dependent binding is PENDING before it is anything else.
6. Every claim node renders ▸evidence; the affordance's verbatim rows byte-match the dataset.
7. Coverage is rendered with every view.
8. An unresolved binding is visibly unresolved — never silent, never guessed.

Each maps to a Tier-A test in the brief (F1–F8) and a paper claim.

## 8. Non-goals

Query understanding and model choice (Layer 5). Persistence across sessions (Layer 4). Pixel-perfect layout/theming (replaceable rendering concern). New derivation functions (Qafiya owns the closed set). Any modification of Qafiya spec v1.1 — insufficiencies are reported upward.

---
*Companion to `brief.md` (approved by owner 2026-10-19) and `litreview/review.md`. Next: prototype, then frozen experiments.*
