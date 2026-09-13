# Count tables

Aggregated vehicle counts used to build SUMO demand (from the YOLOv11 pipeline + QA).

| File | Description |
|------|-------------|
| `peak_exit.xlsx` / `peak_merge.xlsx` | Peak period exit / merge counts |
| `offpeak_exit.xlsx` / `offpeak_merge.xlsx` | Off-peak exit / merge counts |

Raw videos and full per-frame logs are **not** in this repository.

## The empirical capacity figure, and how to check it

`peak_merge.xlsx`, sheet `Results`, is the source of the ≈5,060 veh/h weaving
capacity quoted in the report and the README. Rather than opening the workbook
and reading a formula, run:

```bash
python scripts/counts/capacity_from_counts.py
```

It re-adds the sheet from its per-class columns with the standard library only,
cross-checks the result against the totals the workbook itself stores, and reads
the survey duration out of the workbook's own `* 60 / 43` rate formula:

```text
total               3627 veh   (workbook stores 3627)
survey duration     43 min (from the workbook formula)
capacity            5060.9302 veh/h
```

Facts a reader of the sheet should have up front:

- The `total (w/o motorcycles)` column is **cars + buses + trucks** for the
  mainline and the merge. Motorcycles are tallied in their own columns and are
  **not** in that total, and row 1 of the sheet carries the survey note
  `Number of motorcycles is not accurate`.
- Row 1 also carries `This statistics is less accurate than statistics at exit`,
  which is about this merge sheet relative to the exit sheet.
- 42 one-minute rows hold data; rows for 720 s, 780 s and 840 s are empty. The
  sheet normalises the total by 43 minutes.
- Six cells in the columns that feed the total are negative — `D9`, `D22`, `I8`,
  `I32`, `J8`, `J20`, net −10 veh over the 42 rows. They are left exactly as
  recorded, and the script prints them so the effect is visible rather than
  buried. (The motorcycle columns, which do not enter the total, hold seven
  more.)

`tests/test_documented_numbers.py` asserts that 3,627, 43 min and 5,060.9 veh/h
still come out of the workbook and are still the numbers the README quotes.

## Which version of the counting code produced these tables

These tallies were produced by the line-counting pipeline as it stood **before**
`point_on_segment` was corrected in `scripts/vision/line_counting.py`. The
earlier predicate compared a boolean against `0`, so a point inside a line's
bounding box on one side of that line was read as lying on it, and a frame that
crossed nothing could be recorded as a crossing. Lines 1 and 2 are horizontal,
their bounding boxes are degenerate and they are unaffected; lines 3-8 are the
diagonal merge and exit movements, with 50x40 px boxes, and are the ones
exposed. Because a track is counted at most once per line and once per group, a
spurious hit can also take the place of the count the real crossing would have
produced, so the effect is not purely additive.

The workbooks have **not** been recounted: the source video and the per-frame
logs are not in this repository, so there is nothing here to recount from. The
counts above, and the ≈5,060 veh/h derived from them, are therefore the output
of that earlier code. The corrected predicate is covered by
`tests/test_line_counting.py` and applies to later runs.
