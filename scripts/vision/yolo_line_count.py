import cv2
import numpy as np
from ultralytics import YOLO
import time
import csv
import os
from datetime import datetime
import os

VIDEO_PATH = "202603291735.mp4"
#VIDEO_PATH = "202603211716.mp4"
MODEL_PATH = "yolo11s_openvino_model/"
VEHICLE_CLASSES = [2, 3, 5, 7]
CLASS_NAMES = {2: "car", 3: "motorcycle", 5: "bus", 7: "truck"}
CONF_THRESHOLD = 0.1
TRACKER_CONFIG = "bytetrack.yaml"

LINES = [
    {"p1": (0, 425), "p2": (708, 425), "direction": "down"},
    {"p1": (708, 425), "p2": (1100, 425), "direction": "down"},
    {"p1": (728, 138), "p2": (678, 178), "direction": "left"},
    {"p1": (678, 178), "p2": (665, 285), "direction": "left"},
    {"p1": (665, 285), "p2": (708, 425), "direction": "left"},
    {"p1": (728, 138), "p2": (678, 178), "direction": "right"},
    {"p1": (678, 178), "p2": (665, 285), "direction": "right"},
    {"p1": (665, 285), "p2": (708, 425), "direction": "right"},
]

LINE_GROUPS = [(2, 5, 3, 6, 4, 7)]

DISPLAY_WIDTH = 1280

model = YOLO(MODEL_PATH)
cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print("Cannot open video file")
    exit()

fps = cap.get(cv2.CAP_PROP_FPS)
if fps <= 0:
    fps = 30   
total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
total_duration = total_frames / fps if fps > 0 else 0
print(f" {fps:.2f} fps, total frames: {total_frames}, total time: {total_duration:.2f}s")

orig_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
orig_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
display_height = int(DISPLAY_WIDTH * orig_height / orig_width)
display_size = (DISPLAY_WIDTH, display_height)

prev_positions = {}
line_counts = []
for _ in LINES:
    line_counts.append({name: 0 for name in CLASS_NAMES.values()})

line_counted_ids = [set() for _ in LINES]

line_to_groups = [[] for _ in range(len(LINES))]
for g_idx, group in enumerate(LINE_GROUPS):
    for line_idx in group:
        line_to_groups[line_idx].append(g_idx)

group_counted_ids = [set() for _ in LINE_GROUPS]


