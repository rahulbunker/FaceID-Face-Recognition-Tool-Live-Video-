"""
STEP 3 (VIDEO): Uploaded video file se face identify karta hai.

Use:
    python 3_recognize_video.py input.mp4
    python 3_recognize_video.py input.mp4 output.mp4   (result video save karne ke liye)

Band karne ke liye 'q' dabao.
"""

import face_recognition
import cv2
import pickle
import numpy as np
import sys

ENCODINGS_FILE = "encodings.pickle"
TOLERANCE = 0.5
PROCESS_EVERY_N = 2   # speed ke liye har 2nd frame process karo (1 = har frame)

if len(sys.argv) < 2:
    raise SystemExit("Use: python 3_recognize_video.py input.mp4 [output.mp4]")

input_path = sys.argv[1]
output_path = sys.argv[2] if len(sys.argv) > 2 else None

with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)
print(f"[INFO] {len(data['encodings'])} known faces load hue.")

video = cv2.VideoCapture(input_path)
if not video.isOpened():
    raise SystemExit(f"[ERROR] Video open nahi hui: {input_path}")

writer = None
if output_path:
    w = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = video.get(cv2.CAP_PROP_FPS) or 25
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

frame_no = 0
last_results = []   # detected faces ko frames ke beech reuse karne ke liye

while True:
    ret, frame = video.read()
    if not ret:
        break
    frame_no += 1

    if frame_no % PROCESS_EVERY_N == 0:
        small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
        rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)

        last_results = []
        for (top, right, bottom, left), encoding in zip(boxes, encodings):
            name = "Unknown"
            distances = face_recognition.face_distance(data["encodings"], encoding)
            if len(distances) > 0:
                best = np.argmin(distances)
                if distances[best] <= TOLERANCE:
                    name = data["names"][best]
            last_results.append((top * 4, right * 4, bottom * 4, left * 4, name))

    for (top, right, bottom, left, name) in last_results:
        color = (0, 200, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    if writer:
        writer.write(frame)

    cv2.imshow("Video Face Recognition (press q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video.release()
if writer:
    writer.release()
    print(f"[DONE] Output saved -> {output_path}")
cv2.destroyAllWindows()
