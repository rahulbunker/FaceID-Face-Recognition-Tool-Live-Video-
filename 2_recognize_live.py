"""
STEP 2 (LIVE): Webcam se live face identify karta hai.

Chalane se pehle '1_encode_faces.py' run kar lena (taaki encodings.pickle ban jaaye).
Band karne ke liye 'q' button dabao.
"""

import face_recognition
import cv2
import pickle
import numpy as np

ENCODINGS_FILE = "encodings.pickle"
TOLERANCE = 0.5      # kam value = zyada strict matching (0.4-0.6 try karo)
CAMERA_INDEX = 0     # agar external camera hai to 1 ya 2 try karo

# Encodings load karo
with open(ENCODINGS_FILE, "rb") as f:
    data = pickle.load(f)
print(f"[INFO] {len(data['encodings'])} known faces load hue.")

video = cv2.VideoCapture(CAMERA_INDEX)
if not video.isOpened():
    raise SystemExit("[ERROR] Camera open nahi hua. CAMERA_INDEX badal kar dekho.")

print("[INFO] Live recognition shuru... band karne ke liye 'q' dabao.")

while True:
    ret, frame = video.read()
    if not ret:
        break

    # Speed ke liye frame chhota kar lo (1/4)
    small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

    boxes = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, boxes)

    names = []
    for encoding in encodings:
        name = "Unknown"
        distances = face_recognition.face_distance(data["encodings"], encoding)
        if len(distances) > 0:
            best = np.argmin(distances)
            if distances[best] <= TOLERANCE:
                name = data["names"][best]
        names.append(name)

    # Box aur naam draw karo (coordinates ko wapas *4 karna hai)
    for (top, right, bottom, left), name in zip(boxes, names):
        top *= 4; right *= 4; bottom *= 4; left *= 4
        color = (0, 200, 0) if name != "Unknown" else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, name, (left + 6, bottom - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow("Live Face Recognition (press q to quit)", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

video.release()
cv2.destroyAllWindows()
