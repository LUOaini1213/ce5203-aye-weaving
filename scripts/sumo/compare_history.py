#!/usr/bin/env python3
"""Write a comparison, without using historical numbers to set simulation inputs."""
import argparse
import csv
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


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
    lines += ["", "The numerical disagreement remains unresolved. No thresholds or demand inputs were tuned to match the old table.",
              "See ../../docs/REPRODUCTION.md for provenance, input equivalence, simulator version and the legacy metric definitions.", ""]
    with (output / "historical_comparison.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
    # The committed evidence keeps CRLF bytes (see .gitattributes); write them explicitly so the
    # byte-for-byte check gives the same answer on Linux CI as on the Windows machine that ran SUMO.
    (output / "comparison.md").write_text("\n".join(lines), encoding="utf-8", newline="\r\n")
    if not quiet:
        print(output / "comparison.md")


DERIVED = ("comparison.md", "historical_comparison.csv")


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
    print(f"PASS: {output} comparison.md and historical_comparison.csv "
          "follow from summary.csv")


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
