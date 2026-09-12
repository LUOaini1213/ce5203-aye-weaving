#!/usr/bin/env python3
"""Write a comparison, without using historical numbers to set simulation inputs."""
import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read_rows(path):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        return {(r["period"], r["scenario"]): r for r in csv.DictReader(handle)}


def compare(output):
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
    lines += ["", "The numerical disagreement remains unresolved. No thresholds or demand inputs were tuned to match the old table.",
              "See ../../docs/REPRODUCTION.md for provenance, input equivalence, simulator version and the legacy metric definitions.", ""]
    with (output / "historical_comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    (output / "comparison.md").write_text("\n".join(lines), encoding="utf-8")
    print(output / "comparison.md")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    compare(parser.parse_args().output)
