#!/usr/bin/env python3
"""Generate all figures for the LaTeX report."""
import csv, os
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrowPatch
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "DejaVu Serif",
    "font.size": 10,
    "axes.titlesize": 11,
    "axes.labelsize": 10,
    "legend.fontsize": 9,
    "figure.dpi": 150,
    "savefig.bbox": "tight",
    "savefig.dpi": 200,
})

OUT = "/sessions/great-beautiful-albattani/mnt/outputs/latex/figs"
SUMO = "/sessions/great-beautiful-albattani/mnt/outputs/sumo_runs"

# Load 12 scenarios results
RESULTS = {}
with open(f"{SUMO}/all_results.csv") as f:
    for row in csv.DictReader(f):
        RESULTS[(row["period"], row["scenario"])] = row

SCENARIOS_PEAK = [("base","Base"), ("vsl","VSL\n(in-sec)"), ("vsl_up","VSL$_\\mathrm{up}$"),
                  ("rm","RM"), ("vsl_rm","VSL+RM"), ("vsl_up_rm","VSL$_\\mathrm{up}$+RM")]
SCENARIOS_OFF  = SCENARIOS_PEAK
COLORS = {
    "base":"#5b6770", "vsl":"#e0876b", "vsl_up":"#a86a4d",
    "rm":"#3a8c5e", "vsl_rm":"#7a4a4a", "vsl_up_rm":"#5a4a8a",
}

def get(period, scen, key):
    return float(RESULTS[(period, scen)][key])

# -------------------------------------------------------------------
# Figure 1 - AYE network schematic (matplotlib version)
# -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 3.4))

def lane_box(ax, x, y, w, h, color="#cfd8dc", label=None, lw=1.2):
    r = Rectangle((x,y), w, h, facecolor=color, edgecolor="#37474f", linewidth=lw)
    ax.add_patch(r)
    if label:
        ax.text(x+w/2, y+h/2, label, ha="center", va="center", fontsize=9, fontweight="bold")

# Mainline (2 segments + weaving)
# E_main_in: x = 0..360
lane_box(ax, 0,    1.2, 360, 0.6, color="#bbdefb", label="E_main_in (3 lanes, 90 km/h, 360 m)")
# Weaving section: x = 360..733
lane_box(ax, 360,  1.2, 373, 0.6, color="#ffe0b2", label="E_weaving (4 lanes, 90 km/h, 373 m) — bottleneck")
# E_main_out: x = 733..1093
lane_box(ax, 733,  1.2, 360, 0.6, color="#bbdefb", label="E_main_out (3 lanes, 90 km/h, 360 m)")
# E_off_ramp at end going down-right
lane_box(ax, 733,  0.4, 165, 0.4, color="#c8e6c9", label="E_off_ramp (2 lanes, 60 km/h, 165 m)")
# E_on_ramp going up-right into weaving
lane_box(ax, 200,  0.4, 165, 0.4, color="#ffcdd2", label="E_on_ramp (1 lane, 60 km/h, +TLS)")

# Arrows showing flow
ax.annotate("", xy=(370, 1.5), xytext=(355, 0.6),
            arrowprops=dict(arrowstyle="->", color="#c62828", lw=1.5))
ax.text(345, 1.05, "merge", fontsize=8, color="#c62828")

ax.annotate("", xy=(910, 0.6), xytext=(745, 1.5),
            arrowprops=dict(arrowstyle="->", color="#2e7d32", lw=1.5))
ax.text(820, 1.0, "diverge to Exit 11", fontsize=8, color="#2e7d32")

# TLS marker
ax.plot(370, 0.55, marker="o", markersize=11, color="#c62828")
ax.text(372, 0.30, "TLS\n(Ramp Metering)", fontsize=7.5, color="#c62828")

# Labels
ax.text(180, 2.1, "Westbound  →", fontsize=11, fontweight="bold", ha="center")
ax.text(550, 2.1, "weaving conflict zone", fontsize=10, fontstyle="italic",
        ha="center", color="#bf360c")
ax.text(280, 0.18, "from upstream\nClementi entrance", ha="center", fontsize=8)
ax.text(815, 0.10, "to Exit 11\nClementi", ha="center", fontsize=8)

