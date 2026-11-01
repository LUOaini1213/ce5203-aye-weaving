"""Unit tests for the counting-line geometry used by the video tallies.

Everything here runs on hand-written pixel tracks: no video, no model export,
no GPU, and no third-party import, so it runs in CI next to the SUMO control
tests.
"""
import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "vision"))
from line_counting import (  # noqa: E402
    AYE_WB_LINES,
    AYE_WB_LINE_GROUPS,
    CountingLine,
    LineCounter,
    VEHICLE_CLASS_NAMES,
    direction_matches,
    orientation,
    point_on_segment,
    segments_intersect,
)

CLASSES = tuple(VEHICLE_CLASS_NAMES.values())
# One of the diagonal survey lines, reused below because diagonals are where
# the collinearity test actually bites.
DIAGONAL = ((728, 138), (678, 178))


class GeometryTests(unittest.TestCase):
    def test_point_on_segment_requires_collinearity_not_just_the_bounding_box(self):
        a, b = DIAGONAL
        # Inside the bounding box, off the line, on the negative-cross side.
        # A membership test written as `cross(...) == 0` on a boolean-valued
        # helper accepts this point, because False == 0.
        self.assertEqual(orientation(a, b, (690, 170)), -1)
        self.assertFalse(point_on_segment((690, 170), a, b))
        # Same box, positive-cross side.
        self.assertEqual(orientation(a, b, (700, 140)), 1)
        self.assertFalse(point_on_segment((700, 140), a, b))
        # Genuinely on the segment, and on its extension beyond an endpoint.
        self.assertTrue(point_on_segment((703, 158), a, b))
        self.assertTrue(point_on_segment(a, a, b))
        self.assertFalse(point_on_segment((628, 218), a, b))

    def test_segments_intersect_covers_crossing_touching_and_parallel_cases(self):
        a, b = DIAGONAL
        self.assertTrue(segments_intersect((690, 130), (700, 190), a, b))
        self.assertFalse(segments_intersect((692, 172), (690, 170), a, b))
        # A step that ends exactly on the line counts as touching it.
        self.assertTrue(segments_intersect((690, 130), (703, 158), a, b))
        # Collinear overlap.
        self.assertTrue(segments_intersect((703, 158), (690, 168), a, b))
        # Parallel, offset.
        self.assertFalse(segments_intersect((738, 138), (688, 178), a, b))

    def test_direction_matches_uses_image_coordinates(self):
        self.assertTrue(direction_matches((10, 10), (11, 10), "right"))
        self.assertFalse(direction_matches((10, 10), (9, 10), "right"))
        self.assertTrue(direction_matches((10, 10), (9, 10), "left"))
        self.assertTrue(direction_matches((10, 10), (10, 11), "down"))
        self.assertTrue(direction_matches((10, 11), (10, 10), "up"))
        # A pure sideways step never satisfies a vertical line.
        self.assertFalse(direction_matches((10, 10), (11, 10), "down"))
        with self.assertRaises(ValueError):
            direction_matches((0, 0), (1, 1), "sideways")

    def test_counting_line_rejects_bad_configuration(self):
        with self.assertRaises(ValueError):
            CountingLine((0, 0), (10, 0), "northwest")
        with self.assertRaises(ValueError):
            CountingLine((5, 5), (5, 5), "down")


