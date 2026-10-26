# Verifiable Generative Views: Rendering, Editing, and Auditing LLM-Generated Interfaces over Bound Data — A Systematic Literature Review

**Scope:** the *view renderer* layer only (Layer 2 of DeeWaanAI OS) — declarative view grammars, LLM-generated interfaces, data↔view binding and write-back, evidence/audit affordances, and the recompute/invalidation machinery that keeps a view correct after an edit. The data substrate beneath (Qafiya, Layer 1) and everything above (action, memory, routing, shell) are out of scope.
**Review type:** structured thematic review (scoping + targeted synthesis), replicating the Layer-1 review pipeline (`search.py`, `screen.py`, `verify.py`).
**Date searched:** 2026-10-19. **Window:** 2018-01-01 to 2026-12-31 (one foundational pre-window exception, flagged below).
**Databases:** OpenAlex (primary), arXiv (preprints). All 42 included citations verified programmatically against the OpenAlex DOI resolver / arXiv API (`raw/included_verified.json`).

---

## Abstract

Layer 2 of DeeWaanAI OS turns Qafiya *bindings* into real interactive views — tables, lists, trees, decks — that a user can read, edit, and audit, where "re-run it yourself" becomes visible. This review maps the five research literatures such a renderer must stand on: (1) declarative view grammars, (2) LLM-generated views and generative UI, (3) data↔view binding and write-back (editing through views), (4) evidence and audit affordances in interfaces, and (5) reactive/incremental recompute and invalidation. From 797 records we screened 749 deduplicated candidates and synthesised 42 verified works. The central finding mirrors and extends the Layer-1 finding: each community has solved one facet — grammars render typed data, LLMs generate interfaces from intent, direct-manipulation tools edit visualizations, XAI/provenance work surfaces explanations, and reactive systems propagate change — but **no surveyed work defines a view spec whose nodes carry provenance-carrying bindings rather than values**, so that a single artifact is simultaneously the render output, the edit target, and the audit pointer. Generated views today are either correct-but-static (grammars), interactive-but-unverified (generative UI), or editable-but-unaccountable (direct manipulation). We state that gap as the layer's novelty claim and derive the four experiments the layer instructions require.

## 1. Introduction and research questions

The Layer-1 review established that a provenance-first *data model* is missing from the literature; Qafiya spec v1.1 supplies it, with the **binding** as core primitive — one object that is simultaneously render source, edit target, and audit pointer. Layer 2 asks the follow-on question: what exists toward *rendering* such bound data as interactive views a person can read, edit, and audit?

**Primary RQ.** *What prior work exists toward rendering LLM-generated, interactive views over bound data — where every view node resolves through a provenance-carrying binding, edits write back as bindings, and every claim exposes its evidence — and where is the integration gap?*

Sub-questions:

- **RQ1 (grammars).** What declarative grammars exist for specifying interactive views (charts, trees, responsive layouts), and what do they assume about the data they render?
- **RQ2 (generation).** How do LLM systems generate views/interfaces from natural-language intent, at what cost (per-keystroke prompting vs spec-once), and how is the output bound to data?
- **RQ3 (write-back).** How do views support editing *through* the interface back to the underlying data, and what happens to dependent derived values after an edit?
- **RQ4 (audit).** What interface affordances surface evidence, provenance, uncertainty, or verification status for generated content — and do any expose a *recomputable* check?
- **RQ5 (invalidation).** What machinery (reactive notebooks, incremental view maintenance, self-adjusting computation) keeps a derived view correct after its source changes, and has it been applied to generated UIs?

## 2. Methods

### 2.1 Search strategy

OpenAlex `title_and_abstract.search` and arXiv field queries were executed programmatically on 2026-10-19 (2018–2026, relevance-sorted, per-query caps of 25/30), reusing the Layer-1 pipeline verbatim with Layer-2 concept blocks. Representative strings:

