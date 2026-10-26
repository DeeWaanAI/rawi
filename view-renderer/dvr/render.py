#!/usr/bin/env python3
"""Renderer — spec §3. Pure function: (spec, bindings, datasets) -> HTML.
Byte-identical output under unchanged inputs (invariant 3)."""
import html
from pathlib import Path

from . import resolve

BADGE = {"PASS": "✓", "FAIL": "✗", "FLAG": "⚠", "PENDING": "…", "UNRESOLVED": "◌"}


def _fmt(v):
    if isinstance(v, resolve.Unresolved):
        return f"[unresolved: {html.escape(v.reason)}]"
    if isinstance(v, float) and v == int(v):
        return str(int(v))
    return html.escape(str(v))


def _badge(state):
    return f'<span class="badge badge-{state.lower()}">{BADGE.get(state, "?")} {state}</span>'


def _node_html(root, node, bindings):
    role = node["role"]
    if role in ("label", "structure"):
        return html.escape(node.get("text", "")), "", None
    b = bindings[node["binding_ref"]]
    value, rstate = resolve.resolve_binding(root, b)
    state = "UNRESOLVED" if isinstance(value, resolve.Unresolved) else resolve.check_state(b)
    if rstate == "UNRESOLVED":
        state = "UNRESOLVED"
    body = _fmt(value)
    if role == "claim":
        text = (b.get("assertion") or {}).get("statement", "")
        body = (f'{html.escape(text)} <button class="evidence" '
                f'data-binding="{b["id"]}">▸evidence</button>')
    if node.get("editable"):
        body += f' <span class="editable" data-node="{node["id"]}">✎</span>'
    return body, state, (role in ("value", "claim") and not isinstance(value, resolve.Unresolved) and state == "PASS")


def render(root: Path, view: dict) -> str:
    """Render a validated view to HTML. Pure: no mutation, no clock, no randomness."""
    bindings = resolve.load_bindings(root)
    parts = []
    resolved_ok = []
    nodes_out = []
    for node in view["nodes"]:
        body, state, ok = _node_html(root, node, bindings)
        nodes_out.append({"id": node["id"], "role": node["role"], "state": state,
                          "resolved_ok": bool(ok)})
        resolved_ok.append(node["role"] in ("value", "claim") and ok)
        parts.append(f'<div class="node" data-node="{node["id"]}" data-state="{state}">'
                     f'{body} {_badge(state) if state else ""}</div>')
    cov = resolve.coverage(nodes_out)
    title = html.escape((view.get("title") or {}).get("text", view["id"]))
    return (f'<section class="view" data-view="{view["id"]}" data-kind="{view["kind"]}">'
            f'<h2>{title}</h2>{"".join(parts)}'
            f'<footer class="coverage">coverage: {cov:.0%}</footer></section>')
