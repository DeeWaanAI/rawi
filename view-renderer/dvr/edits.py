#!/usr/bin/env python3
"""Edits — spec §5. A UI edit NEVER mutates data directly: it produces an
`edit` binding handed to qafiya_core.engine.apply_edit, which guarantees
atomic write-back, history, and transitive invalidation."""
import uuid
from datetime import datetime, timezone
from pathlib import Path

from qafiya_core import engine, store


def make_edit_binding(root: Path, view_id: str, node: dict, new_value) -> dict:
    """Build the edit binding for a user edit on an editable value node."""
    if not node.get("editable") or node.get("role") != "value":
        raise ValueError(f"node {node.get('id')} is not editable")
    bindings = {b["id"]: b for b in store.read_jsonl(root / store.BINDINGS)}
    src = bindings[node["binding_ref"]]
    s0 = src["sources"][0]
    record_id = node.get("row_key")
    if not record_id:
        raise ValueError(f"node {node['id']}: editable value nodes require row_key")
    field = (node.get("column_source_field") or s0.get("field")
             or s0.get("key_path", [None])[0])
    if not field:
        raise ValueError(f"node {node['id']}: cannot determine writeback field")
    return {
        "id": "b_" + uuid.uuid4().hex[:8],
        "kind": "edit",
        "target": {"view": view_id, "node": node["id"]},
        "sources": [],
        "writeback": {
            "dataset": s0["dataset"], "record_id": record_id,
            "field": field, "op": "set", "value": new_value,
        },
        "provenance": {
            "created_by": "dvr/1.0",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        },
    }


def apply(root: Path, edit_binding: dict):
    """Persist the edit binding, apply via qafiya-core (atomic + invalidate)."""
    bindings = store.read_jsonl(root / store.BINDINGS)
    bindings.append(edit_binding)
    store.atomic_write_jsonl(root / store.BINDINGS, bindings)
    return engine.apply_edit(root, edit_binding)  # (updated_record, n_invalidated)