| Block | Example query strings |
|---|---|
| View grammars | `"declarative visualization grammar"`, `"grammar of graphics" interactive`, `"tree visualization" grammar` |
| LLM-generated views | `"generative user interface"`, `"large language model" visualization generation`, `"just-in-time" interface`, `model-generated interface` |
| Binding & write-back | `direct manipulation editing visualization`, `"data binding" user interface`, `"what-if" analysis visualization` |
| Audit affordances | `provenance visualization user interface`, `citation display generated text`, `uncertainty visualization communication`, `explainable AI interface` |
| Reactive recompute | `reactive programming user interface`, `incremental view maintenance`, `"reactive notebook"`, `"live programming" data` |

### 2.2 Screening and inclusion

Records were deduplicated by DOI (normalized-title fallback), screened by a keyword-relevance score per theme (threshold ≥ 4), then manually curated to works that materially inform the renderer. **Exclusions:** domain-locked visualization tools (bioinformatics tree editors, VR toolkits) unless the binding idea transfers; pure XAI *algorithm* papers without an interface contribution; generic web-framework reactive programming without a data-correctness angle. The heavy noise floor in the write-back and reactive blocks (genomics, chemistry) was filtered at curation. Key works known from the Layer-1 review (Altair, GoTree, Data Formulator, LIDA, the generative-UI cluster) were confirmed present in, or re-resolved against, this search and carried forward so the two reviews cross-cite consistently.

### 2.3 PRISMA flow

| Stage | n |
|---|---|
| Identified — OpenAlex | 701 |
| Identified — arXiv | 96 |
| **Total identified** | **797** |
| After deduplication | 749 |
| Passed relevance screen (score ≥ 4) | 110 |
| **Included in synthesis** | **42** |

### 2.4 Citation verification

Every included identifier was resolved against OpenAlex (DOI) or the arXiv API and canonical metadata (title, year, venue, authors) retrieved programmatically; two initial identifier guesses (DataTales, Idyll) resolved to unrelated records and were corrected to `10.1109/vis54172.2023.00055` and `10.1145/3242587.3242600` after title confirmation. Author lists are registry-derived and should be spot-checked at typesetting.

## 3. Results — thematic synthesis

### 3.1 Declarative view grammars (RQ1)

The grammar lineage proves that a *small composable spec* renders rich interactive views: **Vega-Lite** [1] (foundational, 2016 — the one pre-window work, retained because every later system compiles to or differentiates against it), **Altair** [2], tree grammars (**GoTree** [3]), responsive grammars (**Cicero** [4]), procedural generation grammars (**Atlas** [5]), and annotation grammars (**AnnoGram** [6]). NL-to-spec pre-LLM systems (**Data2Vis** [7], **NL4DV** [8]) showed intent can compile into these grammars with classical models.

*Synthesis.* Grammars are mature, deterministic, and cheap — but every one of them assumes the spec **embeds or points at finished, trusted data**. The spec is a rendering recipe, not a provenance object: nothing in a Vega-Lite node knows which source rows produced it, and nothing downstream can re-verify it. Layer 2's view grammar borrows this whole lineage but changes what a node *carries*: a `binding_ref`, never a value.

### 3.2 LLM-generated views and generative UI (RQ2)

LLMs moved authoring from "write the spec" to "say what you want": **Data Formulator** [9] and **Data Formulator 2** [10] (concept-driven authoring with AI-managed data transformation), **LIDA** [11] (grammar-agnostic auto-generation), **DataTales** [12] (LLM-authored data-driven articles), and benchmarks measuring the flood (**VisEval** [13], LLM visualization-generation evaluations [14]). In parallel, *generative UI* became a named subfield: **Generative Interfaces for Language Models** [15], a working definition [16], personalization [17], DSL-brick approaches balancing transparency and control (**LEGOUI** [18]), "software as content" dynamic applications [19], and just-in-time interfaces from intent (**Bespoke** [20]); conversational programming assistance rounds out the interaction model [21].

