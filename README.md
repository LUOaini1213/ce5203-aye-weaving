# CE5203 · AYE Westbound Weaving Bottleneck

**Analysis and Mitigation of the AYE Westbound Weaving Bottleneck**  
NUS CE5203 *Traffic Flow and Control* — Course Project (Spring 2026) · Group 12

| | |
|---|---|
| **Site** | Singapore AYE westbound, Exit 9 → Exit 11 (≈373 m weaving section) |
| **Pipeline** | Field video → **YOLOv11** counts/speeds → **SUMO** microsimulation → VSL / RM / VSL+RM |
| **Key result** | Peak-period ramp metering cut network **total time loss by 22.7%** |
| **Report** | [latex/report.tex](latex/report.tex) |

> Course group project. Public mirror for portfolio / reproducibility.  
> Contributors: Leong Sio Kuan · **Luo Wenjie** · Wang Xu · Zhao Jiaqing

---

## What this project does

1. **Identify** a recurring weaving bottleneck on AYE WB (on-ramp merge vs off-ramp diverge).
2. **Measure** peak (≈46 min) and off-peak (≈62 min) demand with a **YOLOv11** multi-line counting pipeline at four points.
3. **Estimate** weaving-section capacity ≈ **5,060 veh/h** from field counts.
4. **Calibrate** a SUMO network to YOLO-derived demand/speeds.
5. **Evaluate** control strategies over **12 runs**: Variable Speed Limit (VSL), Ramp Metering (RM), VSL+RM, plus upstream VSL placement, under peak and off-peak demand.
6. **Recommend** ramp metering alone (ALINEA-style occupancy threshold ≈20% downstream): peak network total time loss **−22.7%**, weaving delay **−7.7%**; off-peak gain negligible; in-section VSL can hurt.

---

## Repository layout

```text
docs/                 Final group report (PDF)
sumo/peak/            Peak demand network + routes + sample outputs
sumo/offpeak/         Off-peak demand network + routes + sample outputs
scripts/vision/       YOLOv11 line-count sample (OpenVINO export path)
scripts/analysis/     Figure generation + optional React dashboards
data/counts/          Aggregated count tables (xlsx) used for demand
results/              Scenario comparison tables
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

Scenario-level control configs used for the 12-run table live in the full submission package; this repo publishes the **calibrated base networks**, **demand routes**, **detectors**, and **reported results**. See `results/` and the PDF for VSL/RM settings and metrics.

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
