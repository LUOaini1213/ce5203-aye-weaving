"""check_rerun.py must accept a run that matches the committed one and reject drift.

CI uses it to compare full-horizon SUMO reruns with the committed evidence. A
comparison that can never fail proves nothing, so these tests feed it the
committed run itself (must pass) and edited copies of it (must fail), without
needing SUMO.
"""
import csv
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "sumo"))
from check_rerun import REFERENCE, check  # noqa: E402

KEEP = {("peak", "base"), ("peak", "rm"), ("peak", "vsl_up")}


class CheckRerunTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.run = self.tmp / "fresh"
        self.run.mkdir()
        shutil.copy(REFERENCE / "run_manifest.json", self.run / "run_manifest.json")
        with (REFERENCE / "summary.csv").open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            self.fields = reader.fieldnames
            self.rows = [r for r in reader if (r["period"], r["scenario"]) in KEEP]
        self.write()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self):
        with (self.run / "summary.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=self.fields)
            writer.writeheader()
            writer.writerows(self.rows)

    def row(self, scenario):
        return next(r for r in self.rows if r["scenario"] == scenario)

    def test_the_committed_run_passes_against_itself(self):
        _, problems = check([self.run])
        self.assertEqual(problems, [])

    def test_a_drifted_time_loss_fails(self):
        row = self.row("rm")
        row["net_total_timeloss_veh_s"] = str(float(row["net_total_timeloss_veh_s"]) * 1.05)
        self.write()
        _, problems = check([self.run])
        self.assertTrue(any("net_total_timeloss_veh_s differs" in p for p in problems), problems)

    def test_a_flipped_sign_fails_even_within_a_loose_tolerance(self):
        # Make RM's edge + entry total lower than base: the stated sign no longer holds.
        row = self.row("rm")
        row["tripinfo_completed_depart_delay_s"] = "100000.0"
        self.write()
        _, problems = check([self.run], tolerance_pct=1000.0)
        self.assertTrue(any("no longer raises" in p for p in problems), problems)

    def test_a_smoke_run_is_refused(self):
        manifest = json.loads((self.run / "run_manifest.json").read_text(encoding="utf-8"))
        manifest["parameters"]["end"] = 120
        (self.run / "run_manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        _, problems = check([self.run])
        self.assertTrue(any("smoke run" in p for p in problems), problems)


if __name__ == "__main__":
    unittest.main()
