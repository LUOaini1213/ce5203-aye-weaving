# CE5203 · AYE Westbound Weaving Bottleneck

**Analysis and Mitigation of the AYE Westbound Weaving Bottleneck**  
NUS CE5203 *Traffic Flow and Control* — Course Project (Spring 2026) · Group 12

- **Built:** a YOLOv11 line-counting pipeline for four points on the AYE westbound
  weaving section (Exit 9 → Exit 11, ≈373 m), a SUMO network calibrated to those
  counts, and the course's VSL / ramp-metering (RM) controller, recovered from the
  submission archive and rerun in September 2026 as 12 scenarios (6 strategies ×
  peak / off-peak) with control traces and SHA-256-hashed raw XML.
- **Found, edge time loss only:** RM alone is the lowest of the six in both
  periods; at peak it cuts network **total time loss 54.98%** against do-nothing.
- **Found, edge time loss + entry delay:** the ranking flips. Upstream VSL is the
  lowest in both periods (peak 780,648.7 vs base 829,343.9 veh-s, −5.9%; off-peak
  −12.8%), and RM is higher than do-nothing (+14.6% peak, +141.2% off-peak):
  the extra delay of vehicles it holds before entry outweighs its edge saving.
- **Limits:** one seed (42) on one simulator version (SUMO 1.24.0); the original
  course table (RM −22.7% time loss, −7.7% weaving delay) does not reproduce; the
  ≈5,060 veh/h field figure is a mean flow from tallies that predate a
  counting-code fix and were not recounted.

