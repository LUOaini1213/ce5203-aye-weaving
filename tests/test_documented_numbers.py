"""Every number quoted in README.md must still follow from the committed CSVs.

The repository verifies its raw artifacts by hash, but prose is where numbers
usually rot: a table gets edited, a percentage is copied by hand, and nothing
complains. These tests recompute each quoted figure from
`results/sumo_12scenarios_results.csv` and
`results/reproduction-2026-09-12/summary.csv`, format it the way the README
does, and require the resulting text to be present. Change either the CSV or
the sentence and the suite goes red.

`latex/data_macros.tex` is covered the same way, by regenerating it.
"""
import csv
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "latex"))
sys.path.insert(0, str(ROOT / "scripts" / "counts"))
from make_data_macros import load_rows, render, TARGET  # noqa: E402
from capacity_from_counts import analyse  # noqa: E402

MINUS = "−"  # the README uses a real minus sign, not a hyphen
HISTORICAL = ROOT / "results" / "sumo_12scenarios_results.csv"
RERUN = ROOT / "results" / "reproduction-2026-09-12" / "summary.csv"
README = ROOT / "README.md"
SCENARIOS = ("base", "vsl", "vsl_up", "rm", "vsl_rm", "vsl_up_rm")


def table(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row["period"], row["scenario"]): row for row in csv.DictReader(handle)}


def change_pct(rows, period, column):
    base = float(rows[(period, "base")][column])
    metered = float(rows[(period, "rm")][column])
    return (metered - base) / base * 100.0


def as_written(field):
    """Group thousands in a CSV field, leaving its decimals exactly as recorded."""
    whole, _, frac = field.partition(".")
    grouped = f"{int(whole):,}"
    return f"{grouped}.{frac}" if frac else grouped


def signed_pct(value, digits):
    sign = MINUS if value < 0 else "+"
    return f"{sign}{abs(value):.{digits}f}%"


class DocumentedNumberTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.historical = table(HISTORICAL)
        cls.rerun = table(RERUN)
        cls.readme = README.read_text(encoding="utf-8")

    def assertQuoted(self, text, what):
        # assertTrue, not assertIn: a failing assertIn would print the whole README.
        self.assertTrue(text in self.readme,
                        f"README.md no longer quotes {what} as {text!r}")

    def test_ramp_metering_percentages_in_both_tables(self):
        expected = {
            "peak time loss, historical": (self.historical, "peak", "net_total_timeloss_veh_s", 1),
            "peak weaving delay, historical": (self.historical, "peak", "avg_delay_s_veh", 1),
            "peak time loss, rerun": (self.rerun, "peak", "net_total_timeloss_veh_s", 2),
            "peak weaving delay, rerun": (self.rerun, "peak", "avg_delay_s_veh", 2),
            "off-peak time loss, historical": (self.historical, "offpeak", "net_total_timeloss_veh_s", 2),
            "off-peak weaving delay, historical": (self.historical, "offpeak", "avg_delay_s_veh", 2),
            "off-peak time loss, rerun": (self.rerun, "offpeak", "net_total_timeloss_veh_s", 2),
            "off-peak weaving delay, rerun": (self.rerun, "offpeak", "avg_delay_s_veh", 2),
        }
        for what, (rows, period, column, digits) in expected.items():
            value = change_pct(rows, period, column)
            self.assertLess(value, 0, f"{what} is no longer an improvement")
            self.assertQuoted(signed_pct(value, digits), what)

    def test_headline_uses_the_rerun_figure_the_committed_evidence_supports(self):
        value = change_pct(self.rerun, "peak", "net_total_timeloss_veh_s")
        self.assertQuoted(f"total time loss {abs(value):.2f}%", "the front-matter headline")

    def test_the_absolute_pairs_behind_both_peak_columns_are_quoted(self):
        """A reader must be able to redo the division, not just read the percentage."""
        base = float(self.historical[("peak", "base")]["net_total_timeloss_veh_s"])
        metered = float(self.historical[("peak", "rm")]["net_total_timeloss_veh_s"])
        self.assertEqual((base, metered), (143396.6, 110833.5))
        for label, rows in (("historical", self.historical), ("rerun", self.rerun)):
            for column in ("net_total_timeloss_veh_s", "avg_delay_s_veh"):
                pair = " → ".join(as_written(rows[("peak", scenario)][column])
                                       for scenario in ("base", "rm"))
                self.assertQuoted(pair, f"the {label} peak {column} pair")

    def test_departure_delay_counterweight_is_recomputed(self):
        for period, digits in (("peak", 1), ("offpeak", 1)):
            base = self.rerun[(period, "base")]
            metered = self.rerun[(period, "rm")]
            delay_base = float(base["tripinfo_completed_depart_delay_s"])
            delay_rm = float(metered["tripinfo_completed_depart_delay_s"])
            self.assertQuoted(f"{delay_base:,.1f} → {delay_rm:,.1f}",
                              f"{period} departure delay")
            self.assertQuoted(signed_pct((delay_rm - delay_base) / delay_base * 100, digits),
                              f"{period} departure delay change")
            loss_base = float(base["net_total_timeloss_veh_s"])
            loss_rm = float(metered["net_total_timeloss_veh_s"])
            combined = ((loss_rm + delay_rm) - (loss_base + delay_base)) / (loss_base + delay_base) * 100
            self.assertQuoted(signed_pct(combined, 1), f"{period} combined change")

    def test_clearance_time_and_throughput_proxy(self):
        base = self.rerun[("peak", "base")]
        metered = self.rerun[("peak", "rm")]
        end_base = float(base["simulation_end_s"])
        end_rm = float(metered["simulation_end_s"])
        self.assertQuoted(f"{end_base:,.0f} → {end_rm:,.0f} s", "peak clearance time")
        self.assertQuoted(f"{end_rm - end_base:,.0f} s later", "peak clearance delta")
        throughput = change_pct(self.rerun, "peak", "throughput_veh_h")
        self.assertLess(throughput, 0)
        self.assertQuoted(f"falls {abs(throughput):.2f}%", "peak throughput proxy")

    def test_ramp_metering_is_the_best_of_the_six_in_both_tables(self):
        """The README claims a ranking, not only a percentage."""
        for label, rows in (("historical", self.historical), ("rerun", self.rerun)):
            for period in ("peak", "offpeak"):
                loss = {scenario: float(rows[(period, scenario)]["net_total_timeloss_veh_s"])
                        for scenario in SCENARIOS}
                self.assertEqual(min(loss, key=loss.get), "rm",
                                 f"{label} {period}: ramp metering is no longer the best")
                self.assertGreater(loss["vsl"], loss["base"],
                                   f"{label} {period}: in-section VSL is no longer worse than base")
                self.assertGreater(loss["vsl_rm"], loss["rm"],
                                   f"{label} {period}: VSL+RM is no longer worse than RM alone")

    def test_capacity_is_recomputed_from_the_tally_workbook(self):
        result = analyse(ROOT / "data" / "counts" / "peak_merge.xlsx")
        self.assertEqual(result["total_veh"], result["workbook_total_veh"])
        self.assertEqual(result["total_veh"], 3627)
        self.assertEqual(result["survey_minutes"], 43.0)
        self.assertAlmostEqual(result["capacity_veh_h"], 5060.9302325581393, places=6)
        self.assertQuoted(f"{result['total_veh']:,} veh", "the counted vehicle total")
        self.assertQuoted(f"{result['survey_minutes']:g} min", "the survey duration")
        self.assertQuoted(f"{result['capacity_veh_h']:,.1f} veh/h", "the empirical capacity")
        self.assertQuoted(f"{result['by_group']['main road']:,} mainline + "
                          f"{result['by_group']['merge']:,} merge",
                          "the mainline and merge subtotals")

    def test_the_counts_are_attributed_to_the_code_that_produced_them(self):
        """The tallies predate the point_on_segment fix; both files must say so."""
        counts_readme = (ROOT / "data" / "counts" / "README.md").read_text(encoding="utf-8")
        self.assertIn("point_on_segment", counts_readme,
                      "data/counts/README.md no longer names the corrected predicate")
        self.assertIn("been recounted", counts_readme,
                      "data/counts/README.md no longer says the tallies were not recounted")
        self.assertIn("point_on_segment", self.readme,
                      "README.md no longer says which counting code produced the tallies")

    def test_data_macros_are_regenerated_from_the_historical_csv(self):
        self.assertEqual(TARGET.read_text(encoding="utf-8"), render(load_rows(HISTORICAL)),
                         "latex/data_macros.tex is stale; run scripts/latex/make_data_macros.py")

    def test_capacity_line_in_the_figures_comes_from_the_workbook(self):
        source = (ROOT / "latex" / "make_figures.py").read_text(encoding="utf-8")
        self.assertTrue("capacity_from_workbook" in source,
                        "make_figures.py no longer derives the capacity line from the workbook")
        self.assertFalse("cap = 5060" in source,
                         "the fundamental-diagram capacity line is hard-coded again")
        self.assertFalse("sumo_runs" in source,
                         "make_figures.py still looks for the sumo_runs/ folder that never existed")


if __name__ == "__main__":
    unittest.main()
