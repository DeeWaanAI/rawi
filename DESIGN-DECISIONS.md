# Layer 2 — Design Decision Log

Append-only. Annotate, never rewrite.

**D1 (2026-10-19) — View grammar shape.** Four kinds (`table, list, tree, deck`), four roles
(`value, label, claim, structure`), nodes carry `binding_ref` never values. Rationale:
closed sets make specs machine-validatable and versionable; provenance-by-construction is
the paper's core claim. Grounding: dvr/1.0 spec; litreview §3.1–3.2.

**D2 (2026-10-19) — Evidence affordance v1: full source rows.** First implementation showed
the binding, check result, and all matching source rows. Rationale: completeness.
Grounding: Qafiya R1 verbatim anchoring.

**D3 (2026-10-20) — Evidence affordance v2: focused explanation ("only the lines that
matter").** Owner feedback as E4 participant zero: the v1 panel showed rows but not
*where the error is* or *what the correct value is*. Fix: a `focus` block computed in
`affordance.py` — (a) claim statement vs recomputed correct value (both sides of the
comparison recomputed from current data), (b) the changed-record trail from
`history.jsonl` (record id, field, prior → new), (c) only the *deciding rows* per side,
not the full dump. Rationale: the affordance must answer "what's wrong and what's right"
in one glance; guards against illusion-of-explanatory-depth (litreview [34]) by showing
the *decisive* evidence rather than *more* evidence. Grounding: owner session feedback;
HaLLMark [28] transparency findings. Implementing files: `view-renderer/dvr/affordance.py`
(`build_focus`), `experiments/e4_session/build_session.py`, `experiments/make_demo.py`.
Paper impact: §mechanics gains a worked example; E4 protocol analysis gains a
"feedback-driven refinement" note.

**D4 (2026-10-26) — E4 dropped; revision per external audit.** Owner dropped the E4
usability study on 2026-10-20; audit `instructions_26_oct_2026.md` enforced removal from
paper and spine (one future-work sentence retained: usability deferred to field feedback
after deployment). Same instruction set: abstract caveats on the 135× offline estimate,
"found no evidence in the surveyed set" phrasing, measured scale curve instead of a loose
complexity claim, new L6 expressiveness probe, substrate re-pinned to qafiya v0.2.0
(hash-chained history), AI-usage disclosure added. The D3 focus-block design is kept
(owner-approved 2026-10-20).

**D5 (2026-10-26) — Claim maps rebuilt to monitor schema.** datapoints.json rebuilt in
{id, claim, source, path, expect, marker} form (29 entries); verify_two_way.py checks
artifact==expect AND marker-in-draft, exit 0. semantic-claims.json re-swept against the
post-revision draft: 26 claims + 4 captions, verdict vocabulary verified /
verified-with-note. Reverse sweep (draft→map) found no uncovered headline numbers; the
stale v1 paper-claims.json was removed so the two maps are the single source of truth.
Discrepancy #4 (spine missing corpus composition) found and fixed during this sweep.
