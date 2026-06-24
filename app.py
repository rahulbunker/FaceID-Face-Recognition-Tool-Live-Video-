"""
Flask backend for the Face Recognition frontend.

Ye wahi 'encodings.pickle' use karta hai jo aapne 1_encode_faces.py se banaya.

Chalane ke liye:
    pip install flask
    python app.py
Phir browser me kholo:  http://127.0.0.1:5000
"""

import os
import time
import pickle
import base64

import cv2
import numpy as np
import face_recognition
from flask import Flask, request, jsonify, render_template

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ENCODINGS_FILE = os.path.join(BASE_DIR, "encodings.pickle")
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "outputs")

TOLERANCE = 0.5          # kam = zyada strict matching
PROCESS_EVERY_N = 5      # video me har 5th frame process karo (speed ke liye)

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = Flask(__name__)

# Known faces load karo (server start hote hi ek baar)
if not os.path.exists(ENCODINGS_FILE):
    raise SystemExit("[ERROR] encodings.pickle nahi mila. Pehle 1_encode_faces.py chalao.")

with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)
known_encodings = data["encodings"]
known_names = data["names"]
print(f"[INFO] {len(known_encodings)} known faces load hue.")


def recognize_in_rgb(rgb):
    """Ek RGB image me saare faces dhoondo aur naam match karo."""
    rgb = np.ascontiguousarray(rgb)
    boxes = face_recognition.face_locations(rgb, model="hog")
    encs = face_recognition.face_encodings(rgb, boxes)
    results = []
    for (top, right, bottom, left), enc in zip(boxes, encs):
        name = "Unknown"
        if len(known_encodings) > 0:
            distances = face_recognition.face_distance(known_encodings, enc)
            best = int(np.argmin(distances))
            if distances[best] <= TOLERANCE:
                name = known_names[best]
        results.append({
            "name": name,
            "top": int(top), "right": int(right),
            "bottom": int(bottom), "left": int(left),
        })
    return results


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/known")
def api_known():
    """Dataset me kitne aur kaun-kaun log hai."""
    names = sorted(set(known_names))
    return jsonify({"names": names, "count": len(known_encodings)})


@app.route("/api/recognize_frame", methods=["POST"])
def api_recognize_frame():
    """Live camera ka ek frame -> detected faces + naam."""
    payload = request.get_json(silent=True) or {}
    img_b64 = payload.get("image", "")
    if "," in img_b64:
        img_b64 = img_b64.split(",", 1)[1]
    try:
        img_bytes = base64.b64decode(img_b64)
        arr = np.frombuffer(img_bytes, np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception:
        bgr = None
    if bgr is None:
        return jsonify({"faces": [], "w": 0, "h": 0})
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    faces = recognize_in_rgb(rgb)
    return jsonify({"faces": faces, "w": bgr.shape[1], "h": bgr.shape[0]})


@app.route("/api/recognize_video", methods=["POST"])
def api_recognize_video():
    """Uploaded video -> annotated video + jin logo ko pehchaana unki list."""
    if "video" not in request.files or request.files["video"].filename == "":
        return jsonify({"error": "Koi video file nahi mili."}), 400

    file = request.files["video"]
    stamp = str(int(time.time()))
    in_path = os.path.join(UPLOAD_DIR, f"input_{stamp}_{file.filename}")
    file.save(in_path)

    cap = cv2.VideoCapture(in_path)
    if not cap.isOpened():
        return jsonify({"error": "Video open nahi ho payi."}), 400

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25

    out_name = f"result_{stamp}.mp4"
    out_path = os.path.join(OUTPUT_DIR, out_name)

    # Browser me chalne ke liye pehle H.264 (avc1) try karo, na ho to mp4v
    writer = None
    for codec in ("avc1", "mp4v"):
        writer = cv2.VideoWriter(out_path, cv2.VideoWriter_fourcc(*codec), fps, (w, h))
        if writer.isOpened():
            break

    frame_no = 0
    last = []
    found = {}      # naam -> pehli baar kis second par dikha

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame_no += 1

        if frame_no % PROCESS_EVERY_N == 0:
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)
            res = recognize_in_rgb(rgb)
            last = []
            for r in res:
                last.append((r["top"] * 4, r["right"] * 4, r["bottom"] * 4, r["left"] * 4, r["name"]))
                if r["name"] != "Unknown" and r["name"] not in found:
                    found[r["name"]] = round(frame_no / fps, 1)

        for (top, right, bottom, left, name) in last:
            color = (0, 200, 0) if name != "Unknown" else (60, 70, 240)
            cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
            cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
            cv2.putText(frame, name, (left + 6, bottom - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        writer.write(frame)

    cap.release()
    writer.release()

    people = [{"name": n, "first_seen": found[n]} for n in sorted(found, key=found.get)]
    return jsonify({"video_url": f"/static/outputs/{out_name}", "people": people})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