frame_count = 0
start_time = time.time()
last_csv_video_time = 0.0          
last_1p_frame = 0
progress_interval = max(1, total_frames // 100)  


last_print_200_time = start_time   


csv_filename = "traffic_counts_log.csv"

csv_header = ["timestamp", "video_time_sec"]

for i in range(len(LINES)):
    csv_header.append(f"line_{i+1}_{LINES[i]['direction']}_car")
    csv_header.append(f"line_{i+1}_{LINES[i]['direction']}_motorcycle")
    csv_header.append(f"line_{i+1}_{LINES[i]['direction']}_bus")
    csv_header.append(f"line_{i+1}_{LINES[i]['direction']}_truck")

def write_csv(data_dict):
    
    file_exists = os.path.isfile(csv_filename)
    with open(csv_filename, mode='a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=csv_header)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data_dict)

def get_current_counts_dict(video_time):
    
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "video_time_sec": round(video_time, 2)
    }
    for i, counts in enumerate(line_counts):
        for name in ["car", "motorcycle", "bus", "truck"]:
            key = f"line_{i+1}_{LINES[i]['direction']}_{name}"
            data[key] = counts.get(name, 0)
    return data

last_progress_time = start_time
last_progress_frame = 0

os.makedirs("screenshots", exist_ok=True)
last_screenshot_video_time = 0.0

show_window = True
print("Press 'd' to show/hide video, press 'q' to quit")


def ccw(A, B, C):
    return (C[1] - A[1]) * (B[0] - A[0]) > (B[1] - A[1]) * (C[0] - A[0])

def segments_intersect(A, B, C, D):
    return (ccw(A, C, D) != ccw(B, C, D)) and (ccw(A, B, C) != ccw(A, B, D))

def point_on_segment(P, A, B):
    if min(A[0], B[0]) <= P[0] <= max(A[0], B[0]) and min(A[1], B[1]) <= P[1] <= max(A[1], B[1]):
        return ccw(A, B, P) == 0
    return False

def direction_matches(prev, curr, direction):
    dx = curr[0] - prev[0]
    dy = curr[1] - prev[1]
    if direction == "right":
        return dx > 0
    elif direction == "left":
        return dx < 0
    elif direction == "down":
        return dy > 0
    elif direction == "up":
        return dy < 0
    return False

while True:
    ret, frame = cap.read()
    if not ret:
        break
    frame_count += 1
    video_time = frame_count / fps

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break
    elif key == ord('d'):
        show_window = not show_window
        print(f"Video is {'shown' if show_window else 'hidden'}")

    results = model.track(
        frame,
        device="intel:gpu",
        persist=True,
        tracker=TRACKER_CONFIG,
        classes=VEHICLE_CLASSES,
        conf=CONF_THRESHOLD,
        verbose=False
    )

    if results[0].boxes is not None and results[0].boxes.id is not None:
        boxes = results[0].boxes.xyxy.cpu().numpy().astype(int)
        track_ids = results[0].boxes.id.cpu().numpy().astype(int)
        cls_ids = results[0].boxes.cls.cpu().numpy().astype(int)

        for box, track_id, cls_id in zip(boxes, track_ids, cls_ids):
            x1, y1, x2, y2 = box
            cx = (x1 + x2) // 2
            cy = y2

            if track_id in prev_positions:
                prev_cx, prev_cy = prev_positions[track_id]

                for idx, line in enumerate(LINES):
                    p1, p2 = line["p1"], line["p2"]
                    is_crossing = segments_intersect((prev_cx, prev_cy), (cx, cy), p1, p2)
                    if not is_crossing:
                        if point_on_segment((prev_cx, prev_cy), p1, p2) or point_on_segment((cx, cy), p1, p2):
                            is_crossing = True

                    if is_crossing and direction_matches((prev_cx, prev_cy), (cx, cy), line["direction"]):
                        if track_id in line_counted_ids[idx]:
                            continue

                        skip = False
                        for g_idx in line_to_groups[idx]:
                            if track_id in group_counted_ids[g_idx]:
                                skip = True
                                break
                        if skip:
                            continue

                        line_counted_ids[idx].add(track_id)
                        for g_idx in line_to_groups[idx]:
                            group_counted_ids[g_idx].add(track_id)
                        class_name = CLASS_NAMES.get(cls_id, "unknown")
                        if class_name in line_counts[idx]:
                            line_counts[idx][class_name] += 1

            prev_positions[track_id] = (cx, cy)

            cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)

    for idx, line in enumerate(LINES):
        p1, p2 = line["p1"], line["p2"]
        cv2.line(frame, p1, p2, (0, 255, 255), 2)
        mid_x, mid_y = (p1[0] + p2[0]) // 2, (p1[1] + p2[1]) // 2
        counts = line_counts[idx]
        counts_text = f"{line['direction']}: " + " ".join([f"{k[:1]}:{v}" for k, v in counts.items()])
        cv2.putText(frame, counts_text, (mid_x + 10, mid_y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 1)

    elapsed_real = time.time() - start_time

    if frame_count % 200 == 0:
        if frame_count > 0:
            inst_fps = 200 / (time.time() - last_print_200_time)
            print(f"[Instantaneous FPS] Frame {frame_count}: {inst_fps:.2f} FPS")
            last_print_200_time = time.time()

    if frame_count >= last_1p_frame + progress_interval:
        now = time.time()
        delta_frames = frame_count - last_progress_frame
        delta_time = now - last_progress_time
        inst_progress_fps = delta_frames / delta_time if delta_time > 0 else 0
        percent = (frame_count / total_frames) * 100
        print(f"[Progress] {percent:.1f}% ({frame_count}/{total_frames}) | Instantaneous FPS: {inst_progress_fps:.2f}")
        last_1p_frame = frame_count
        last_progress_time = now
        last_progress_frame = frame_count


    if video_time - last_csv_video_time >= 60:
        data = get_current_counts_dict(video_time)
        write_csv(data)
        print(f"[CSV] Video time {video_time:.1f}s saved")
        last_csv_video_time = video_time
        screenshot_filename = f"screenshots/screenshot_{video_time:.1f}s.jpg"
        cv2.imwrite(screenshot_filename, frame)
        print(f"[Screenshot] Saved {screenshot_filename} (video time {video_time:.1f} s)")
        last_screenshot_video_time = video_time

    if show_window:
        display_frame = cv2.resize(frame, display_size)
        cv2.imshow("Traffic Counting", display_frame)
    else:
        pass
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

final_data = get_current_counts_dict(video_time)
write_csv(final_data)
print(f"[CSV] Final result saved in {csv_filename}")

print("\n===== Final statistics =====")
for idx, counts in enumerate(line_counts):
    print(f"line {idx+1} ({LINES[idx]['p1']}-{LINES[idx]['p2']}, direction:{LINES[idx]['direction']}):")
    for name, cnt in counts.items():
        print(f"  {name}: {cnt}")
    total = sum(counts.values())
    print(f"  total: {total} veh")

total_time = time.time() - start_time
print(f"\nFinished! Total time spent: {total_time:.2f}s, average FPS: {frame_count/total_time:.2f}")
