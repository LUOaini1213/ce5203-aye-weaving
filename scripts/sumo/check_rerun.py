#!/usr/bin/env python3
"""Compare fresh full-horizon runs with the committed rerun, and check the ranking signs.

`check_run.py` proves the committed evidence is internally consistent; it does
not simulate anything. This script is the other half: point it at one or more
new run directories (each holding a `summary.csv` written by
`run_scenarios.py`, at the default thresholds and the full 5,400 s horizon) and
it

* compares each fresh scenario with the same scenario in the committed run, on
  edge time loss, entry (departure) delay and arrivals, and fails if any
  differs by more than `--tolerance-pct`;
* checks the signs the README states, for every period where the needed
  scenarios were run: ramp metering lowers edge time loss against base, but
  raises edge time loss plus entry delay; upstream VSL lowers edge time loss
  plus entry delay against base.

    python scripts/sumo/run_scenarios.py --period peak --scenario base --output runs/full-base
    python scripts/sumo/run_scenarios.py --period peak --scenario rm --output runs/full-rm
    python scripts/sumo/check_rerun.py runs/full-base runs/full-rm
"""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "results" / "reproduction-2026-09-12"
EDGE = "net_total_timeloss_veh_s"
ENTRY = "tripinfo_completed_depart_delay_s"
COMPARED = (EDGE, ENTRY, "arrived")
FULL_HORIZON_S = 5400.0


def read_summary(folder):
    with (Path(folder) / "summary.csv").open(encoding="utf-8", newline="") as handle:
        return {(r["period"], r["scenario"]): r for r in csv.DictReader(handle)}


def combined(row):
    return float(row[EDGE]) + float(row[ENTRY])


def sumo_version(folder, period, scenario):
    path = Path(folder) / f"{period}_{scenario}" / "provenance.json"
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("sumo_version", "unknown")
    except (OSError, ValueError):
        return "unknown"


def check(runs, reference=REFERENCE, tolerance_pct=2.0):
    """Return (report lines, problems). An empty problem list means PASS."""
    reference_rows = read_summary(reference)
    reference_params = json.loads((Path(reference) / "run_manifest.json")
                                  .read_text(encoding="utf-8"))["parameters"]
    fresh, origin = {}, {}
    problems, lines = [], []
    for folder in runs:
        manifest = json.loads((Path(folder) / "run_manifest.json").read_text(encoding="utf-8"))
        params = manifest.get("parameters", {})
        if float(params.get("end", 0)) < FULL_HORIZON_S:
            problems.append(f"{folder}: horizon {params.get('end')} s is shorter than the full "
                            f"{FULL_HORIZON_S:g} s; a smoke run cannot check the result")
        changed = sorted(k for k in reference_params if params.get(k) != reference_params[k])
        if changed:
            problems.append(f"{folder}: parameters differ from the committed run: "
                            + ", ".join(f"{k}={params.get(k)!r} (committed {reference_params[k]!r})"
                                        for k in changed))
        for key, row in read_summary(folder).items():
            fresh[key] = row
            origin[key] = folder
    if not fresh:
        problems.append("no fresh scenarios found")
    for key in sorted(fresh):
        row, ref = fresh[key], reference_rows[key]
        version = sumo_version(origin[key], *key)
        lines.append(f"{key[0]}_{key[1]}  ({version}; committed run: {sumo_version(reference, *key)})")
        for column in COMPARED:
            new, old = float(row[column]), float(ref[column])
            diff = 0.0 if new == old else 100.0 * (new - old) / old
            status = "identical" if new == old else f"{diff:+.3f}%"
            lines.append(f"  {column:<36}{new:>16,.2f} vs {old:>16,.2f}  {status}")
            if abs(diff) > tolerance_pct:
                problems.append(f"{key[0]}_{key[1]} {column} differs from the committed run by "
                                f"{diff:+.3f}% (tolerance {tolerance_pct}%)")
    for period in ("peak", "offpeak"):
        base = fresh.get((period, "base"))
        if base is None:
            continue
        rm = fresh.get((period, "rm"))
        if rm is not None:
            edge = 100.0 * (float(rm[EDGE]) / float(base[EDGE]) - 1)
            both = 100.0 * (combined(rm) / combined(base) - 1)
            lines.append(f"{period}: RM vs base  edge {edge:+.2f}%  edge + entry {both:+.2f}%")
            if edge >= 0:
                problems.append(f"{period}: ramp metering no longer lowers edge time loss ({edge:+.2f}%)")
            if both <= 0:
                problems.append(f"{period}: ramp metering no longer raises edge time loss plus "
                                f"entry delay ({both:+.2f}%)")
        up = fresh.get((period, "vsl_up"))
        if up is not None:
            both = 100.0 * (combined(up) / combined(base) - 1)
            lines.append(f"{period}: upstream VSL vs base  edge + entry {both:+.2f}%")
            if both >= 0:
                problems.append(f"{period}: upstream VSL no longer lowers edge time loss plus "
                                f"entry delay ({both:+.2f}%)")
    return lines, problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path, help="fresh run directories")
    parser.add_argument("--reference", type=Path, default=REFERENCE)
    parser.add_argument("--tolerance-pct", type=float, default=2.0)
    args = parser.parse_args(argv)
    lines, problems = check(args.runs, args.reference, args.tolerance_pct)
    print("\n".join(lines))
    if problems:
        print("FAIL:\n  " + "\n  ".join(problems))
        return 1
    print(f"PASS: every fresh scenario within {args.tolerance_pct}% "
          "of the committed run, and the stated signs hold")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
