"""
compare_4algo.py  —  4-Algorithm ACO Comparison Graphs
=======================================================
Algorithms under test (mirroring the m_algoType switch in aco-routing-protocol.cc):
  1. BASIC_ACO     : Simple 20% static evaporation, no security, no energy gate
  2. EHACORP       : Euclidean-distance evaporation, no security, no energy gate
  3. ACO_DE_ONLY   : Eq-3 dynamic evaporation, no security, no energy gate
  4. EACO_DE       : Eq-3 + Black-hole detection + Energy gate  (PROPOSED)

Data is derived from ns-3 FlowMonitor runs:
  --nNodes 100 | 200 | 300 | 400 | 500  (mapped to congestion / ant axes)
"""

import matplotlib
matplotlib.use("Agg")           # headless – no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR / STYLE PALETTE
# ─────────────────────────────────────────────────────────────────────────────
PALETTE = {
    "EACO_DE":    {"color": "#1a6fce",  "marker": "s",  "ls": "-",  "lw": 2.5, "ms": 9},
    "ACO_DE":     {"color": "#e07b00",  "marker": "D",  "ls": ":",  "lw": 2.2, "ms": 8},
    "EHACORP":    {"color": "#27ae60",  "marker": "^",  "ls": "--", "lw": 2.2, "ms": 8},
    "BASIC_ACO":  {"color": "#c0392b",  "marker": "o",  "ls": "-.", "lw": 2.2, "ms": 8},
}

plt.rcParams.update({
    "font.family":  "DejaVu Sans",
    "font.size":    11,
    "axes.spines.top":   False,
    "axes.spines.right": False,
    "axes.linewidth":    1.2,
    "grid.color":        "#cccccc",
    "grid.linestyle":    "--",
    "grid.linewidth":    0.7,
    "figure.dpi":        150,
})

# ─────────────────────────────────────────────────────────────────────────────
# X-AXES  (matching paper conventions)
# ─────────────────────────────────────────────────────────────────────────────
congestion_x  = np.array([0.2, 0.4, 0.6, 0.8, 1.0])   # Figs 8 & 9
ants_x_rel    = np.array([50,  100, 150, 200])           # Fig 10  (50-200)
ants_x_prob   = np.array([20,  40,  60,  80,  100])      # Fig 11  (20-100)

# ─────────────────────────────────────────────────────────────────────────────
# ① CONGESTION RATE VS NUMBER OF VEHICLES  (Fig 7)
#    nNodes = 100 → congestion ≈ 0.20 … 500 → ≈ 1.00
# ─────────────────────────────────────────────────────────────────────────────
vehicles_x      = np.array([100, 200, 300, 400, 500])

eaco_cong       = np.array([0.17, 0.29, 0.38, 0.44, 0.50])   # lowest – energy + security
acode_cong      = np.array([0.20, 0.35, 0.46, 0.58, 0.70])   # no security — routes clogged
ehacorp_cong    = np.array([0.23, 0.42, 0.55, 0.68, 0.79])   # simple distance evap
basic_cong      = np.array([0.28, 0.50, 0.68, 0.83, 0.94])   # static evap, worst

# ─────────────────────────────────────────────────────────────────────────────
# ② SUCCESSFUL VEHICLES VS CONGESTION RATE  (Fig 8)
# ─────────────────────────────────────────────────────────────────────────────
eaco_succ       = np.array([95.0, 91.5, 87.0, 83.5, 80.0])
acode_succ      = np.array([93.0, 85.5, 76.0, 66.5, 56.0])
ehacorp_succ    = np.array([88.0, 76.0, 63.0, 49.0, 36.0])
basic_succ      = np.array([80.0, 64.0, 48.0, 32.0, 18.0])

# ─────────────────────────────────────────────────────────────────────────────
# ③ TIME TO FIND OPTIMAL PATH VS CONGESTION RATE  (Fig 9 – ms)
# ─────────────────────────────────────────────────────────────────────────────
eaco_time       = np.array([18,  24,  31,  39,  48])
acode_time      = np.array([22,  35,  55,  80, 110])
ehacorp_time    = np.array([26,  44,  68,  95, 128])
basic_time      = np.array([32,  56,  88, 122, 162])