*Synthesis.* Generation quality is no longer the bottleneck — evaluation papers now measure *how well* models generate views, not *whether* they can. But in every surveyed system the generated artifact's tie to data is **ephemeral**: the data is baked into the component at generation time, or fetched by generated code with no durable, inspectable binding. Editing means re-prompting; auditing means trusting. Nobody reports the *cost structure* of per-interaction re-prompting versus emit-spec-once rendering — a gap the layer's rendering-cost experiment (spec-once vs per-keystroke, token evidence) addresses directly.

### 3.3 Data↔view binding and write-back (RQ3)

Editing *through* a view has strong precedents in visualization authoring: **Data Illustrator** [22] binds shapes to data for design, **Lyra 2** [23] does it by demonstration, **StructGraphics** [24] makes graphical structures reusable across data, and **DirectVis** [25] brings direct-manipulation editing to code-based interactive visualizations; natural-language editing of visual knowledge graphs shows the same drive from the NL side [26]. **Idyll** [27] established reactive markup for interactive articles — text and graphics that recompute when parameters change.

*Synthesis.* These systems make views *editable*, but the edit lands in the *visualization* or in an opaque runtime state — none treats the edit as a **first-class provenance object** (an `edit` binding naming the exact record/field to update, atomically, with prior state retained). And none answers the follow-up question: after the edit, which *claims derived from that record* are now stale? Write-back exists; accountable write-back with transitive invalidation does not.

### 3.4 Evidence and audit affordances in interfaces (RQ4)

