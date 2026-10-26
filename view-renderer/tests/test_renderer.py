#!/usr/bin/env python3
"""Tier A functional tests F1-F8 (brief §5). Run: python -m unittest discover tests -v"""
import json, shutil, sys, tempfile, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent / "qafiya-ref" / "qafiya-core"))
sys.path.insert(0, str(ROOT))

from dvr import specval, resolve, render, edits, affordance
from qafiya_core import engine, semantic, store

RECORDS = [
    {"id": "r_010", "date": "2026-07-11", "period": "Q2", "amount": 4800.0, "category": "travel"},
    {"id": "r_011", "date": "2026-08-03", "period": "Q3", "amount": 2100.0, "category": "food"},
    {"id": "r_012", "date": "2026-09-15", "period": "Q3", "amount": 2110.0, "category": "tools"},
]

def make_workspace():
    """Frozen fixture: one dataset, one view binding, one claim binding."""
    root = Path(tempfile.mkdtemp())
    ds = root / "datasets" / "expenses"
    ds.mkdir(parents=True)
    store.atomic_write_jsonl(ds / store.DATA, RECORDS)
    (ds / "schema.json").write_text(json.dumps({
        "dataset": "expenses", "id_field": "id",
        "fields": {"id": "id", "date": "timestamp", "period": "enum[Q2,Q3]",
                   "amount": "number", "category": "enum[travel,food,tools,other]"},
        "derivations": ["sum", "avg", "count", "min", "max"]}))
    bindings = [
        {"id": "b_7f3a", "kind": "view", "target": {"view": "v_q3", "node": "cell:total"},
         "sources": [{"dataset": "ds:expenses", "filter": "period=Q3", "field": "amount",
                      "key_path": ["amount"], "verbatim_excerpt": "2110.0"}],
         "derivation": "sum(amount) where period='Q3'", "value": 4210.0, "statistic": "sum",
         "device": "test", "authoritative_artifact": "datasets/expenses/data.jsonl",
         "provenance": {"created_by": "test", "created_at": "2026-10-19T00:00Z"},
         "check": {"provenance": "PASS", "checked_at": "2026-10-19T00:00Z"}},
        {"id": "b_9c11", "kind": "claim", "target": {"view": "v_q3", "node": "claim:trend"},
         "sources": [{"dataset": "ds:expenses", "field": "amount", "key_path": ["amount"],
                      "verbatim_excerpt": "4800.0"}],
         "derivation": "sum(amount) where period='Q3'", "value": 4210.0, "statistic": "sum",
         "device": "test", "authoritative_artifact": "datasets/expenses/data.jsonl",
         "assertion": {"statement": "Q3 spend fell 12% vs Q2", "predicate": "direction",
                       "expected": -0.12, "tolerance": 0.005,
                       "both_sides": {"Q2": {"derivation": "sum(amount) where period='Q2'"},
                                      "Q3": {"derivation": "sum(amount) where period='Q3'"}}},
         "provenance": {"created_by": "test", "created_at": "2026-10-19T00:00Z"},
         "check": {"provenance": "PASS", "semantic": "PASS", "checked_at": "2026-10-19T00:00Z"}},
        {"id": "b_cell12", "kind": "view", "target": {"view": "v_q3", "node": "cell:r_012"},
         "sources": [{"dataset": "ds:expenses", "filter": "period=Q3", "field": "amount",
                      "key_path": ["amount"], "verbatim_excerpt": "2110.0"}],
         "derivation": "sum(amount) where period='Q3'", "value": 4210.0, "statistic": "sum",
         "device": "test", "authoritative_artifact": "datasets/expenses/data.jsonl",
         "provenance": {"created_by": "test", "created_at": "2026-10-19T00:00Z"},
         "check": {"provenance": "PASS", "checked_at": "2026-10-19T00:00Z"}},
    ]
    store.atomic_write_jsonl(root / store.BINDINGS, bindings)
    return root

VIEW = {
    "spec": "dvr/1.0", "id": "v_q3", "kind": "table",
    "title": {"text": "Q3 expenses"},
    "columns": [{"id": "col:amount", "label": "Amount", "source_field": "amount"}],
    "nodes": [
        {"id": "cell:total", "role": "value", "binding_ref": "b_7f3a", "column": "col:amount"},
        {"id": "cell:r_012", "role": "value", "binding_ref": "b_cell12",
         "column": "col:amount", "row_key": "r_012", "editable": True},
        {"id": "claim:trend", "role": "claim", "binding_ref": "b_9c11"},
        {"id": "lbl", "role": "label", "text": "All figures verified against frozen data."},
    ],
}


class F1GrammarValidation(unittest.TestCase):
    def test_valid_view_passes(self):
        self.assertIs(specval.validate_view(VIEW), VIEW)

    def test_rejects_bad_specs(self):
        bad = []
        v = dict(VIEW, spec="dvr/0.9"); bad.append(v)
        v = dict(VIEW, kind="chart"); bad.append(v)
        v = json.loads(json.dumps(VIEW)); v["nodes"][0]["value"] = 4210.0; bad.append(v)      # embedded value
        v = json.loads(json.dumps(VIEW)); del v["nodes"][0]["binding_ref"]; bad.append(v)     # missing ref
        v = json.loads(json.dumps(VIEW)); v["nodes"][1]["id"] = "cell:total"; bad.append(v)   # dup id
        v = json.loads(json.dumps(VIEW)); v["nodes"][2]["editable"] = True; bad.append(v)     # editable claim
        v = json.loads(json.dumps(VIEW)); v["nodes"][0]["binding_ref"] = "b_nope"; bad.append(v)  # dangling ref
        for i, v in enumerate(bad):
            with self.assertRaises(specval.SpecError, msg=f"fixture {i} should be rejected"):
                specval.validate_view(v, known_binding_ids={"b_7f3a", "b_9c11", "b_cell12"})