| | |
|---|---|
| **Pipeline** | Field video → **YOLOv11** counts/speeds → **SUMO** microsimulation → VSL / RM / VSL+RM |
| **Rankings, both measures** | [comparison.md](results/reproduction-2026-09-12/comparison.md) and [combined_delay.csv](results/reproduction-2026-09-12/combined_delay.csv), regenerated and diffed by `compare_history.py --check` |
| **Historical course report** | [latex/report.tex](latex/report.tex) (26 April 2026). Kept unchanged: its −22.7% and its "ramp metering alone" recommendation predate the rerun; see [what did not hold up](docs/REPRODUCTION.md#new-result-versus-the-historical-claim) |
| **Environment** | Python 3.11 (CI: Linux and Windows); SUMO 1.24.0 for simulation (`pip install eclipse-sumo==1.24.0 traci==1.24.0` or an Eclipse SUMO install) |

> Course group project. Public mirror for portfolio / reproducibility.  
> Contributors: Leong Sio Kuan · **Luo Wenjie** · Wang Xu · Zhao Jiaqing  
> **My part (Luo Wenjie):** the YOLOv11 counting pipeline (`scripts/vision/line_counting.py` and `scripts/vision/yolo_line_count.py`, the four-point tallies in `data/counts/`) and the SUMO side: network build, demand and speed calibration, and the 12 scenario runs behind `results/`. Site selection, capacity analysis and the report were joint work.

## Provenance and verification

**12 September 2026: the original control runner was recovered from the course submission archive.**
All six strategies can now be simulated for both demand periods, with control
traces, raw XML, metrics and provenance. A fresh twelve-scenario run is committed.
It **does not reproduce the historical −22.7% / −7.7% numbers**; the new and old
results are [compared explicitly](results/reproduction-2026-09-12/comparison.md).
[Recovery details and metric limitations](docs/REPRODUCTION.md) ·
[![SUMO reproduction](https://github.com/LUOaini1213/ce5203-aye-weaving/actions/workflows/sumo-reproduction.yml/badge.svg)](https://github.com/LUOaini1213/ce5203-aye-weaving/actions/workflows/sumo-reproduction.yml)

What that badge covers: CI recomputes the SHA-256 of the twelve scenarios' raw
outputs, checks `summary.csv` against their `metrics.json`, regenerates the
derived comparison files and recomputes the numbers quoted in this file. With
SUMO 1.24.0 pinned from PyPI, it then re-simulates peak `base`, `rm` and `vsl_up`
over the full 5,400 s horizon at the original thresholds and requires them to
match the committed run within 2% and to keep the signs stated above
(`check_rerun.py`). The other nine scenarios are re-simulated only as a 120 s
integration smoke test with both thresholds lowered so every controller fires;
that run checks the software, not the result.

```bash
# Verify the committed evidence: ~1 s, standard library only, no SUMO needed.
# Recomputes every artifact's SHA-256 and checks summary.csv against the
# twelve metrics.json files. CI runs this same command on every push.
python scripts/sumo/check_run.py results/reproduction-2026-09-12 --require-complete

# Regenerate-and-diff the derived comparison files, including the two rankings.
python scripts/sumo/compare_history.py results/reproduction-2026-09-12 --check

# Produce a new run of your own (this one needs SUMO).
python scripts/sumo/run_scenarios.py --all --jobs 2 --output runs/full --compress-xml
python scripts/sumo/check_run.py runs/full --require-complete
python scripts/sumo/compare_history.py runs/full

# Or re-simulate only the scenarios behind the headline and compare them with
# the committed run (about 30 s each; this is what CI does).
python scripts/sumo/run_scenarios.py --period peak --scenario base --output runs/full-base --compress-xml
python scripts/sumo/run_scenarios.py --period peak --scenario rm --output runs/full-rm --compress-xml
python scripts/sumo/check_rerun.py runs/full-base runs/full-rm
```

Simulation requires SUMO and TraCI tools (`SUMO_HOME` or `--sumo-binary`). The
build CI uses is the PyPI one: `pip install eclipse-sumo==1.24.0 traci==1.24.0`,
then point `SUMO_HOME` at `python -c "import sumo; print(sumo.SUMO_HOME)"`. With
it, peak `base`, `rm` and `vsl_up` re-simulated on 3 November 2026, on Windows and
on the Linux CI runner, matched the committed run exactly (CI requires 2%). Uses the
recovered 0.5-second step, seed 42 and 0.15/0.20 occupancy thresholds. No model or
dataset download is needed; the published network and demand files are sufficient.

---

## What this project does

1. **Identify** a recurring weaving bottleneck on AYE WB (on-ramp merge vs off-ramp diverge).
2. **Measure** peak (46 min recorded, 43 valid) and off-peak (62 recorded, 60 valid) demand with a **YOLOv11** multi-line counting pipeline at four points.
3. **Estimate** weaving-section capacity from field counts as the observed mean flow,
   ≈ **5,060 veh/h** (`python scripts/counts/capacity_from_counts.py` re-derives it
   from the tally workbook: 3,627 veh over 43 min = 5,060.9 veh/h). It is an average
   over the survey, not a measured queue-discharge capacity; see [Results](#results).
4. **Calibrate** a SUMO network to YOLO-derived demand/speeds.
5. **Evaluate** control strategies over **12 runs**: Variable Speed Limit (VSL), Ramp Metering (RM), VSL+RM, plus upstream VSL placement, under peak and off-peak demand.
6. **Rank** the six strategies. On edge time loss alone, ramp metering is the
   lowest in both demand periods and in both tables: the original course table put
   the peak gain at **−22.7%** total time loss and **−7.7%** weaving delay; the
   September 2026 rerun puts it at **−54.98%** and **−54.81%**. Adding the entry
   delay of vehicles held back by the meter (rerun only; the historical table has no
   such column) reverses that: upstream VSL is the lowest of the six and ramp
   metering is higher than do-nothing in both periods. See [Results](#results).

---

## Repository layout

```text
docs/                 Runner recovery and reproduction notes (group report PDF not published)
sumo/peak/            Peak network + routes + standalone 0.1 s base-case outputs
sumo/offpeak/         Off-peak network + routes + standalone 0.1 s base-case outputs
scripts/vision/       Counting-line geometry (line_counting.py) + the YOLO runner
scripts/sumo/         Recovered VSL / RM controls, twelve-scenario runner and verification
scripts/counts/       Re-derives the empirical capacity from the tally workbook
scripts/latex/        Generates latex/data_macros.tex from the historical CSV
scripts/analysis/     Optional React dashboards (figure generation lives in latex/make_figures.py)
tests/                Regression tests; CI runs them before installing SUMO
data/counts/          Aggregated count tables (xlsx) used for demand
results/              Historical tables + separately identified September 2026 rerun
latex/                Report source + figures
```

**Not included (size / privacy):** raw field videos, YOLO weights, OpenVINO model folder. Pass your own with `--video` and `--model`.

---

## Quick start · SUMO

Requirements: [SUMO](https://eclipse.dev/sumo/) with `SUMO_HOME` set.

```bash
# Peak base case
sumo -c sumo/peak/aye_peak.sumocfg

# Off-peak base case
sumo -c sumo/offpeak/aye_offpeak.sumocfg
```

Rebuild net from nod/edg/con (Windows example):

```bat
cd sumo\peak
build_network.bat
```

**What is and is not re-runnable.** The two `sumo -c` commands above run the
standalone base configurations at 0.1 s. To run **all twelve controlled
scenarios**, use `scripts/sumo/run_scenarios.py` above; it restores the original
scenario runner's 0.5 s step and controls. The old runner was recovered and
published in portable form on 12 September 2026. The historical −22.7% / −7.7%
claims remain arithmetically checkable in `results/sumo_12scenarios_results.csv`,
but the fresh execution produces different numbers, preserved separately under
`results/reproduction-2026-09-12/`. `results/sumo_8scenarios_comparison.txt` is an
earlier subset, retained as history. [See the recovery notes](docs/REPRODUCTION.md).

Report figures regenerate from the committed data:
`pip install -r requirements.txt && python latex/make_figures.py` (writes
`latex/figs/`). Eight of them are the report's own figures, redrawn from
`results/sumo_12scenarios_results.csv` and the demand files. The report's two
per-edge figures needed controlled-scenario outputs that the original run never
published; the recovered runner does save them, so the script draws those two
from `results/reproduction-2026-09-12/` instead and writes them as
`fig_timeseries_rerun.pdf` and `fig_per_edge_speed_rerun.pdf`, captioned with the
run they come from. They are new observations at the recovered 0.5 s step and
stay out of the historical figure series. The empirical capacity line on the
fundamental diagram is computed from the tally workbook at run time, not typed in.

---

## Quick start · vision counting

```bash
pip install -r requirements-vision.txt
python scripts/vision/yolo_line_count.py \
  --video your_clip.mp4 --model yolo11s.pt --csv counts.csv
```

Ultralytics YOLO + ByteTrack tracking feed eight oriented counting lines, which
produce per-class tallies (car / motorcycle / bus / truck) and a CSV row per
minute of video. `--device` takes any Ultralytics device string (`cpu`,
`cuda:0`, `intel:gpu` for an OpenVINO export) and defaults to `cpu`; `--show`
opens a preview window and is off by default, so the script also runs headless.
`--help` lists the rest (confidence, tracker config, screenshot dumps).

The part that decides whether a tally is incremented — segment intersection,
travel direction, per-line and per-group de-duplication — is
[`scripts/vision/line_counting.py`](scripts/vision/line_counting.py). It has no
third-party dependencies, so `tests/test_line_counting.py` exercises it on
hand-written pixel tracks in the same CI job as the SUMO tests:

```bash
python -m unittest discover -s tests -v
```

---

## Results

Ramp metering versus do-nothing, in the two tables this repository holds. The
left column is the original course table; the right one is the run that ships
with control traces, raw XML and per-file hashes, and that the command at the
top of this page verifies.

| Ramp metering vs base | Historical table<br>`results/sumo_12scenarios_results.csv` | September 2026 rerun<br>`results/reproduction-2026-09-12/summary.csv` |
|---|---:|---:|
| Peak — network total time loss | **−22.7%** | **−54.98%** |
| Peak — weaving average delay | **−7.7%** | **−54.81%** |
| Off-peak — network total time loss | −2.77% | −36.09% |
| Off-peak — weaving average delay | −7.09% | −38.78% |

Both peak columns are arithmetic on the CSVs, for `peak,base` against `peak,rm`:
historically `net_total_timeloss_veh_s` 143,396.6 → 110,833.5 and `avg_delay_s_veh`
11.89 → 10.97; in the rerun 183,708.2 → 82,697.5 and 21.2 → 9.58.

In both tables, in-section VSL alone is worse than doing nothing, and combining
it with ramp metering is worse than ramp metering alone, on edge time loss.

**The ranking under both measures** (rerun only, one seed; the full table with all
six strategies is in [comparison.md](results/reproduction-2026-09-12/comparison.md),
machine-readable in [combined_delay.csv](results/reproduction-2026-09-12/combined_delay.csv)):

| Period | Lowest edge time loss | Lowest edge time loss + entry delay | RM vs base, edge + entry |
|---|---|---|---:|
| Peak | `rm` (82,697.5 veh-s) | `vsl_up` (780,648.7 vs base 829,343.9 veh-s, −5.9%) | +14.6% |
| Off-peak | `rm` (83,313.7 veh-s) | `vsl_up` (188,890.2 vs base 216,563.5 veh-s, −12.8%) | +141.2% |

The upstream-VSL margins (−5.9% and −12.8%) come from a single seed. No seed sweep has
been run, so they show that the ranking depends on what is counted, not that
upstream VSL is robustly the best strategy.

**What that percentage measures.** `net_total_timeloss_veh_s` sums the edgeData
`timeLoss` of the modelled edges. Ramp metering holds vehicles at the entry,
where they are not yet on a modelled edge, so part of the saving is a transfer
rather than a reduction. In the same rerun, peak `tripinfo_completed_depart_delay_s`
rises 645,635.7 → 868,079.7 veh-s (+34.5%); the two together rise +14.6%. Off-peak
the transfer dominates: 86,202.4 → 439,107.9 veh-s (+409.4%), +141.2% combined.
The peak network also clears 300 s later (3,503 → 3,803 s) and the flow proxy
`throughput_veh_h` falls 7.95%. Every one of these numbers is a division on the
two committed CSVs, and `tests/test_documented_numbers.py` recomputes them.

Capacity (field): weaving section ≈ **5,060 veh/h** — 3,627 veh counted over
43 min (2,348 mainline + 1,279 merge), re-derived from the workbook by
`scripts/counts/capacity_from_counts.py`. Four things limit it. It is the mean
flow over the survey, not a flow measured while the section was discharging a
queue. The workbook divides by 43 minutes although only 42 one-minute rows hold
data; over those 42 rows the same total gives 5,181.4 veh/h, and the script prints
both. Row 1 of the sheet notes that this merge-point tally is less accurate than
the exit tally. And the tallies were produced by the counting code as it stood
before the `point_on_segment` fix in this repository and have not been recounted,
because the source video is not here; [data/counts/README.md](data/counts/README.md)
sets out which of the eight counting lines that predicate affected.

---

## Citation

If you reuse this material, please cite the course and authors, e.g.:

```text
Group 12 (Leong, Luo, Wang, Zhao). Analysis and Mitigation of the AYE
Westbound Weaving Bottleneck. CE5203 Traffic Flow and Control, NUS, 2026.
```

---

## Licence and report

- `LICENSE` (MIT) covers the scripts and SUMO configs I wrote; the report source
  under `latex/` remains the joint work of Group 12 and is not covered by it.
- Coursework released for **educational / portfolio** use. Do not redistribute raw
  field videos or third-party lecture slides.
- SUMO is under EPL-2.0; YOLO/Ultralytics under their respective licences.
- The compiled group report PDF has been removed from this repository because it
  carried the four authors' student IDs; the LaTeX source under `latex/` is kept
  with the IDs removed. The PDF is available on request.
