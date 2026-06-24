# FaceID — Face Recognition Tool (Live + Video)

Ek face recognition project jo **live camera** aur **uploaded video** dono se chehra pehchaan kar uska **naam** bata deta hai. Iske do tarike se use kar sakte ho:

1. **Terminal scripts** — seedhe Python se (live camera / video file).
2. **Web app** — ek sundar browser interface (Flask + HTML/CSS/JS) jisme tab badal kar live ya video upload kar sakte ho.

---

## Kaam kaise karta hai

1. Aap har person ki kuch photos `dataset/` me rakhte ho (folder ka naam = us person ka naam).
2. `1_encode_faces.py` har chehre ka ek "encoding" (128 number ka fingerprint) banakar `encodings.pickle` me save kar deta hai.
3. Live camera ya video me jo chehra aata hai uska encoding banakar dataset se compare hota hai. Sabse milta-julta mil jaaye to uska naam dikhta hai, warna **Unknown**.

---

## Project structure

```
files/
    dataset/                 # known logo ki photos (har person ka folder)
        Rahul/
            1.jpg
            2.jpg
    1_encode_faces.py        # STEP 1: faces ko encode karta hai
    2_recognize_live.py      # terminal: live camera
    3_recognize_video.py     # terminal: video file
    app.py                   # web app ka backend (Flask)
    templates/
        index.html           # web app ka page
    static/
        style.css            # web app ki styling
        app.js               # web app ki logic
        outputs/             # (auto) analyze ki hui videos yaha save hoti hai
    uploads/                 # (auto) upload ki hui videos temporarily yaha
    encodings.pickle         # (auto) STEP 1 ke baad banti hai
    requirements.txt
    README.md
```

---

## Tech used

- **Python 3.10**
- **face_recognition** (dlib par based) — face detect + match
- **OpenCV** (opencv-python) — image/video padhna aur draw karna
- **NumPy (<2)** — arrays
- **Flask** — web app backend

---

## Setup (Windows)

### 1. Python aur virtual environment
Python 3.10 (64-bit) install hona chahiye. Project folder me terminal kholo aur venv banao:
```
python -m venv venv
venv\Scripts\activate
```
(Activate hone par prompt ke aage `(venv)` dikhega.)

### 2. dlib install karo (ZAROORI — pehle ye)
Windows par `dlib` seedhe `pip install` se aksar fail hota hai (C++ compiler chahiye). Isliye ek **ready-made wheel** install karte hai. Python 3.10 ke liye:
```
pip install https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.22.99-cp310-cp310-win_amd64.whl
```
> Doosre Python version ke liye sahi wheel yaha se lo: https://github.com/z-mahmud22/Dlib_Windows_Python3.x
> (file ka `cp310` / `cp311` part aapke Python version se match hona chahiye.)

### 3. Baaki libraries install karo
```
pip install -r requirements.txt
```

### 4. Verify
```
python -c "import face_recognition; print('OK')"
```
`OK` aaya to setup complete.

---

## Dataset banao

`dataset/` folder me har person ka alag folder banao, folder ka naam = uska naam:
```
dataset/
    Rahul/
        1.jpg
        2.jpg
    Priya/
        1.jpg
```
Har person ki **3-5 saaf photos** rakho (front face, achhi light, ek hi insaan). Jitni achhi photos, utni achhi accuracy.

---

## Use kaise kare

### STEP 1 — Faces encode karo (har baar jab naye log add karo)
```
python 1_encode_faces.py
```
`Total X faces encode hue` dikhe = `encodings.pickle` ban gayi.

### Option A — Terminal scripts

**Live camera:**
```
python 2_recognize_live.py
```
Window me face par box + naam aayega. Band karne ke liye **q** dabao.

**Video file:**
```
python 3_recognize_video.py test.mp4
```
Result save karna ho to:
```
python 3_recognize_video.py test.mp4 output.mp4
```

### Option B — Web app (recommended)

```
pip install flask        # ek baar
python app.py
```
Terminal me `Running on http://127.0.0.1:5000` dikhega. Ab **Chrome ya Edge** kholo (VS Code ke andar wale browser me NAHI — wo camera support nahi karta) aur jao:
```
http://127.0.0.1:5000
```
- **Live camera** tab → *Start camera* → browser ka permission popup *Allow* karo.
- **Upload video** tab → video select karo → *Analyze video* → result video + pehchaane gaye logo ki list aa jayegi.

Server band karne ke liye terminal me **Ctrl + C**.

---

## Settings / Tuning

| Setting | Kaha | Kya karta hai |
|---|---|---|
| `TOLERANCE` | scripts/app.py ke top par | Match kitna strict ho. Galat naam aaye → kam karo (0.45). "Unknown" hi aaye → badhao (0.55). |
| `PROCESS_EVERY_N` | `3_recognize_video.py` / `app.py` | Video me har kitne-vaa frame check ho. Video slow lage → badhao (10-15). |
| `CAMERA_INDEX` | `2_recognize_live.py` | Camera 0 na chale to 1 ya 2 try karo. |

---

## Troubleshooting (jo dikkatein aati hai)

**`Failed building wheel for dlib` / `You must use Visual Studio`**
dlib build ho nahi pa raha. Setup Step 2 wala prebuilt wheel install karo, phir baaki libraries. Apne Python version ke hisaab se sahi `cpXXX` wheel lena.

**`RuntimeError: Unsupported image type, must be 8bit gray or RGB image`**
NumPy 2.x aur purani dlib ka clash. Fix:
```
pip install "numpy<2"
```

**Web app me "Camera access nahi mila"**
Page VS Code ke andar wale browser me khula hai. Use band karke **Chrome/Edge** me `http://127.0.0.1:5000` kholo aur permission *Allow* karo. Agar pehle Block kar diya tha to address bar ke lock/camera icon se Allow karke page refresh karo.

**Video "processing" par bahut der atki rehti hai**
Slow hai, atki nahi. Har frame CPU par process hota hai. `PROCESS_EVERY_N` ko 15 kar do aur HD ki jagah chhoti video try karo. Terminal me error na ho to bas wait karo.

**Galat naam / sab "Unknown" aa raha hai**
`TOLERANCE` adjust karo, aur us person ki aur saaf photos `dataset/` me daal kar `python 1_encode_faces.py` dobara chalao.

**Camera open nahi ho raha (terminal script)**
`2_recognize_live.py` me `CAMERA_INDEX = 0` ko `1`/`2` karo. Camera kisi aur app (Zoom/Meet) me khuli ho to band karo.

---

## Privacy note

Kisi ka face data collect/store karne se pehle uski **permission** lena zaroori hai. Sirf un logo ki photos rakho jinhone consent diya hai, aur is tool ka istemal kisi ki marzi ke khilaf na karo.