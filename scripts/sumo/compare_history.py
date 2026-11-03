#!/usr/bin/env python3
"""Write a comparison, without using historical numbers to set simulation inputs."""
import argparse
import csv
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ("base", "vsl", "vsl_up", "rm", "vsl_rm", "vsl_up_rm")
EDGE = "net_total_timeloss_veh_s"
ENTRY = "tripinfo_completed_depart_delay_s"


def combined_rows(new):
    """Edge time loss plus the delay of vehicles held before they enter the network.

    `net_total_timeloss_veh_s` only sees vehicles once they are on a modelled
    edge. Ramp metering holds vehicles at the entry, so its edge saving is
    partly a transfer into `tripinfo_completed_depart_delay_s`. Both columns
    are already in summary.csv; this adds them and ranks the six strategies
    under each measure, so the ranking a reader sees does not depend on which
    of the two columns they happened to look at.
    """
    rows = []
    for period in ("peak", "offpeak"):
        edge = {s: float(new[(period, s)][EDGE]) for s in SCENARIOS}
        entry = {s: float(new[(period, s)][ENTRY]) for s in SCENARIOS}
        combined = {s: round(edge[s] + entry[s], 2) for s in SCENARIOS}
        edge_rank = {s: i + 1 for i, s in enumerate(sorted(SCENARIOS, key=edge.get))}
        combined_rank = {s: i + 1 for i, s in enumerate(sorted(SCENARIOS, key=combined.get))}
        for s in SCENARIOS:
            rows.append({
                "period": period, "scenario": s,
                "edge_time_loss_veh_s": edge[s], "entry_delay_veh_s": entry[s],
                "combined_veh_s": combined[s],
                "edge_vs_base_pct": round(100 * (edge[s] / edge["base"] - 1), 2),
                "combined_vs_base_pct": round(100 * (combined[s] / combined["base"] - 1), 2),
                "edge_rank": edge_rank[s], "combined_rank": combined_rank[s],
            })
    return rows


def read_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return {(r["period"], r["scenario"]): r for r in csv.DictReader(handle)}


def compare(output, quiet=False):
    output = Path(output)
    old = read_rows(ROOT / "results" / "sumo_12scenarios_results.csv")
    new = read_rows(output / "summary.csv")
    rows = []
    lines = ["# Historical report versus the recovered runner", "",
             "New values are a fresh SUMO run. Historical values are retained unchanged; agreement is not an acceptance criterion.", "",
             "| Period | Scenario | Historical network time loss (veh-s) | New network time loss (veh-s) | New vs historical |",
             "|---|---|---:|---:|---:|"]
    for key, previous in old.items():
        current = new[key]
        before = float(previous["net_total_timeloss_veh_s"])
        after = float(current["net_total_timeloss_veh_s"])
        row = {"period": key[0], "scenario": key[1],
               "historical_time_loss_veh_s": before, "rerun_time_loss_veh_s": after,
               "change_pct": round(100 * (after / before - 1), 4)}
        rows.append(row)
        lines.append(f"| {key[0]} | {key[1]} | {before:,.1f} | {after:,.1f} | {row['change_pct']:+.2f}% |")
    lines += ["", "## Ramp-metering effect within each run", "",
              "| Period | Historical RM vs base | New RM vs base |", "|---|---:|---:|"]
    for period in ("peak", "offpeak"):
        effects = [100 * (float(data[(period, "rm")]["net_total_timeloss_veh_s"]) /
                          float(data[(period, "base")]["net_total_timeloss_veh_s"]) - 1) for data in (old, new)]
        lines.append(f"| {period} | {effects[0]:+.2f}% | {effects[1]:+.2f}% |")
    combined = combined_rows(new)
    lines += ["", "## New run: edge time loss plus entry delay", "",
              "The table above, like the historical one, counts only time lost on modelled edges. "
              "Vehicles held before entry (ramp metering's queue) appear in tripinfo `departDelay` instead. "
              "Rank 1 is the lowest of the six strategies in that period. This is one run with one seed; "
              "the seed and simulator version are in run_manifest.json and each provenance.json.", "",
              "| Period | Scenario | Edge time loss (veh-s) | Entry delay (veh-s) | Edge + entry (veh-s) | Edge vs base | Edge + entry vs base | Rank, edge | Rank, edge + entry |",
              "|---|---|---:|---:|---:|---:|---:|---:|---:|"]
    for row in combined:
        lines.append(f"| {row['period']} | {row['scenario']} | {row['edge_time_loss_veh_s']:,.1f} | "
                     f"{row['entry_delay_veh_s']:,.1f} | {row['combined_veh_s']:,.1f} | "
                     f"{row['edge_vs_base_pct']:+.2f}% | {row['combined_vs_base_pct']:+.2f}% | "
                     f"{row['edge_rank']} | {row['combined_rank']} |")
    for period in ("peak", "offpeak"):
        mine = [r for r in combined if r["period"] == period]
        best_edge = min(mine, key=lambda r: r["edge_rank"])["scenario"]
        best_combined = min(mine, key=lambda r: r["combined_rank"])["scenario"]
        lines.append("")
        lines.append(f"{period}: lowest edge time loss `{best_edge}`; lowest edge + entry `{best_combined}`.")
    lines += ["", "The numerical disagreement remains unresolved. No thresholds or demand inputs were tuned to match the old table.",
              "See ../../docs/REPRODUCTION.md for provenance, input equivalence, simulator version and the legacy metric definitions.", ""]
    with (output / "historical_comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    with (output / "combined_delay.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=combined[0])
        writer.writeheader()
        writer.writerows(combined)
    # The committed evidence keeps CRLF bytes (see .gitattributes); write them explicitly so the
    # byte-for-byte check gives the same answer on Linux CI as on the Windows machine that ran SUMO.
    (output / "comparison.md").write_text("\n".join(lines), encoding="utf-8", newline="\r\n")
    if not quiet:
        print(output / "comparison.md")


DERIVED = ("comparison.md", "historical_comparison.csv", "combined_delay.csv")


def check(output):
    """Regenerate the derived documents in a temporary directory and diff them.

    comparison.md is linked straight from README.md, so it is held to the same
    standard as the tables it summarises: it must still follow, byte for byte,
    from the committed summary.csv and the historical CSV.
    """
    output = Path(output)
    problems = []
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        shutil.copy(output / "summary.csv", tmp / "summary.csv")
        compare(tmp, quiet=True)
        for name in DERIVED:
            committed = output / name
            if not committed.exists():
                problems.append(f"{name} is missing")
            elif committed.read_bytes() != (tmp / name).read_bytes():
                problems.append(f"{name} no longer follows from summary.csv")
    if problems:
        raise ValueError(f"{output}: " + "; ".join(problems)
                         + f"; regenerate with scripts/sumo/compare_history.py {output}")
    print(f"PASS: {output} {', '.join(DERIVED)} follow from summary.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    parser.add_argument("--check", action="store_true",
                        help="verify the committed derived documents instead of rewriting them")
    args = parser.parse_args()
    if args.check:
        check(args.output)
    else:
        compare(args.output)
