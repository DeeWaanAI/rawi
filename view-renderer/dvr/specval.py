#!/usr/bin/env python3
"""dvr/1.0 grammar validator — spec §2. Fail loud, never guess."""
KINDS = {"table", "list", "tree", "deck"}
ROLES = {"value", "label", "claim", "structure"}
NODE_KEYS = {"id", "role", "binding_ref", "column", "row_key", "path", "slide",
             "slot", "text", "editable", "children"}
VIEW_KEYS = {"spec", "id", "kind", "title", "columns", "nodes"}
# data-bearing literals forbidden on nodes (spec §2.3 rule 3)
FORBIDDEN_NODE_KEYS = {"value", "data", "number", "amount", "result"}


class SpecError(ValueError):
    pass


def validate_view(view: dict, known_binding_ids=None) -> dict:
    """Validate a view spec. Returns the view unchanged if valid; raises SpecError otherwise.
    known_binding_ids: optional set of existing binding ids for reference checking."""
    unknown = set(view) - VIEW_KEYS
    if unknown:
        raise SpecError(f"unknown view keys: {sorted(unknown)}")
    if view.get("spec") != "dvr/1.0":
        raise SpecError(f"spec must be 'dvr/1.0', got {view.get('spec')!r}")
    vid = view.get("id", "")
    if not (isinstance(vid, str) and vid.startswith("v_")):
        raise SpecError(f"view id must start with 'v_', got {vid!r}")
    if view.get("kind") not in KINDS:
        raise SpecError(f"kind must be one of {sorted(KINDS)}, got {view.get('kind')!r}")
    if view["kind"] == "table" and "columns" not in view:
        raise SpecError("kind=table requires columns[]")

    nodes = view.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        raise SpecError("nodes must be a non-empty list")

    seen = set()
    for n in nodes:
        nid = n.get("id")
        if not nid:
            raise SpecError("node missing id")
        if nid in seen:
            raise SpecError(f"duplicate node id: {nid}")
        seen.add(nid)

        unknown = set(n) - NODE_KEYS
        if unknown & FORBIDDEN_NODE_KEYS:
            raise SpecError(f"node {nid}: embedded data values forbidden: {sorted(unknown & FORBIDDEN_NODE_KEYS)}")
        if unknown:
            raise SpecError(f"node {nid}: unknown keys: {sorted(unknown)}")

        role = n.get("role")
        if role not in ROLES:
            raise SpecError(f"node {nid}: role must be one of {sorted(ROLES)}, got {role!r}")

        has_ref = "binding_ref" in n
        if role in ("value", "claim") and not has_ref:
            raise SpecError(f"node {nid}: role={role} requires binding_ref")
        if role in ("label", "structure") and has_ref:
            raise SpecError(f"node {nid}: role={role} must not carry binding_ref")

        if role == "claim" and n.get("editable"):
            raise SpecError(f"node {nid}: claim nodes are never editable")
        if n.get("editable") and role != "value":
            raise SpecError(f"node {nid}: only value nodes may be editable")

        if has_ref and known_binding_ids is not None and n["binding_ref"] not in known_binding_ids:
            raise SpecError(f"node {nid}: binding_ref {n['binding_ref']!r} does not resolve to an existing binding")

    return view