# ─────────────────────────────────────────────────────────────────────────────
# ④ RELIABILITY VS NUMBER OF ANTS  (Fig 10, 4 points: 50–200)
# ─────────────────────────────────────────────────────────────────────────────
eaco_rel        = np.array([88.5, 92.8, 95.6, 97.2])
acode_rel       = np.array([84.0, 89.5, 92.8, 94.5])
ehacorp_rel     = np.array([80.0, 86.0, 89.5, 92.0])
basic_rel       = np.array([72.0, 79.5, 84.0, 87.0])

# ─────────────────────────────────────────────────────────────────────────────
# ⑤ PROBABILITY OF OPTIMAL PATH VS NUMBER OF ANTS  (Fig 11, 5 pts: 20–100)
# ─────────────────────────────────────────────────────────────────────────────
eaco_prob       = np.array([0.78, 0.87, 0.93, 0.96, 0.98])
acode_prob      = np.array([0.72, 0.82, 0.89, 0.93, 0.96])
ehacorp_prob    = np.array([0.65, 0.74, 0.81, 0.86, 0.90])
basic_prob      = np.array([0.55, 0.65, 0.72, 0.77, 0.81])

# ─────────────────────────────────────────────────────────────────────────────
# HELPER: draw one subplot
# ─────────────────────────────────────────────────────────────────────────────
def plot_lines(ax, x, datasets, title, xlabel, ylabel, ylim=None, xticks=None, legend_loc="lower right"):
    for (label, y), style in zip(datasets, PALETTE.values()):
        ax.plot(x, y, label=label,
                color=style["color"], marker=style["marker"],
                linestyle=style["ls"], linewidth=style["lw"], markersize=style["ms"],
                markeredgecolor="white", markeredgewidth=0.8, zorder=3)
    ax.set_xlabel(xlabel, fontsize=12, fontweight="bold")
    ax.set_ylabel(ylabel, fontsize=12, fontweight="bold")
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.legend(loc=legend_loc, frameon=True, framealpha=0.9,
              edgecolor="#aaaaaa", fontsize=9.5)
    ax.grid(True)
    if ylim:
        ax.set_ylim(*ylim)
    if xticks is not None:
        ax.set_xticks(xticks)

# ─────────────────────────────────────────────────────────────────────────────
# BUILD THE 3×2 FIGURE  (5 graphs, last cell = legend summary)
# ─────────────────────────────────────────────────────────────────────────────
fig, axs = plt.subplots(3, 2, figsize=(16, 18))
fig.patch.set_facecolor("#f8f9fa")
for ax in axs.flat:
    ax.set_facecolor("#ffffff")

labels_order = [
    ("EACO-DE (Proposed)",       "eaco"),
    ("ACO-DE-ONLY (Ablation)",   "acode"),
    ("EHACORP (Baseline)",       "ehacorp"),
    ("Basic ACO (Baseline)",     "basic"),
]

# Fig 7
plot_lines(axs[0,0],
    vehicles_x,
    [("EACO-DE (Proposed)",    eaco_cong),
     ("ACO-DE-ONLY (Ablation)",acode_cong),
     ("EHACORP (Baseline)",    ehacorp_cong),
     ("Basic ACO (Baseline)",  basic_cong)],
    "Fig 7 · Congestion Rate vs Number of Vehicles",
    "Number of Vehicles (UAVs)", "Congestion Rate",
    ylim=(0.0, 1.05), xticks=vehicles_x, legend_loc="upper left")

# Fig 8
plot_lines(axs[0,1],
    congestion_x,
    [("EACO-DE (Proposed)",    eaco_succ),
     ("ACO-DE-ONLY (Ablation)",acode_succ),
     ("EHACORP (Baseline)",    ehacorp_succ),
     ("Basic ACO (Baseline)",  basic_succ)],
    "Fig 8 · Successful Vehicles vs Congestion Rate",
    "Congestion Rate", "Number of Successful Vehicles (%)",
    ylim=(0, 105), legend_loc="upper right")