class LineCounterTests(unittest.TestCase):
    def make_counter(self):
        lines = [
            CountingLine((0, 100), (200, 100), "down", name="cordon"),
            CountingLine((0, 200), (200, 200), "down", name="second"),
        ]
        return LineCounter(lines, groups=(), classes=CLASSES)

    def test_forward_crossing_is_counted_once_per_class(self):
        counter = self.make_counter()
        self.assertEqual(counter.update(1, "car", (50, 90)), ())  # first sighting
        self.assertEqual(counter.update(1, "car", (50, 110)), (0,))
        self.assertEqual(counter.counts[0]["car"], 1)
        self.assertEqual(counter.total(), 1)

    def test_crossing_against_the_line_direction_is_not_counted(self):
        counter = self.make_counter()
        counter.update(2, "truck", (50, 110))
        self.assertEqual(counter.update(2, "truck", (50, 90)), ())
        self.assertEqual(counter.total(), 0)

    def test_the_same_track_crossing_the_same_line_twice_counts_once(self):
        counter = self.make_counter()
        counter.update(3, "bus", (50, 90))
        counter.update(3, "bus", (50, 110))
        counter.update(3, "bus", (50, 90))   # back over, wrong direction
        counter.update(3, "bus", (50, 130))  # forward again
        self.assertEqual(counter.counts[0]["bus"], 1)

    def test_two_ungrouped_lines_crossed_in_one_step_both_count(self):
        counter = self.make_counter()
        counter.update(4, "car", (50, 50))
        self.assertEqual(counter.update(4, "car", (50, 250)), (0, 1))
        self.assertEqual(counter.total(), 2)

    def test_grouped_lines_tally_a_track_only_once(self):
        lines = [
            CountingLine((0, 100), (200, 100), "down"),
            CountingLine((0, 200), (200, 200), "down"),
            CountingLine((0, 300), (200, 300), "down"),
        ]
        counter = LineCounter(lines, groups=((0, 1, 2),), classes=CLASSES)
        counter.update(5, "car", (50, 50))
        self.assertEqual(counter.update(5, "car", (50, 150)), (0,))
        self.assertEqual(counter.update(5, "car", (50, 350)), ())
        self.assertEqual(counter.total(), 1)
        # A different track is unaffected by the first one's group state.
        counter.update(6, "car", (50, 250))
        self.assertEqual(counter.update(6, "car", (50, 350)), (2,))
        self.assertEqual(counter.total(), 2)

    def test_unknown_class_advances_dedup_state_without_a_tally(self):
        counter = self.make_counter()
        counter.update(7, "bicycle", (50, 90))
        self.assertEqual(counter.update(7, "bicycle", (50, 110)), (0,))
        self.assertEqual(counter.line_total(0), 0)
        self.assertNotIn("bicycle", counter.counts[0])

    def test_reset_clears_tallies_and_dedup_state(self):
        counter = self.make_counter()
        counter.update(8, "car", (50, 90))
        counter.update(8, "car", (50, 110))
        counter.reset()
        self.assertEqual(counter.total(), 0)
        counter.update(8, "car", (50, 90))
        self.assertEqual(counter.update(8, "car", (50, 110)), (0,))
        self.assertEqual(counter.total(), 1)

    def test_group_indices_are_validated(self):
        with self.assertRaises(ValueError):
            LineCounter(list(AYE_WB_LINES), groups=((0, 99),), classes=CLASSES)
        with self.assertRaises(ValueError):
            LineCounter([], classes=CLASSES)


class SurveyConfigurationTests(unittest.TestCase):
    def test_survey_configuration_is_consistent(self):
        counter = LineCounter(list(AYE_WB_LINES), groups=AYE_WB_LINE_GROUPS, classes=CLASSES)
        self.assertEqual(len(counter.lines), 8)
        self.assertEqual(sorted(AYE_WB_LINE_GROUPS[0]), [2, 3, 4, 5, 6, 7])
        self.assertEqual(counter.total(), 0)

    def test_a_track_drifting_inside_a_diagonal_bounding_box_is_not_tallied(self):
        """Regression: the drift never touches the line, so nothing may count.

        Both positions sit inside the bounding box of survey line 3 but on the
        same side of it. A collinearity test that treats "not on the positive
        side" as "on the line" turns this drift into a crossing and inflates
        the ramp tallies.
        """
        counter = LineCounter(list(AYE_WB_LINES), groups=AYE_WB_LINE_GROUPS, classes=CLASSES)
        counter.update(11, "car", (692, 172))
        self.assertEqual(counter.update(11, "car", (690, 170)), ())
        self.assertEqual(counter.total(), 0)

    def test_a_leftward_track_actually_cutting_the_diagonal_is_tallied_once(self):
        counter = LineCounter(list(AYE_WB_LINES), groups=AYE_WB_LINE_GROUPS, classes=CLASSES)
        counter.update(12, "motorcycle", (720, 170))
        self.assertEqual(counter.update(12, "motorcycle", (690, 150)), (2,))
        self.assertEqual(counter.counts[2]["motorcycle"], 1)
        # The mirrored "right" copy of the same segment must stay at zero.
        self.assertEqual(counter.counts[5]["motorcycle"], 0)


if __name__ == "__main__":
    unittest.main()