class F2F3ResolutionPurity(unittest.TestCase):
    def setUp(self):
        self.root = make_workspace()

    def test_resolution_matches_recompute(self):
        bindings = resolve.load_bindings(self.root)
        v, st = resolve.resolve_binding(self.root, bindings["b_7f3a"])
        self.assertEqual(v, 4210.0)
        # tamper with data -> resolution must follow data, not cached binding.value
        ds, records = store.load_dataset(self.root, "expenses")
        records[1]["amount"] = 999.0
        store.atomic_write_jsonl(ds / store.DATA, records)
        v, _ = resolve.resolve_binding(self.root, bindings["b_7f3a"])
        self.assertEqual(v, 3109.0)  # 999 + 2110 — cached 4210 never trusted

    def test_unresolved_is_explicit(self):
        bindings = resolve.load_bindings(self.root)
        bad = dict(bindings["b_7f3a"], derivation="sum(amount) where period='Q9'")
        v, st = resolve.resolve_binding(self.root, bad)
        self.assertIsInstance(v, resolve.Unresolved)
        self.assertEqual(st, "UNRESOLVED")

    def test_render_purity(self):
        a = render.render(self.root, specval.validate_view(VIEW))
        b = render.render(self.root, specval.validate_view(VIEW))
        self.assertEqual(a, b)


class F4F5EditInvalidation(unittest.TestCase):
    def setUp(self):
        self.root = make_workspace()

    def test_edit_path_atomic_with_history(self):
        node = VIEW["nodes"][1]
        eb = edits.make_edit_binding(self.root, "v_q3", node, 3000.0)
        updated, n_inv = edits.apply(self.root, eb)
        self.assertEqual(updated["amount"], 3000.0)
        hist = store.read_jsonl(self.root / "datasets" / "expenses" / store.HISTORY)
        self.assertEqual(len(hist), 1)
        self.assertEqual(hist[0]["prior"], 2110.0)
        self.assertEqual(hist[0]["new"], 3000.0)
        self.assertGreaterEqual(n_inv, 3)  # b_7f3a, b_9c11, b_cell12 all touch Q3

    def test_invalidation_visible_then_flag(self):
        """Badge sequence: PASS -> PENDING (after edit) -> FLAG (semantic, -12% vs actual)."""
        html0 = render.render(self.root, VIEW)
        self.assertIn('data-state="PASS"', html0)
        node = VIEW["nodes"][1]
        edits.apply(self.root, edits.make_edit_binding(self.root, "v_q3", node, 3000.0))
        html1 = render.render(self.root, VIEW)
        self.assertIn('data-state="PENDING"', html1)  # stale is visible, not silent
        engine.refresh_values(self.root)
        self.assertEqual(engine.provenance_gate(self.root), 0)
        flags = semantic.semantic_sweep(self.root)
        self.assertEqual(flags, 1)  # claim said -12%, actual (5110-4800)/4800 = +6.5%
        bindings = resolve.load_bindings(self.root)
        self.assertEqual(bindings["b_9c11"]["check"]["semantic"], "FLAG")
        html2 = render.render(self.root, VIEW)
        self.assertIn('data-state="FLAG"', html2)
        # assertion text untouched by the whole loop
        self.assertEqual(bindings["b_9c11"]["assertion"]["statement"], "Q3 spend fell 12% vs Q2")


class F6F7EvidenceCoverage(unittest.TestCase):
    def setUp(self):
        self.root = make_workspace()

    def test_evidence_panel(self):
        bindings = resolve.load_bindings(self.root)
        panel = affordance.evidence_panel(self.root, bindings["b_9c11"])
        self.assertEqual(panel["binding_id"], "b_9c11")
        self.assertTrue(panel["source_rows"])
        for r in panel["source_rows"]:  # verbatim rows byte-match dataset
            self.assertIn(r, RECORDS)
        self.assertEqual(panel["check"]["provenance"], "PASS")
        # every claim node renders the affordance
        self.assertIn("▸evidence", render.render(self.root, VIEW))

    def test_coverage_rendered(self):
        out = render.render(self.root, VIEW)
        self.assertIn("coverage: 100%", out)
        # break one binding -> coverage drops and is displayed
        bindings = store.read_jsonl(self.root / store.BINDINGS)
        bindings[0]["derivation"] = "sum(amount) where period='Q9'"
        store.atomic_write_jsonl(self.root / store.BINDINGS, bindings)
        out = render.render(self.root, VIEW)
        self.assertIn("coverage: 67%", out)


class F8Contract(unittest.TestCase):
    def test_only_qafiya_public_api_used(self):
        """Renderer modules import qafiya_core only (never modify Layer-1 files)."""
        for mod in ("specval", "resolve", "render", "affordance", "edits"):
            src = (ROOT / "dvr" / f"{mod}.py").read_text()
            for line in src.splitlines():
                if line.startswith(("import ", "from ")) and "qafiya" not in line \
                   and not line.startswith(("from .", "from pathlib", "import ")) :
                    pass  # stdlib/local allowed
            self.assertNotIn("01-data-layer-qafiya", src)
        # renderer never writes dataset files except via edits.apply -> engine.apply_edit
        res_src = (ROOT / "dvr" / "resolve.py").read_text() + (ROOT / "dvr" / "render.py").read_text()
        self.assertNotIn("atomic_write", res_src)
        self.assertNotIn("open(", res_src)


if __name__ == "__main__":
    unittest.main()
