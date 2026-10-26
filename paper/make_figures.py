#!/usr/bin/env python3
"""Paper figures: fig1 architecture, fig2 E1 timeline, fig3 E3 cost, fig4 L4 scale."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

EXP = Path(__file__).resolve().parent.parent / "experiments"
OUT = Path(__file__).resolve().parent / "figures"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"font.size": 10, "figure.dpi": 150})

# ---- fig1: architecture ----
fig, ax = plt.subplots(figsize=(7.2, 3.4)); ax.axis("off")
def box(x, y, w, h, label, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                fc=fc, ec="#333", lw=0.8))
    ax.text(x + w/2, y + h/2, label, ha="center", va="center", fontsize=9)
def arrow(x1, y1, x2, y2, label=""):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=12, color="#333", lw=1))
    if label:
        ax.text((x1+x2)/2, (y1+y2)/2 + 0.05, label, ha="center", fontsize=7.5, color="#333")
box(0.02, 0.62, 0.20, 0.24, "LLM\n(emits spec + bindings once)", "#e8eefc")
box(0.30, 0.62, 0.22, 0.24, "View spec (dvr/1.0)\nnodes carry binding_ref", "#e8eefc")
box(0.60, 0.62, 0.18, 0.24, "Rawi renderer\n(pure function)", "#dcf2e3")
box(0.84, 0.62, 0.14, 0.24, "User sees:\nview + badges\n+ ▸evidence", "#dcf2e3")
box(0.30, 0.12, 0.22, 0.24, "Qafiya bindings\n(view / claim / edit)", "#fdf0dc")
box(0.60, 0.12, 0.18, 0.24, "Frozen datasets\n(history.jsonl)", "#fdf0dc")
box(0.84, 0.12, 0.14, 0.24, "Two-layer check\nproof / flag", "#fbdedd")
arrow(0.22, 0.74, 0.30, 0.74)
arrow(0.52, 0.74, 0.60, 0.74)
arrow(0.78, 0.74, 0.84, 0.74)
arrow(0.41, 0.62, 0.41, 0.36, "resolves")
arrow(0.52, 0.24, 0.60, 0.24)
arrow(0.78, 0.24, 0.84, 0.24)
arrow(0.91, 0.62, 0.91, 0.36, "edit binding")
ax.set_xlim(0, 1); ax.set_ylim(0, 1)
fig.savefig(OUT / "fig1_architecture.pdf", bbox_inches="tight"); plt.close(fig)

# ---- fig2: E1 durability timeline ----
trace = [json.loads(l) for l in open(EXP / "results" / "raw" / "e1_trace.jsonl")]
steps = ["Baseline\n(all PASS)", "Edit r_051\n820.89→1320.89", "Invalidation\n(4 → PENDING)", "Re-check\n(trend → FLAG)"]
colors = ["#4ade80", "#4ade80", "#9ca3af", "#fbbf24"]
fig, ax = plt.subplots(figsize=(7.2, 1.9))
for i, (s, c) in enumerate(zip(steps, colors)):
    ax.scatter(i, 0, s=900, c=c, zorder=3, edgecolors="#333")
    ax.text(i, -0.55, s, ha="center", va="top", fontsize=9)
    if i < 3:
        ax.annotate("", xy=(i+0.72, 0), xytext=(i+0.28, 0),
                    arrowprops=dict(arrowstyle="-|>", color="#333"))
ax.set_xlim(-0.5, 3.5); ax.set_ylim(-1.6, 0.8); ax.axis("off")
fig.savefig(OUT / "fig2_e1_timeline.pdf", bbox_inches="tight"); plt.close(fig)

# ---- fig3: E3 token cost (log scale) ----
e3 = json.loads((EXP / "results" / "raw" / "e3_counts.json").read_text())
fig, ax = plt.subplots(figsize=(4.6, 2.8))
vals = [e3["dvr"]["T_total"], e3["regen"]["T_total"]]
bars = ax.bar(["Rawi (spec once,\n100 interactions local)", "Generative UI\n(regenerate per interaction)"],
              vals, color=["#4ade80", "#f87171"], edgecolor="#333")
ax.set_yscale("log"); ax.set_ylabel("model tokens (log)")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v*1.15, f"{v:,}", ha="center", fontsize=9)
ax.set_title(f"100 interactions — {e3['ratio']}× fewer tokens", fontsize=10)
fig.tight_layout(); fig.savefig(OUT / "fig3_cost.pdf"); plt.close(fig)

# ---- fig4: L4 scale curve ----
lim = json.loads((EXP.parent / "view-renderer" / "limits_results.json").read_text())
curve = lim["L4_scale"]["curve"]
fig, ax = plt.subplots(figsize=(4.6, 2.8))
ax.plot([c["nodes"] for c in curve], [c["render_s"] for c in curve], "o-", color="#25406e")
ax.set_xscale("log"); ax.set_yscale("log")
ax.axhline(1.0, ls="--", color="#f87171", lw=1)
ax.text(12, 1.15, "1 s interactive threshold", fontsize=8, color="#f87171")
ax.set_xlabel("nodes per view (log)"); ax.set_ylabel("render time, s (log)")
ax.set_title("Scale ceiling of the naive resolver", fontsize=10)
fig.tight_layout(); fig.savefig(OUT / "fig4_scale.pdf"); plt.close(fig)

print("figures:", [p.name for p in OUT.iterdir()])