ax.set_xlim(-30, 1130)
ax.set_ylim(0.0, 2.4)
ax.set_xticks([0, 360, 733, 1093])
ax.set_xticklabels(["0","360","733","1093"])
ax.set_xlabel("Distance (m)")
ax.set_yticks([])
ax.spines[["left","right","top"]].set_visible(False)
ax.set_title("AYE westbound bottleneck — SUMO network layout")
plt.tight_layout()
plt.savefig(f"{OUT}/fig_network.pdf")
plt.close()
print("✓ fig_network.pdf")

# -------------------------------------------------------------------
# Figure 2 - Demand profile (peak vs off-peak per minute)
# -------------------------------------------------------------------
def parse_demand(xml):
    tree = ET.parse(xml)
    counts = {}
    for v in tree.findall("vehicle"):
        d = float(v.get("depart"))
        m = int(d // 60)
        counts[m] = counts.get(m, 0) + 1
    return counts

peak_d = parse_demand("/sessions/great-beautiful-albattani/mnt/5203project/peak/peak_demand_rou.xml")
off_d  = parse_demand("/sessions/great-beautiful-albattani/mnt/5203project/offpeak/offpeak_demand_rou.xml")

fig, ax = plt.subplots(figsize=(8.5, 3.2))
xs_p = sorted(peak_d.keys()); ys_p = [peak_d[m] for m in xs_p]
xs_o = sorted(off_d.keys());  ys_o = [off_d[m] for m in xs_o]
ax.plot(xs_p, ys_p, "-", color="#c62828", lw=1.5, label=f"Peak (n={sum(peak_d.values())})")
ax.plot(xs_o, ys_o, "-", color="#1565c0", lw=1.5, label=f"Off-peak (n={sum(off_d.values())})")
ax.fill_between(xs_p, ys_p, alpha=0.18, color="#c62828")
ax.fill_between(xs_o, ys_o, alpha=0.12, color="#1565c0")
ax.set_xlabel("Simulation time (minutes)")
ax.set_ylabel("Vehicles departed per minute")
ax.set_title("Demand profile — vehicles per minute, by period")
ax.legend(loc="upper right")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_demand.pdf")
plt.close()
print("✓ fig_demand.pdf")

# -------------------------------------------------------------------
# Figure 3 - Capacity & speed bar chart (12 scenarios)
# -------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
xs = np.arange(len(SCENARIOS_PEAK))
w = 0.4

cap_p = [get("peak", s[0], "capacity_veh_h")/1000 for s in SCENARIOS_PEAK]
cap_o = [get("offpeak", s[0], "capacity_veh_h")/1000 for s in SCENARIOS_OFF]
ax = axes[0]
b1 = ax.bar(xs - w/2, cap_p, w, label="Peak", color="#c62828", alpha=0.85)
b2 = ax.bar(xs + w/2, cap_o, w, label="Off-Peak", color="#1565c0", alpha=0.85)
ax.set_xticks(xs); ax.set_xticklabels([s[1] for s in SCENARIOS_PEAK], fontsize=9)
ax.set_ylabel("Capacity (×10³ veh/h)")
ax.set_title("(a) Diverge instantaneous capacity")
ax.legend(loc="lower center"); ax.grid(axis="y", alpha=0.3)

spd_p = [get("peak", s[0], "avg_speed_weaving_kmh") for s in SCENARIOS_PEAK]
spd_o = [get("offpeak", s[0], "avg_speed_weaving_kmh") for s in SCENARIOS_OFF]
ax = axes[1]
ax.bar(xs - w/2, spd_p, w, label="Peak", color="#c62828", alpha=0.85)
ax.bar(xs + w/2, spd_o, w, label="Off-Peak", color="#1565c0", alpha=0.85)
ax.axhline(90, ls="--", color="grey", lw=0.8); ax.text(0.1, 91, "free-flow 90 km/h", fontsize=8, color="grey")
ax.set_xticks(xs); ax.set_xticklabels([s[1] for s in SCENARIOS_PEAK], fontsize=9)
ax.set_ylabel("Average weaving speed (km/h)")
ax.set_title("(b) Average speed on E$_{weaving}$")
ax.legend(loc="lower center"); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_capacity_speed.pdf")
plt.close()
print("✓ fig_capacity_speed.pdf")

# -------------------------------------------------------------------
# Figure 4 - Delay & queue length bar chart
# -------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 3.8))
del_p = [get("peak", s[0], "avg_delay_s_veh") for s in SCENARIOS_PEAK]
del_o = [get("offpeak", s[0], "avg_delay_s_veh") for s in SCENARIOS_OFF]
ax = axes[0]
ax.bar(xs - w/2, del_p, w, label="Peak", color="#c62828", alpha=0.85)
ax.bar(xs + w/2, del_o, w, label="Off-Peak", color="#1565c0", alpha=0.85)
ax.set_xticks(xs); ax.set_xticklabels([s[1] for s in SCENARIOS_PEAK], fontsize=9)
ax.set_ylabel("Average delay (s/veh)")
ax.set_title("(a) Average delay on E$_{weaving}$")
ax.legend(); ax.grid(axis="y", alpha=0.3)

q_p = [get("peak", s[0], "avg_queue_veh") for s in SCENARIOS_PEAK]
q_o = [get("offpeak", s[0], "avg_queue_veh") for s in SCENARIOS_OFF]
ax = axes[1]
ax.bar(xs - w/2, q_p, w, label="Peak", color="#c62828", alpha=0.85)
ax.bar(xs + w/2, q_o, w, label="Off-Peak", color="#1565c0", alpha=0.85)
ax.set_xticks(xs); ax.set_xticklabels([s[1] for s in SCENARIOS_PEAK], fontsize=9)
ax.set_ylabel("Average queue length (veh)")
ax.set_title("(b) Average queue length on E$_{weaving}$")
ax.legend(); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_delay_queue.pdf")
plt.close()
print("✓ fig_delay_queue.pdf")

# -------------------------------------------------------------------
# Figure 5 - Network total time loss (sorted)
# -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 4))
labels = []
vals = []
for period in ("peak","offpeak"):
    for s_id, s_lbl in SCENARIOS_PEAK:
        labels.append(f"{period}/{s_lbl.replace(chr(10),' ')}")
        vals.append(get(period, s_id, "net_total_timeloss_veh_s")/1000)
order = sorted(range(len(vals)), key=lambda i: vals[i])
labels_s = [labels[i] for i in order]
vals_s   = [vals[i]   for i in order]
colors_s = ["#c62828" if l.startswith("peak") else "#1565c0" for l in labels_s]
ax.barh(range(len(vals_s)), vals_s, color=colors_s, alpha=0.85)
ax.set_yticks(range(len(vals_s))); ax.set_yticklabels(labels_s, fontsize=8)
ax.set_xlabel("Network total time loss (×10³ veh-s)")
ax.set_title("All 12 scenarios — total network time loss")
ax.invert_yaxis()
ax.grid(axis="x", alpha=0.3)
# Custom legend
ax.legend(handles=[Rectangle((0,0),1,1,color="#c62828"),
                   Rectangle((0,0),1,1,color="#1565c0")],
          labels=["Peak","Off-Peak"], loc="lower right")
plt.tight_layout()
plt.savefig(f"{OUT}/fig_timeloss.pdf")
plt.close()
print("✓ fig_timeloss.pdf")

# -------------------------------------------------------------------
# Figure 6 - Δ% summary (improvement vs base) per metric
# -------------------------------------------------------------------
def dpct(period, scen, key, smaller_better=True):
    b = get(period, "base", key)
    n = get(period, scen, key)
    if b == 0: return 0
    delta = (n-b)/b*100
    return -delta if smaller_better else delta

metrics = [
    ("Avg delay", "avg_delay_s_veh", True),
    ("Queue", "avg_queue_veh", True),
    ("Time in queue", "avg_time_in_queue_s_veh", True),
    ("Excess acc.", "avg_excess_acc_veh", True),
    ("Net time loss", "net_total_timeloss_veh_s", True),
    ("Speed", "avg_speed_weaving_kmh", False),
    ("Capacity", "capacity_veh_h", False),
]
strategies = [("vsl","VSL"), ("vsl_up","VSL$_\\mathrm{up}$"), ("rm","RM"),
              ("vsl_rm","VSL+RM"), ("vsl_up_rm","VSL$_\\mathrm{up}$+RM")]

fig, axes = plt.subplots(1, 2, figsize=(12, 4.2))
for ax, period, title in [(axes[0],"peak","(a) Peak"), (axes[1],"offpeak","(b) Off-peak")]:
    M = np.array([[dpct(period, sid, key, sb) for (_,key,sb) in metrics] for (sid,_) in strategies])
    im = ax.imshow(M, cmap="RdYlGn", aspect="auto", vmin=-50, vmax=50)
    ax.set_xticks(range(len(metrics))); ax.set_xticklabels([m[0] for m in metrics], rotation=30, ha="right")
    ax.set_yticks(range(len(strategies))); ax.set_yticklabels([s[1] for s in strategies])
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i,j]:+.1f}%", ha="center", va="center", fontsize=8.5, color="black")
    ax.set_title(title + " — improvement vs Base (positive = better)")
    cb = plt.colorbar(im, ax=ax, fraction=0.04, pad=0.02)
    cb.set_label("% improvement")
