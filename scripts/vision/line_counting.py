#!/usr/bin/env python3
"""Counting-line geometry and de-duplication for the AYE video tallies.

This module is the part of the vision pipeline that decides *whether a tally
is incremented*: segment intersection, travel direction, and the two levels of
de-duplication (per line and per line group).  It is deliberately free of
third-party dependencies -- no OpenCV, no Ultralytics, no NumPy -- so that it
can be imported and unit-tested without a video, a model export or a GPU.

`yolo_line_count.py` supplies the detections; everything below only ever sees
integer pixel coordinates.

Coordinates follow the image convention: x grows to the right, y grows
downward, so "down" means an increasing y.
"""
from __future__ import annotations

__all__ = [
    "AYE_WB_LINES",
    "AYE_WB_LINE_GROUPS",
    "CountingLine",
    "LineCounter",
    "VEHICLE_CLASS_IDS",
    "VEHICLE_CLASS_NAMES",
    "cross",
    "direction_matches",
    "orientation",
    "point_on_segment",
    "segments_intersect",
]

DIRECTIONS = ("left", "right", "up", "down")


def cross(origin, a, b):
    """Z component of (a - origin) x (b - origin).

    Returns a number, not a boolean: the sign says which side of the ray
    origin->a the point b falls on, and exactly zero means collinear.
    """
    return (a[0] - origin[0]) * (b[1] - origin[1]) - (a[1] - origin[1]) * (b[0] - origin[0])


def orientation(a, b, c):
    """1 if a->b->c turns one way, -1 the other way, 0 when collinear."""
    value = cross(a, b, c)
    if value > 0:
        return 1
    if value < 0:
        return -1
    return 0


