# CE5203 · AYE Westbound Weaving Bottleneck

**Analysis and Mitigation of the AYE Westbound Weaving Bottleneck**  
NUS CE5203 *Traffic Flow and Control* — Course Project (Spring 2026) · Group 12

| | |
|---|---|
| **Site** | Singapore AYE westbound, Exit 9 → Exit 11 (≈373 m weaving section) |
| **Pipeline** | Field video → **YOLOv11** counts/speeds → **SUMO** microsimulation → VSL / RM / VSL+RM |
| **Historical course result** | Peak-period ramp metering cut network **total time loss by 22.7%** in the original table; September rerun differs |
| **Report** | [latex/report.tex](latex/report.tex) |

> Course group project. Public mirror for portfolio / reproducibility.  
> Contributors: Leong Sio Kuan · **Luo Wenjie** · Wang Xu · Zhao Jiaqing  
> **My part (Luo Wenjie):** the YOLOv11 counting pipeline (`scripts/vision/yolo_line_count.py`, the four-point tallies in `data/counts/`) and the SUMO side: network build, demand and speed calibration, and the 12 scenario runs behind `results/`. Site selection, capacity analysis and the report were joint work.

**12 September 2026: the original control runner was recovered from the course submission archive.**
All six strategies can now be simulated for both demand periods, with control
traces, raw XML, metrics and provenance. A fresh twelve-scenario run is committed.
It **does not reproduce the historical −22.7% / −7.7% numbers**; the new and old
results are [compared explicitly](results/reproduction-2026-09-12/comparison.md).
[Recovery details and metric limitations](docs/REPRODUCTION.md) ·
[![SUMO reproduction](https://github.com/LUOaini1213/ce5203-aye-weaving/actions/workflows/sumo-reproduction.yml/badge.svg)](https://github.com/LUOaini1213/ce5203-aye-weaving/actions/workflows/sumo-reproduction.yml)

```bash
python scripts/sumo/run_scenarios.py --all --jobs 2 --output runs/full --compress-xml
python scripts/sumo/check_run.py runs/full --require-complete
python scripts/sumo/compare_history.py runs/full
```

Requires SUMO and TraCI tools (`SUMO_HOME` or `--sumo-binary`). Uses the recovered
0.5-second step, seed 42 and 0.15/0.20 occupancy thresholds. No model or dataset
download is needed; the published network and demand files are sufficient.

---

## What this project does

1. **Identify** a recurring weaving bottleneck on AYE WB (on-ramp merge vs off-ramp diverge).
2. **Measure** peak (46 min recorded, 43 valid) and off-peak (62 recorded, 60 valid) demand with a **YOLOv11** multi-line counting pipeline at four points.
3. **Estimate** weaving-section capacity ≈ **5,060 veh/h** from field counts.
4. **Calibrate** a SUMO network to YOLO-derived demand/speeds.
5. **Evaluate** control strategies over **12 runs**: Variable Speed Limit (VSL), Ramp Metering (RM), VSL+RM, plus upstream VSL placement, under peak and off-peak demand.
6. **Historical report conclusion:** ramp metering alone (occupancy threshold ≈20% downstream) reduced peak network total time loss **22.7%** and weaving delay **7.7%**, with negligible off-peak gain. These are original course results; the September rerun has different numerical effects, documented above.

---

## Repository layout

```text
docs/                 Runner recovery and reproduction notes (group report PDF not published)
sumo/peak/            Peak demand network + routes + sample outputs
sumo/offpeak/         Off-peak demand network + routes + sample outputs
scripts/vision/       YOLOv11 line-count sample (OpenVINO export path)
scripts/sumo/         Recovered VSL / RM controls, twelve-scenario runner and verification
scripts/analysis/     Optional React dashboards (figure generation lives in latex/make_figures.py)
data/counts/          Aggregated count tables (xlsx) used for demand
results/              Historical tables + separately identified September 2026 rerun
latex/                Report source + figures
```

**Not included (size / privacy):** raw field videos, YOLO weights, OpenVINO model folder. Paths in the vision script are placeholders — point them at your local files.

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

Historical report figures regenerate from the committed data:
`pip install -r requirements.txt && python latex/make_figures.py` (writes
`latex/figs/`; 8 of the 10 figures). The original two per-edge time-series inputs
remain unavailable, so those figures stay as committed PDFs. The new runner
now saves per-edge outputs for all strategies; these are new observations and
must not be substituted into the historical report without labelling the change.

---

## Quick start · vision sample

```bash
pip install ultralytics opencv-python numpy
# Place a video and model export next to the script, then edit paths in:
#   scripts/vision/yolo_line_count.py
python scripts/vision/yolo_line_count.py
```

The script uses Ultralytics YOLO + ByteTrack-style counting lines for multi-class vehicle tallies (car / motorcycle / bus / truck).

---

## Results (summary)

From `results/sumo_12scenarios_results.csv` and the report:

| Period | Best strategy | Network total time loss | Weaving avg delay |
|--------|---------------|-------------------------|-------------------|
| Peak | Ramp metering | **−22.7%** vs do-nothing | **−7.7%** |
| Off-peak | RM | negligible change | — |
| Both | In-section VSL only | often **worse** | — |

Both peak percentages are arithmetic on the CSV: `net_total_timeloss_veh_s` 143,396.6 → 110,833.5 (−22.7 %) and `avg_delay_s_veh` 11.89 → 10.97 (−7.7 %) for `peak,base` vs `peak,rm`.

Capacity (field): weaving section ≈ **5,060 veh/h**.

---

## Citation

If you reuse this material, please cite the course and authors, e.g.:

```text
Group 12 (Leong, Luo, Wang, Zhao). Analysis and Mitigation of the AYE
Westbound Weaving Bottleneck. CE5203 Traffic Flow and Control, NUS, 2026.
```

---

## License

Coursework released for **educational / portfolio** use.  
Do not redistribute raw field videos or third-party lecture slides.  
SUMO is under EPL-2.0; YOLO/Ultralytics under their respective licenses.

## Report and licence

The compiled group report PDF has been removed from this repository because it carried the four authors' student IDs; the LaTeX source under `latex/` is kept with the IDs removed. The PDF is available on request. `LICENSE` (MIT) covers the scripts and SUMO configs I wrote; the report source remains the joint work of Group 12.