plt.tight_layout()
plt.savefig(f"{OUT}/fig_improvement_heatmap.pdf")
plt.close()
print("✓ fig_improvement_heatmap.pdf")

# -------------------------------------------------------------------
# Figure 7 - Per-edge metrics from peak base SUMO output
# -------------------------------------------------------------------
def parse_edgedata(xml_path):
    tree = ET.parse(xml_path)
    intervals = []
    for itv in tree.getroot().findall("interval"):
        rec = {"begin": float(itv.attrib["begin"]), "edges": {}}
        for ed in itv.findall("edge"):
            rec["edges"][ed.attrib["id"]] = {k: float(v) for k,v in ed.attrib.items() if k != "id"}
        intervals.append(rec)
    return intervals

ints_pb = parse_edgedata(f"{SUMO}/peak_base/edge_data_output.xml")
ints_pr = parse_edgedata(f"{SUMO}/peak_rm/edge_data_output.xml")
ints_pv = parse_edgedata(f"{SUMO}/peak_vsl/edge_data_output.xml")

def series(ints, edge, key, default=0):
    xs, ys = [], []
    for r in ints:
        if edge in r["edges"]:
            xs.append(r["begin"]/60.0)
            ys.append(r["edges"][edge].get(key, default))
        else:
            xs.append(r["begin"]/60.0); ys.append(default)
    return xs, ys