def point_on_segment(p, a, b):
    """True only when p is collinear with a-b *and* inside its bounding box."""
    if orientation(a, b, p) != 0:
        return False
    return (min(a[0], b[0]) <= p[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= p[1] <= max(a[1], b[1]))


def segments_intersect(a, b, c, d):
    """True when segment a-b touches or crosses segment c-d.

    Endpoint contact and collinear overlap count as an intersection, which is
    what a counting line needs: a track that lands exactly on the line has
    crossed it.
    """
    o1 = orientation(a, b, c)
    o2 = orientation(a, b, d)
    o3 = orientation(c, d, a)
    o4 = orientation(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    if o1 == 0 and point_on_segment(c, a, b):
        return True
    if o2 == 0 and point_on_segment(d, a, b):
        return True
    if o3 == 0 and point_on_segment(a, c, d):
        return True
    if o4 == 0 and point_on_segment(b, c, d):
        return True
    return False


def direction_matches(prev, curr, direction):
    """True when the step prev->curr moves the required way along one axis."""
    dx = curr[0] - prev[0]
    dy = curr[1] - prev[1]
    if direction == "right":
        return dx > 0
    if direction == "left":
        return dx < 0
    if direction == "down":
        return dy > 0
    if direction == "up":
        return dy < 0
    raise ValueError(f"Unknown direction: {direction!r}")


class CountingLine:
    """One oriented counting line."""

    __slots__ = ("p1", "p2", "direction", "name")

    def __init__(self, p1, p2, direction, name=None):
        if direction not in DIRECTIONS:
            raise ValueError(f"direction must be one of {DIRECTIONS}, got {direction!r}")
        if tuple(p1) == tuple(p2):
            raise ValueError("a counting line needs two distinct endpoints")
        self.p1 = (int(p1[0]), int(p1[1]))
        self.p2 = (int(p2[0]), int(p2[1]))
        self.direction = direction
        self.name = name

    def is_crossed_by(self, prev, curr):
        """True when the step prev->curr cuts this line in the required direction."""
        if not segments_intersect(prev, curr, self.p1, self.p2):
            return False
        return direction_matches(prev, curr, self.direction)

    def __repr__(self):  # pragma: no cover - debugging aid
        return f"CountingLine({self.p1}, {self.p2}, {self.direction!r}, name={self.name!r})"


class LineCounter:
    """Per-line, per-class tallies with two levels of de-duplication.

    A tracked object is counted at most once per line, and at most once per
    *line group*.  Groups exist because the merge and exit movements are drawn
    as several short segments plus a left/right pair over the same physical
    gantry: without the group rule, one vehicle would be tallied several times
    while traversing it.
    """

    def __init__(self, lines, groups=(), classes=()):
        self.lines = list(lines)
        if not self.lines:
            raise ValueError("at least one counting line is required")
        self.groups = [tuple(int(i) for i in group) for group in groups]
        for group in self.groups:
            for index in group:
                if not 0 <= index < len(self.lines):
                    raise ValueError(f"line index {index} in a group is out of range")
        self.classes = list(classes)
        self._line_groups = [[] for _ in self.lines]
        for g_index, group in enumerate(self.groups):
            for line_index in group:
                self._line_groups[line_index].append(g_index)
        self.reset()

    def reset(self):
        self.counts = [dict.fromkeys(self.classes, 0) for _ in self.lines]
        self._prev = {}
        self._line_seen = [set() for _ in self.lines]
        self._group_seen = [set() for _ in self.groups]

    def update(self, track_id, class_name, position):
        """Feed one detection; return the indices of the lines it incremented.

        The first sighting of a track only records its position -- a crossing
        needs two consecutive positions to be defined.
        """
        position = (int(position[0]), int(position[1]))
        counted = []
        prev = self._prev.get(track_id)
        if prev is not None:
            for index, line in enumerate(self.lines):
                if not line.is_crossed_by(prev, position):
                    continue
                if track_id in self._line_seen[index]:
                    continue
                if any(track_id in self._group_seen[g] for g in self._line_groups[index]):
                    continue
                self._line_seen[index].add(track_id)
                for g in self._line_groups[index]:
                    self._group_seen[g].add(track_id)
                if class_name in self.counts[index]:
                    self.counts[index][class_name] += 1
                counted.append(index)
        self._prev[track_id] = position
        return tuple(counted)

    def line_total(self, index):
        return sum(self.counts[index].values())

    def total(self):
        return sum(self.line_total(i) for i in range(len(self.lines)))

    def totals_by_class(self):
        merged = dict.fromkeys(self.classes, 0)
        for counts in self.counts:
            for name, value in counts.items():
                merged[name] = merged.get(name, 0) + value
        return merged


# ---------------------------------------------------------------------------
# Site configuration for the AYE westbound survey
# ---------------------------------------------------------------------------
# Pixel coordinates of the counting lines drawn on the survey camera view.
# Lines 1-2 are two collinear horizontal segments at y = 425 that together span
# the frame.  Lines 3-8 are the same three-segment polyline from (728, 138) to
# (708, 425), listed once for the "left" direction and once for "right"; all six
# share one group so a vehicle traversing the polyline is tallied once.
# Names match the `line_<n>_<direction>_<class>` columns of the CSV log.
AYE_WB_LINES = (
    CountingLine((0, 425), (708, 425), "down", name="line_1_down"),
    CountingLine((708, 425), (1100, 425), "down", name="line_2_down"),
    CountingLine((728, 138), (678, 178), "left", name="line_3_left"),
    CountingLine((678, 178), (665, 285), "left", name="line_4_left"),
    CountingLine((665, 285), (708, 425), "left", name="line_5_left"),
    CountingLine((728, 138), (678, 178), "right", name="line_6_right"),
    CountingLine((678, 178), (665, 285), "right", name="line_7_right"),
    CountingLine((665, 285), (708, 425), "right", name="line_8_right"),
)

AYE_WB_LINE_GROUPS = ((2, 5, 3, 6, 4, 7),)

# COCO class ids kept from the detector, and the tally column names.
VEHICLE_CLASS_IDS = (2, 3, 5, 7)
VEHICLE_CLASS_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