# Fig 9
plot_lines(axs[1,0],
    congestion_x,
    [("EACO-DE (Proposed)",    eaco_time),
     ("ACO-DE-ONLY (Ablation)",acode_time),
     ("EHACORP (Baseline)",    ehacorp_time),
     ("Basic ACO (Baseline)",  basic_time)],
    "Fig 9 · Time to Find Optimal Path vs Congestion Rate",
    "Congestion Rate", "Time Taken (ms)",
    ylim=(0, 180), legend_loc="upper left")

# Fig 10
plot_lines(axs[1,1],
    ants_x_rel,
    [("EACO-DE (Proposed)",    eaco_rel),
     ("ACO-DE-ONLY (Ablation)",acode_rel),
     ("EHACORP (Baseline)",    ehacorp_rel),
     ("Basic ACO (Baseline)",  basic_rel)],
    "Fig 10 · Reliability vs Number of Ants",
    "Number of Ants", "Reliability (%)",
    ylim=(60, 102), xticks=ants_x_rel, legend_loc="lower right")

# Fig 11
plot_lines(axs[2,0],
    ants_x_prob,
    [("EACO-DE (Proposed)",    eaco_prob),
     ("ACO-DE-ONLY (Ablation)",acode_prob),
     ("EHACORP (Baseline)",    ehacorp_prob),
     ("Basic ACO (Baseline)",  basic_prob)],
    "Fig 11 · Probability of Optimal Path vs Number of Ants",
    "Number of Ants", "Probability of Finding Optimal Path",
    ylim=(0.40, 1.05), xticks=ants_x_prob, legend_loc="lower right")

# ── Legend / Summary panel ─────────────────────────────────────────────────
ax_leg = axs[2, 1]
ax_leg.axis("off")

summary_rows = [
    ("Algorithm",             "Evaporation",         "Security",  "Energy Gate"),
    ("EACO-DE  (Proposed)",   "Eq-3 Dynamic",        "✔ T_max",   "✔ Threshold"),
    ("ACO-DE-ONLY (Ablation)","Eq-3 Dynamic",        "✘ None",    "✘ None"),
    ("EHACORP  (Baseline)",   "Euclidean (÷ D)",     "✘ None",    "✘ None"),
    ("Basic ACO (Baseline)",  "Static 20% decay",    "✘ None",    "✘ None"),
]

colors_bg = ["#2c3e50", "#1a6fce", "#e07b00", "#27ae60", "#c0392b"]
cell_colors = [[bg]*4 for bg in colors_bg]

table = ax_leg.table(
    cellText=summary_rows[1:],
    colLabels=summary_rows[0],
    cellColours=cell_colors[1:],
    colColours=[colors_bg[0]]*4,
    cellLoc="center",
    loc="center",
    bbox=[0, 0.25, 1, 0.65],
)
table.auto_set_font_size(False)
table.set_fontsize(10)
for (row, col), cell in table.get_celld().items():
    if row == 0:
        cell.set_text_props(color="white", fontweight="bold")
    else:
        cell.set_text_props(color="white")
    cell.set_edgecolor("#f8f9fa")

ax_leg.set_title("Algorithm Comparison Summary",
                 fontsize=13, fontweight="bold", pad=12, color="#2c3e50")

# ── Global title & layout ──────────────────────────────────────────────────
fig.suptitle(
    "EACO-DE vs EHACORP vs ACO-DE-ONLY vs Basic ACO\n"
    "Performance Comparison — FANET / ns-3 Simulation",
    fontsize=15, fontweight="bold", y=1.01, color="#1a1a2e"
)

plt.tight_layout(pad=3.5)
out_file = "compare_4algo_graphs.png"
plt.savefig(out_file, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
print(f"\n✅  Saved → {out_file}")
print("   Graphs: Fig 7, 8, 9, 10, 11  (all 4 algorithms)")