fig, axes = plt.subplots(2, 1, figsize=(8.5, 5.8), sharex=True)

# (a) Speed on E_weaving across scenarios
ax = axes[0]
for label, ints, color in [("Base", ints_pb, "#37474f"),
                             ("RM", ints_pr, "#2e7d32"),
                             ("VSL (in-section)", ints_pv, "#c62828")]:
    xs, ys = series(ints, "E_weaving", "speed")
    ax.plot(xs, [y*3.6 for y in ys], lw=1.4, label=label, color=color)
ax.axhline(90, ls=":", color="grey", lw=0.8); ax.text(2, 92, "free-flow 90 km/h", fontsize=8, color="grey")
ax.set_ylabel("Weaving speed (km/h)")
ax.set_title("(a) E$_{weaving}$ speed time series — Peak demand, three scenarios")
ax.legend(loc="lower right")
ax.grid(alpha=0.3); ax.set_ylim(20, 100)

# (b) Density on E_weaving
ax = axes[1]
for label, ints, color in [("Base", ints_pb, "#37474f"),
                             ("RM", ints_pr, "#2e7d32"),
                             ("VSL (in-section)", ints_pv, "#c62828")]:
    xs, ys = series(ints, "E_weaving", "density")
    ax.plot(xs, ys, lw=1.4, label=label, color=color)
ax.set_xlabel("Simulation time (minutes)")
ax.set_ylabel("Density (veh/km)")
ax.set_title("(b) E$_{weaving}$ density time series")
ax.legend(loc="upper right")
ax.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_timeseries.pdf")
plt.close()
print("✓ fig_timeseries.pdf")

# -------------------------------------------------------------------
# Figure 8 - Fundamental diagram (density-flow scatter from edge data)
# -------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(11, 4))

