# Response to MONITOR-GUIDE.md (2026-10-20)

## 1. dvr/1.0 status → FROZEN
Declared in `spec.md` header (2026-10-20). L3, L4, L6 may mock against it.
Any change from here requires a version bump to dvr/1.1 with a changelog entry.

## 2. Hash chain
Acknowledged — no action until Qafiya v1.3 lands. The Layer-1 gate calls
(`provenance_gate`) will inherit chain verification through qafiya-core. No paper impact.

## 3. E4 human usability
Owner decision 2026-10-19: deferred ("keep the human user's feedback for later").
Materials are ready and frozen: `experiments/e4_usability_protocol.md` (protocol,
scoring, honesty clause) and `experiments/e4_session/e4_session.html` (one-click
session runner, built from the frozen corpus by `build_session.py`). The paper's E4
section claims no results until n≥5 sessions land in `experiments/results/raw/e4/`.

## 4. Vendored substrate pin
`qafiya-ref/` is pinned at tag **v0.2.0** (commit `a25a2997875294f6e855ed11c2ac83fcb13b7d10`,
2026-10-20 — spec v1.3, hash-chained tamper-evident history). All renderer tests and the
Layer-1 gate pass against it. Update of 2026-10-26 per `instructions_26_oct_2026.md`;
supersedes the earlier `0c6733d` pin.
