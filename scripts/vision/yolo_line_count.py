#!/usr/bin/env python3
"""Multi-line vehicle counting over a traffic video (YOLO detection + tracking).

The counting decision itself -- segment intersection, direction, per-line and
per-group de-duplication -- lives in `line_counting.py`, which has no
third-party dependencies and is covered by `tests/test_line_counting.py`.
This file is the I/O shell around it: decode frames, run the detector/tracker,
feed centroids to the counter, log tallies.

Example:

    python scripts/vision/yolo_line_count.py
        --video peak_1735.mp4 --model yolo11s_openvino_model/
        --device cpu --csv peak_counts.csv

`--device` is passed straight to Ultralytics: `cpu`, `cuda:0`, `0`, or
`intel:gpu` for an OpenVINO export on an Intel GPU. It defaults to `cpu` so
the script starts on any machine. `--show` opens a preview window and is off
by default, so the script also runs on a headless box.

Neither the field videos nor the model weights are in this repository; point
`--video` and `--model` at your own files.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from line_counting import (  # noqa: E402
    AYE_WB_LINES,
    AYE_WB_LINE_GROUPS,
    LineCounter,
    VEHICLE_CLASS_IDS,
    VEHICLE_CLASS_NAMES,
)

CLASS_ORDER = ("car", "motorcycle", "bus", "truck")


def build_arg_parser():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--video", required=True, type=Path,
                        help="input video file")
    parser.add_argument("--model", required=True,
                        help="YOLO weights (.pt) or an exported model directory")
    parser.add_argument("--device", default="cpu",
                        help="Ultralytics device string, e.g. cpu, cuda:0, intel:gpu "
                             "(default: cpu)")
    parser.add_argument("--tracker", default="bytetrack.yaml",
                        help="Ultralytics tracker config (default: bytetrack.yaml)")
    parser.add_argument("--conf", type=float, default=0.1,
                        help="detection confidence threshold (default: 0.1)")
    parser.add_argument("--csv", type=Path, default=Path("traffic_counts_log.csv"),
                        help="tally log to append to (default: traffic_counts_log.csv)")
    parser.add_argument("--csv-interval", type=float, default=60.0,
                        help="video seconds between log rows (default: 60)")
    parser.add_argument("--screenshot-dir", type=Path, default=None,
                        help="if set, save one annotated frame per log row here")
    parser.add_argument("--max-frames", type=int, default=0,
                        help="stop after this many frames (0 = whole video)")
    parser.add_argument("--show", action="store_true",
                        help="open a preview window (off by default; needs a display)")
    parser.add_argument("--display-width", type=int, default=1280,
                        help="preview window width in pixels (default: 1280)")
    return parser


def csv_header(lines):
    header = ["timestamp", "video_time_sec"]
    for index, line in enumerate(lines):
        for name in CLASS_ORDER:
            header.append(f"line_{index + 1}_{line.direction}_{name}")
    return header


def counts_row(counter, video_time):
    row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "video_time_sec": round(video_time, 2),
    }
    for index, line in enumerate(counter.lines):
        for name in CLASS_ORDER:
            row[f"line_{index + 1}_{line.direction}_{name}"] = counter.counts[index].get(name, 0)
    return row


def append_row(path, header, row):
    exists = path.is_file()
    if str(path.parent) and not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=header)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def annotate(cv2, frame, counter):
    for index, line in enumerate(counter.lines):
        cv2.line(frame, line.p1, line.p2, (0, 255, 255), 2)
        mid = ((line.p1[0] + line.p2[0]) // 2, (line.p1[1] + line.p2[1]) // 2)
        text = f"{line.direction}: " + " ".join(
            f"{name[:1]}:{value}" for name, value in counter.counts[index].items())
        cv2.putText(frame, text, (mid[0] + 10, mid[1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)


def run(args):
    import cv2  # imported here so `import yolo_line_count` needs no OpenCV
    from ultralytics import YOLO

    if not args.video.is_file():
        raise SystemExit(f"Video not found: {args.video}")
    if not os.path.exists(args.model):
        raise SystemExit(f"Model not found: {args.model}")

    counter = LineCounter(list(AYE_WB_LINES), groups=AYE_WB_LINE_GROUPS,
                          classes=CLASS_ORDER)
    header = csv_header(counter.lines)

    model = YOLO(args.model)
    capture = cv2.VideoCapture(str(args.video))
    if not capture.isOpened():
        raise SystemExit(f"Cannot open video file: {args.video}")

    fps = capture.get(cv2.CAP_PROP_FPS) or 0
    if fps <= 0:
        fps = 30.0
        print("Frame rate unavailable from the container; assuming 30 fps")
    total_frames = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"{fps:.2f} fps, {total_frames} frames, {total_frames / fps:.2f} s of video")

    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)) or args.display_width
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)) or args.display_width
    display_size = (args.display_width, int(args.display_width * height / width))

    if args.screenshot_dir is not None:
        args.screenshot_dir.mkdir(parents=True, exist_ok=True)
    if args.show:
        print("Preview window open: press 'q' to stop")

    frame_count = 0
    last_logged = 0.0
    started = time.time()
    video_time = 0.0
    progress_step = max(1, total_frames // 100) if total_frames > 0 else 500
    next_progress = progress_step

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                break
            frame_count += 1
            video_time = frame_count / fps

            results = model.track(
                frame,
                device=args.device,
                persist=True,
                tracker=args.tracker,
                classes=list(VEHICLE_CLASS_IDS),
                conf=args.conf,
                verbose=False,
            )

            boxes = results[0].boxes
            if boxes is not None and boxes.id is not None:
                xyxy = boxes.xyxy.cpu().numpy().astype(int)
                track_ids = boxes.id.cpu().numpy().astype(int)
                class_ids = boxes.cls.cpu().numpy().astype(int)
                for box, track_id, class_id in zip(xyxy, track_ids, class_ids):
                    x1, y1, x2, y2 = box
                    centroid = ((int(x1) + int(x2)) // 2, int(y2))
                    counter.update(int(track_id),
                                   VEHICLE_CLASS_NAMES.get(int(class_id), "unknown"),
                                   centroid)
                    cv2.circle(frame, centroid, 4, (0, 0, 255), -1)

            annotate(cv2, frame, counter)

            if total_frames > 0 and frame_count >= next_progress:
                elapsed = time.time() - started
                print(f"[Progress] {frame_count / total_frames * 100:.1f}% "
                      f"({frame_count}/{total_frames}) | "
                      f"{frame_count / max(elapsed, 1e-9):.2f} fps")
                next_progress += progress_step

            if video_time - last_logged >= args.csv_interval:
                append_row(args.csv, header, counts_row(counter, video_time))
                print(f"[CSV] video time {video_time:.1f}s written to {args.csv}")
                last_logged = video_time
                if args.screenshot_dir is not None:
                    shot = args.screenshot_dir / f"screenshot_{video_time:.1f}s.jpg"
                    cv2.imwrite(str(shot), frame)
                    print(f"[Screenshot] {shot}")

            if args.show:
                cv2.imshow("Traffic Counting", cv2.resize(frame, display_size))
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if args.max_frames and frame_count >= args.max_frames:
                break
    finally:
        capture.release()
        if args.show:
            cv2.destroyAllWindows()

    append_row(args.csv, header, counts_row(counter, video_time))
    print(f"[CSV] final tallies written to {args.csv}")

    print("\n===== Final statistics =====")
    for index, line in enumerate(counter.lines):
        print(f"line {index + 1} ({line.p1}-{line.p2}, direction: {line.direction}):")
        for name in CLASS_ORDER:
            print(f"  {name}: {counter.counts[index].get(name, 0)}")
        print(f"  total: {counter.line_total(index)} veh")

    elapsed = time.time() - started
    print(f"\nFinished: {frame_count} frames in {elapsed:.2f}s "
          f"({frame_count / max(elapsed, 1e-9):.2f} fps average)")
    return 0


def main(argv=None):
    return run(build_arg_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