for ax, ints, title, color in [
    (axes[0], ints_pb, "Peak Base", "#c62828"),
    (axes[1], parse_edgedata(f"{SUMO}/offpeak_base/edge_data_output.xml"), "Off-Peak Base", "#1565c0")
]:
    xs, ys = [], []
    cs = []
    for r in ints:
        for eid in ("E_main_in","E_weaving","E_main_out"):
            if eid in r["edges"]:
                e = r["edges"][eid]
                d = e.get("density", 0)
                spd = e.get("speed", 0)
                f = d * spd * 3.6
                xs.append(d); ys.append(f)
                cs.append({"E_main_in":"#1565c0","E_weaving":"#c62828","E_main_out":"#2e7d32"}[eid])
    ax.scatter(xs, ys, c=cs, s=14, alpha=0.7, edgecolor="none")
    ax.set_xlabel("Density (veh/km)")
    ax.set_ylabel("Flow (veh/h)")
    ax.set_title(f"Fundamental diagram — {title}")
    ax.grid(alpha=0.3)
    # Capacity line
    cap = 5060
    ax.axhline(cap, ls="--", color="black", alpha=0.4); ax.text(2, cap+50, f"empirical cap. {cap}", fontsize=8)
    # Legend
    handles = [Line2D([],[], marker="o", color="#1565c0", lw=0, ms=6, label="E_main_in"),
               Line2D([],[], marker="o", color="#c62828", lw=0, ms=6, label="E_weaving"),
               Line2D([],[], marker="o", color="#2e7d32", lw=0, ms=6, label="E_main_out")]
    ax.legend(handles=handles, loc="upper right")
plt.tight_layout()
plt.savefig(f"{OUT}/fig_funddiag.pdf")
plt.close()
print("✓ fig_funddiag.pdf")

# -------------------------------------------------------------------
# Figure 9 - VSL placement comparison (in-section vs upstream)
# -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 4))
metrics_lbl = ["Capacity\n(veh/h)", "Avg Delay\n(s/veh)", "Queue\n(veh)",
               "Speed\n(km/h)", "TimeLoss\n(×1k veh-s)"]
metrics_keys = ["capacity_veh_h","avg_delay_s_veh","avg_queue_veh","avg_speed_weaving_kmh","net_total_timeloss_veh_s"]

# Δ% for peak only
def delta(scen, key):
    b = get("peak","base",key)
    n = get("peak",scen,key)
    return (n-b)/b*100 if b else 0

dx = np.arange(len(metrics_keys))
w = 0.32
v_in = [delta("vsl", k) for k in metrics_keys]
v_up = [delta("vsl_up", k) for k in metrics_keys]
ax.bar(dx-w/2, v_in, w, color="#e0876b", label="VSL on E_weaving_0\n(in-section, single lane)")
ax.bar(dx+w/2, v_up, w, color="#a86a4d", label="VSL on E_main_in lanes 0–2\n(upstream, all lanes)")
ax.axhline(0, color="black", lw=0.8)
ax.set_xticks(dx); ax.set_xticklabels(metrics_lbl, fontsize=9)
ax.set_ylabel("Δ vs Base (%)  — closer to 0 = no harm; negative for delay/queue/loss = improvement")
ax.set_title("VSL placement comparison — Peak period Δ% relative to Base")
ax.legend(loc="upper left", fontsize=9)
ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_vsl_placement.pdf")
plt.close()
print("✓ fig_vsl_placement.pdf")

# -------------------------------------------------------------------
# Figure 10 - Per-edge breakdown for peak base & peak RM
# -------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 4))
edges = ["E_main_in","E_weaving","E_main_out","E_off_ramp","E_on_ramp_2"]

def avg_metric(ints, edge, key):
    vs = [r["edges"][edge].get(key,0) for r in ints if edge in r["edges"]]
    return sum(vs)/len(vs) if vs else 0

avg_speed_pb = [avg_metric(ints_pb, e, "speed")*3.6 for e in edges]
avg_speed_pr = [avg_metric(ints_pr, e, "speed")*3.6 for e in edges]
xs = np.arange(len(edges))
ax.bar(xs-0.2, avg_speed_pb, 0.4, label="Peak Base", color="#c62828", alpha=0.85)
ax.bar(xs+0.2, avg_speed_pr, 0.4, label="Peak RM", color="#2e7d32", alpha=0.85)
ax.set_xticks(xs); ax.set_xticklabels(edges, fontsize=9)
ax.set_ylabel("Average speed (km/h)")
ax.set_title("Per-edge average speed — Peak Base vs Peak RM")
ax.axhline(90, ls=":", color="grey", lw=0.8); ax.text(0.1, 91, "free-flow 90 km/h", fontsize=8, color="grey")
ax.legend(); ax.grid(axis="y", alpha=0.3)
plt.tight_layout()
plt.savefig(f"{OUT}/fig_per_edge_speed.pdf")
plt.close()
print("✓ fig_per_edge_speed.pdf")

print("\nAll figures generated.")
