# E4 — Evidence-Affordance Usability Read-Out · Protocol

**Status:** materials ready; requires n ≥ 5 human participants (owner + recruits). No data yet — this file is the frozen protocol. Running it before participants exist would fabricate results; we do not.

**Design constraints from the literature:** guard against illusion of explanatory depth (litreview [34]) and the transparency penalty ([32]): the affordance is one click deep, summaries one line.

## Participants
n ≥ 5, non-authors, mixed technical comfort. Screen: has used a spreadsheet in the last month. 20-minute session, recorded with consent (screen + voice).

## Apparatus
`view-renderer/` prototype serving the frozen experiment corpus (`experiments/corpus/`), seeded into three states across tasks: all-PASS; one FLAG (wrong trend claim); one PENDING (data edited behind the renderer's back).

## Tasks (counterbalanced order)
1. **Locate:** "Is the Q3 total trustworthy? Show me why." — success: opens ▸evidence, identifies source rows and check state.
2. **Interpret FLAG:** "The trend claim has a warning. What is it telling you? What do you do next?" — success: correctly states that recomputation disagrees with the claim AND that the claim text, not the data, is suspect.
3. **Interpret PENDING:** "Something changed. What is stale right now?" — success: identifies which claims are pending and why.
4. **Act:** "Fix the price of record r_051 by +500. What happened to the claims?" — success: performs edit, reports invalidation, checks evidence again.
5. **Calibrate:** "Which of these two views do you trust more?" (100% vs 33% coverage render) — success: prefers and justifies via coverage, not aesthetics.

## Measures
Task success (binary per task), time-to-evidence (T1), trust calibration score (T5), plus 3-question post interview: what did ▸evidence change about your trust? When did you *not* need it? What confused you?

## Analysis
Report per-task success rates and verbatim quotes; qualitative only (n too small for inference). Negative outcomes (users ignore the affordance, misread FLAG as "data is wrong") are reported as design findings, not hidden.

## Honesty clause
If ≥3/5 participants cannot complete T2 unaided, the affordance design — not the participant — is the finding, and the paper reports the redesign.
