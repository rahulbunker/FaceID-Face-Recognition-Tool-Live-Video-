"""
STEP 1: Dataset ke saare faces ko encode karta hai.

Folder structure aisa hona chahiye:
    dataset/
        Ramesh/
            1.jpg
            2.jpg
        Suresh/
            1.jpg
        Priya/
            1.jpg
            2.jpg

Har person ka apna folder hoga, folder ka naam = us person ka naam.
Ye script saare photos padh kar "encodings.pickle" file bana dega.
"""

import face_recognition
import os
import pickle
import cv2

DATASET_DIR = "dataset"          # jaha aapke logo ki photos hai
ENCODINGS_FILE = "encodings.pickle"

known_encodings = []
known_names = []

if not os.path.isdir(DATASET_DIR):
    raise SystemExit(f"[ERROR] '{DATASET_DIR}' folder nahi mila. Pehle dataset banao.")

for person_name in os.listdir(DATASET_DIR):
    person_dir = os.path.join(DATASET_DIR, person_name)
    if not os.path.isdir(person_dir):
        continue

    print(f"[INFO] Processing: {person_name}")

    for image_name in os.listdir(person_dir):
        image_path = os.path.join(person_dir, image_name)
        image = cv2.imread(image_path)
        if image is None:
            print(f"  [SKIP] padh nahi paya: {image_name}")
            continue

        # OpenCV BGR me padhta hai, face_recognition ko RGB chahiye
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Face ka location dhoondo
        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)

        for encoding in encodings:
            known_encodings.append(encoding)
            known_names.append(person_name)

        if len(encodings) == 0:
            print(f"  [WARN] is photo me face nahi mila: {image_name}")

# Sab kuch ek file me save kar do
data = {"encodings": known_encodings, "names": known_names}
with open(ENCODINGS_FILE, "wb") as f:
    pickle.dump(data, f)

print(f"\n[DONE] Total {len(known_encodings)} faces encode hue.")
print(f"[DONE] Saved -> {ENCODINGS_FILE}")