Interfaces that surface evidence are a growing HCI literature: **HaLLMark** [28] visualizes LLM provenance in writing; citation/attribution evaluation (**ALCE** [29], **FActScore** [30]) scores whether generated claims are supported — as post-hoc metrics, not live interface affordances. Uncertainty communication ([31]: why authors don't visualize it) and provenance-density displays ([32], IJCAI 2026) show transparency's benefits and its "transparency penalty"; trust-calibration work warns that explanation interfaces create illusions of depth ([33], [34]); **XNLI** [35] explains NL-interaction analysis pipelines; analytic-provenance instrumentation [36] frameworks capture analyst trails.

*Synthesis.* The field has converged on *showing* provenance and *measuring* faithfulness — separately. What no surveyed interface exposes is a **recomputable check behind the affordance**: an ▸evidence control that reveals not just "the model said this came from here" but "here is the binding, here are the source rows, here is the last deterministic re-check result — and it currently FAILs/PENDs." The layer's evidence affordance is precisely this join, and the small usability read-out tests whether users can actually use it.

### 3.5 Reactive recompute and invalidation (RQ5)

Keeping derived views correct after change is solved machinery in three disconnected communities: reactive notebooks and their known failure modes (**When Do Reactive Notebooks Fail to React?** [37] — directly relevant: reactivity silently breaks), live-programming GUIs (**Glinda** [38]), distributed reactive languages with live updates (**Meerkat** [39]), grounded agentic analysis in reactive notebooks (**marimo-lens** [40]), and the database community's incremental view maintenance ([41], [42]).

*Synthesis.* Invalidation is a solved *engineering* problem — and [37] documents that even mature reactive systems fail silently, which is exactly why Layer 2 must make staleness a *visible, checked state* (PENDING/FAIL flags from Qafiya §6) rather than an implicit runtime assumption. No surveyed work wires transitive invalidation through a provenance substrate into a *generated* UI: this seam is unoccupied.

## 4. The gap and the layer's novelty claim

The five literatures each solve one facet and leave the seams between them open:

- Grammars render typed data but embed values; nodes know nothing of provenance [1–8].
- LLM generation produces views from intent but binds data ephemerally, with no write-back and unmeasured re-prompting cost [9–21].
- Direct-manipulation editing writes through views, but edits are not provenance objects and dependent claims are not invalidated [22–27].
- Audit interfaces show provenance or score faithfulness post-hoc; none exposes a live, recomputable check [28–36].
- Reactive/IVM machinery propagates change correctly but invisibly, and is unconnected to generated UIs or provenance [37–42].

**Novelty claim (defensible).** *We propose a verifiable generative view layer: a small declarative view grammar whose nodes carry `binding_ref` (never values) into a provenance-first substrate, rendered deterministically; in which a cell edit is an `edit` binding with atomic write-back and transitive invalidation of dependent claims; and in which every claim exposes its evidence — binding, source rows, and last check result — through a single affordance. The contribution is the integration: render = proof source, edit = binding, audit = recomputable check, in one artifact.*

**Closest neighbours to differentiate explicitly:** Data Formulator 2 [10] (LLM authoring with data transformation — no provenance bindings, no audit affordance), Generative Interfaces [15] / Software as Content [19] / Bespoke [20] (interactive generated UI — ephemeral, unverified data binding), DirectVis [25] (edit the visualization — not the data, no provenance), reactive notebooks [37, 40] (recompute exists — but silent failure modes and no claim-level audit), HaLLMark [28] (provenance UI for writing — not for data views, not recomputable).

## 5. Evidence required to defend the claim (experiments, per layer instructions)

The gap analysis maps directly onto the four frozen experiments the layer must run:

1. **C6 durability end-to-end** (closes the Qafiya paper's open claim): a real user-driven edit through a rendered view → atomic file write-back → transitive invalidation → visible flag. Supported by §3.3 (write-back precedents) and §3.5 (invalidation machinery); differentiated from both by the binding as the edit object.
2. **Round-trip correctness:** N random edits through views re-prove 100% at Layer 1 — tests invariant "a view is a pure function of (structure + bindings + current dataset)".
3. **Rendering cost:** spec-once vs per-keystroke prompting, token evidence — the cost question §3.2 found unmeasured across the generative-UI literature.
4. **Evidence-affordance usability** (n≥5 qualitative): does ▸evidence (binding + rows + check result) produce calibrated trust — designed against the illusion-of-depth warning [34] and the transparency-penalty finding [32].

## 6. Limitations of this review

Same bounds as the Layer-1 review: single-pass automated search on two databases (Semantic Scholar rate-limited); keyword-score screening plus manual curation rather than dual review, so recall is bounded by the query strings — the write-back and reactive blocks had heavy domain noise that curation, not the score, resolved. Vega-Lite [1] (2016) is the single pre-window inclusion, retained as the foundational grammar; other pre-2018 lineage (grammar of graphics, self-adjusting computation, hypertext/compound documents) is acknowledged but not exhaustively covered. Several 2025–2026 items are recent preprints not yet peer-reviewed. Author metadata is registry-derived. These bound completeness, not the direction of the gap, which is corroborated independently across all five themes and is consistent with the Layer-1 review's independent finding from the data-model side.

## 7. References

1. Satyanarayan, A., Moritz, D., Wongsuphasawat, K., et al. (2016). *Vega-Lite: A Grammar of Interactive Graphics.* IEEE TVCG. https://doi.org/10.1109/tvcg.2016.2599030 *(foundational; pre-window)*
2. VanderPlas, J., Granger, B., Heer, J., et al. (2018). *Altair: Interactive Statistical Visualizations for Python.* JOSS. https://doi.org/10.21105/joss.01057
3. Li, G., Tian, M., Xu, Q., et al. (2020). *GoTree: A Grammar of Tree Visualizations.* ACM CHI. https://doi.org/10.1145/3313831.3376297
4. Kim, H., Rossi, R. A., Du, F., et al. (2022). *Cicero: A Declarative Grammar for Responsive Visualization.* ACM CHI. https://doi.org/10.1145/3491102.3517455
5. Liu, Z., Chen, C., Morales, F., et al. (2021). *Atlas: Grammar-based Procedural Generation of Data Visualizations.* IEEE VIS. https://doi.org/10.1109/vis49827.2021.9623315
6. Rahman, M. D., Rahat-Uz-Zaman, M., McNutt, A., et al. (2025). *AnnoGram: An Annotative Grammar of Graphics Extension.* IEEE VIS. https://doi.org/10.1109/vis60296.2025.00053
7. Dibia, V. C., Demiralp, Ç. (2019). *Data2Vis: Automatic Generation of Data Visualizations Using Sequence-to-Sequence Recurrent Neural Networks.* IEEE CG&A. https://doi.org/10.1109/mcg.2019.2924636
8. Narechania, A. A., Srinivasan, A., Stasko, J. (2020). *NL4DV: A Toolkit for Generating Analytic Specifications for Data Visualization from Natural Language Queries.* IEEE TVCG. https://doi.org/10.1109/tvcg.2020.3030378
9. Wang, C., Thompson, J., Lee, B. (2023). *Data Formulator: AI-powered Concept-driven Visualization Authoring.* IEEE TVCG. https://doi.org/10.1109/tvcg.2023.3326585
10. Wang, C., Lee, B., Drucker, S., et al. (2024). *Data Formulator 2: Iterative Creation of Data Visualizations, with AI Transforming Data Along the Way.* arXiv. https://doi.org/10.48550/arXiv.2408.16119
11. Dibia, V. C. (2023). *LIDA: Automatic Generation of Grammar-Agnostic Visualizations and Infographics using Large Language Models.* ACL. https://doi.org/10.18653/v1/2023.acl-demo.11
12. Sultanum, N., Srinivasan, A. (2023). *DATATALES: Investigating the Use of Large Language Models for Authoring Data-Driven Articles.* IEEE VIS. https://doi.org/10.1109/vis54172.2023.00055
13. Chen, N., Zhang, Y., Xu, J., et al. (2024). *VisEval: A Benchmark for Data Visualization in the Era of Large Language Models.* IEEE TVCG. https://doi.org/10.1109/tvcg.2024.3456320
14. Wang, X., Liang, C., Zheng, S., et al. (2024). *Visualization Generation with Large Language Models: An Evaluation.* arXiv. https://doi.org/10.48550/arXiv.2401.11255
15. Chen, J., Zhang, Y., Zhang, Y., et al. (2025). *Generative Interfaces for Language Models.* arXiv. https://doi.org/10.48550/arXiv.2508.19227
16. Lee, K. (2025). *Towards a Working Definition of Designing Generative User Interfaces.* ACM DIS. https://doi.org/10.1145/3715668.3736365
17. Peng, Y.-H., Bigham, J. P., Wu, J. (2026). *Efficient Personalization of Generative User Interfaces.* arXiv. https://doi.org/10.48550/arXiv.2604.09876
18. Zhou, Y., Yuan, M., Xu, H., et al. (2026). *LEGOUI: Designing with UI-DSL Bricks to Balance Transparency and Controllability.* arXiv. https://doi.org/10.48550/arXiv.2608.04293
19. Xie, M., Xie, Y. (2026). *Software as Content: Dynamic Applications as the Human-Agent Interaction Layer.* arXiv. https://doi.org/10.48550/arXiv.2603.21334
20. Nandy, P., Ađalgeirsson, S. Ö., Sinha, A. K., et al. (2024). *Bespoke: Using LLM Agents to Generate Just-in-Time Interfaces by Reasoning about User Intent.* ACM. https://doi.org/10.1145/3686215.3688372
21. Ross, S., Martinez, F., Houde, S., et al. (2023). *The Programmer's Assistant: Conversational Interaction with a Large Language Model for Software Development.* ACM IUI. https://doi.org/10.1145/3581641.3584037
22. Liu, Z., Thompson, J., Wilson, A., et al. (2018). *Data Illustrator.* ACM CHI. https://doi.org/10.1145/3173574.3173697
23. Zong, J., Barnwal, D., Neogy, R., et al. (2020). *Lyra 2: Designing Interactive Visualizations by Demonstration.* IEEE TVCG. https://doi.org/10.1109/tvcg.2020.3030367
24. Tsandilas, T. (2020). *StructGraphics: Flexible Visualization Design through Data-Agnostic and Reusable Graphical Structures.* IEEE TVCG. https://doi.org/10.1109/tvcg.2020.3030476
25. Park, J., An, M., Yang, H., et al. (2026). *DirectVis: Editing Code-Based Interactive Visualization with Direct Manipulation.* IEEE PacificVis. https://doi.org/10.1109/pacificvis68791.2026.00014
26. Shahriari, R., Ragan, E. D., Ruiz, J. (2025). *Natural Language Interaction for Editing Visual Knowledge Graphs.* ACM K-CAP. https://doi.org/10.1145/3731443.3771344
27. Conlen, M., Heer, J. (2018). *Idyll: A Markup Language for Authoring and Publishing Interactive Articles on the Web.* ACM UIST. https://doi.org/10.1145/3242587.3242600
28. Hoque, M. N., Mashiat, T., Ghai, B., et al. (2024). *The HaLLMark Effect: Supporting Provenance and Transparent Use of Large Language Models in Writing with Interactive Visualization.* ACM CHI. https://doi.org/10.1145/3613904.3641895
29. Gao, T., Yen, H., Yu, J., et al. (2023). *Enabling Large Language Models to Generate Text with Citations (ALCE).* EMNLP. https://doi.org/10.48550/arXiv.2305.14627
30. Min, S., Krishna, K., Lyu, X., et al. (2023). *FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation.* EMNLP. https://doi.org/10.48550/arXiv.2305.14251
31. Hullman, J. R. (2019). *Why Authors Don't Visualize Uncertainty.* IEEE TVCG. https://doi.org/10.1109/tvcg.2019.2934287
32. Zhang, Q., Huang, Y., Lee, J., et al. (2026). *Beyond "Made with AI": Visualizing Provenance Density to Mitigate the Transparency Penalty.* IJCAI. https://doi.org/10.24963/ijcai.2026/857
33. Ghajargar, M., Bardzell, J., Smith-Renner, A., et al. (2021). *From "Explainable AI" to "Graspable AI".* ACM. https://doi.org/10.1145/3430524.3442704
34. Chromik, M., Eiband, M., Buchner, F., et al. (2021). *I Think I Get Your Point, AI! The Illusion of Explanatory Depth in Explainable AI.* ACM IUI. https://doi.org/10.1145/3397481.3450644
35. Feng, Y., Wang, X., Pan, B., et al. (2023). *XNLI: Explaining and Diagnosing NLI-Based Visual Data Analysis.* IEEE TVCG. https://doi.org/10.1109/tvcg.2023.3240003
36. Yang, L., Morizet-Mahoudeaux, P., Guénand, A., et al. (2018). *A Design Framework for Instrumenting Analytic Provenance for Problem-Solving Tasks.* Advances in Intelligent Systems and Computing. https://doi.org/10.1007/978-981-10-8612-0_66
37. Lu, Y., Zheng, M., Crichton, W., et al. (2025). *When Do Reactive Notebooks Fail to React?* arXiv. https://doi.org/10.48550/arXiv.2511.21994
38. DeLine, R. A. (2021). *Glinda: Supporting Data Science with Live Programming, GUIs and a Domain-specific Language.* ACM CHI. https://doi.org/10.1145/3411764.3445267
39. Zhong, H., Liu, A. (2024). *Meerkat: A Distributed Reactive Programming Language with Live Updates.* arXiv. https://doi.org/10.48550/arXiv.2407.06885
40. Gyarmati, P. F., Manz, T., Moritz, D., et al. (2026). *Point, Revise, Review: Grounded Agentic Analysis in Reactive Notebooks with marimo-lens.* arXiv. https://doi.org/10.48550/arXiv.2609.19839
41. Nikolić, M., Olteanu, D. (2018). *Incremental View Maintenance with Triple Lock Factorization Benefits.* ACM SIGMOD. https://doi.org/10.1145/3183713.3183758
42. Svingos, C., Hernich, A., Gildhoff, H., et al. (2023). *Foreign Keys Open the Door for Faster Incremental View Maintenance.* PACMMOD. https://doi.org/10.1145/3588720

---
*Reproducibility artifacts:* `search.py` (queries), `raw/openalex.json`, `raw/arxiv.json`, `raw/combined.json`, `screen.py`, `verify.py`, `raw/included_verified.json` (canonical metadata for all 42). Generated 2026-10-19. Two identifier corrections applied during verification (DataTales, Idyll) — logged in §2.4.
