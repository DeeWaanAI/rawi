#!/usr/bin/env python3
"""Resolution — spec §3. Every displayed value is recomputed from current data
via qafiya-core derivations.evaluate. binding.value is never printed without
recompute. Unresolvable bindings produce an explicit UNRESOLVED state."""
from pathlib import Path

from qafiya_core import derivations, store


class Unresolved:
    """Marker: rendered visibly, never silently (spec §3.3, invariant 8)."""
    def __init__(self, reason):
        self.reason = reason
    def __repr__(self):
        return f"Unresolved({self.reason})"


def load_bindings(root: Path):
    return {b["id"]: b for b in store.read_jsonl(root / store.BINDINGS)}


def resolve_binding(root: Path, binding: dict):
    """Recompute the binding's derivation over current data.
    Returns (value_or_Unresolved, state)."""
    if not binding.get("derivation"):
        return Unresolved("binding has no derivation"), "UNRESOLVED"
    artifact = binding.get("authoritative_artifact", "")
    if artifact and artifact in store.superseded_set(root):
        return Unresolved(f"quarantined source: {artifact}"), "UNRESOLVED"
    try:
        dataset = binding["sources"][0]["dataset"].removeprefix("ds:")
        _, records = store.load_dataset(root, dataset)
        value = derivations.evaluate(binding["derivation"], records)
    except (KeyError, IndexError) as e:
        return Unresolved(f"missing source: {e}"), "UNRESOLVED"
    except derivations.DerivationError as e:
        return Unresolved(str(e)), "UNRESOLVED"
    state = (binding.get("check") or {}).get("provenance", "PENDING")
    return value, state


def check_state(binding: dict) -> str:
    """Badge state for a node: semantic FLAG outranks provenance for claims."""
    chk = binding.get("check") or {}
    prov = chk.get("provenance", "PENDING")
    sem = chk.get("semantic")
    if binding.get("kind") == "claim" and sem == "FLAG":
        return "FLAG"
    return prov


def coverage(resolved_nodes) -> float:
    """Share of data-bearing nodes that resolved AND passed Layer 1 (spec §3.5)."""
    data_nodes = [n for n in resolved_nodes if n["role"] in ("value", "claim")]
    if not data_nodes:
        return 1.0
    ok = sum(1 for n in data_nodes if n["resolved_ok"] and n["state"] == "PASS")
    return ok / len(data_nodes)
