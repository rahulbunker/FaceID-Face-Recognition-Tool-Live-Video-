// ---------- Tabs ----------
const tabs = document.querySelectorAll(".tab");
const panels = {
  live: document.getElementById("panel-live"),
  upload: document.getElementById("panel-upload"),
};
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((t) => t.classList.remove("is-active"));
    tab.classList.add("is-active");
    Object.values(panels).forEach((p) => p.classList.remove("is-active"));
    panels[tab.dataset.tab].classList.add("is-active");
    if (tab.dataset.tab !== "live") stopCamera();
  });
});

// ---------- Dataset status ----------
fetch("/api/known")
  .then((r) => r.json())
  .then((d) => {
    document.getElementById("datasetText").textContent =
      `${d.count} known face${d.count === 1 ? "" : "s"} loaded`;
    const chips = document.getElementById("knownChips");
    if (d.names.length) {
      chips.innerHTML = d.names.map((n) => `<span class="chip">${escapeHtml(n)}</span>`).join("");
    }
  })
  .catch(() => {
    document.getElementById("datasetText").textContent = "dataset load nahi hua";
  });

// ---------- Detected list (shared) ----------
const detectList = document.getElementById("detectList");
function renderDetections(faces) {
  if (!faces.length) {
    detectList.innerHTML = `<li class="detect-empty">Abhi koi face nahi</li>`;
    return;
  }
  detectList.innerHTML = faces
    .map((f) => {
      const known = f.name !== "Unknown";
      return `<li class="detect-item ${known ? "known" : "unknown"}">
        <span>${escapeHtml(f.name)}</span>
        <span class="tag">${known ? "match" : "unknown"}</span>
      </li>`;
    })
    .join("");
}

// ---------- LIVE CAMERA ----------
const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const octx = overlay.getContext("2d");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const liveStatus = document.getElementById("liveStatus");
const liveHint = document.getElementById("liveHint");
const viewport = document.querySelector("#panel-live .viewport");

let stream = null;
let running = false;
let busy = false;

const CAPTURE_W = 480; // server ko itni width par bhejo (speed ke liye)
const capCanvas = document.createElement("canvas");
const capCtx = capCanvas.getContext("2d");

startBtn.addEventListener("click", startCamera);
stopBtn.addEventListener("click", stopCamera);

async function startCamera() {
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 } });
    video.srcObject = stream;
    await video.play();
    running = true;
    liveHint.hidden = true;
    liveStatus.hidden = false;
    viewport.classList.add("is-live");
    startBtn.disabled = true;
    stopBtn.disabled = false;
    syncOverlaySize();
    loop();
  } catch (e) {
    liveHint.hidden = false;
    liveHint.textContent = "Camera access nahi mila — browser permission allow karo";
  }
}

function stopCamera() {
  running = false;
  if (stream) stream.getTracks().forEach((t) => t.stop());
  stream = null;
  viewport.classList.remove("is-live");
  liveStatus.hidden = true;
  liveHint.hidden = false;
  liveHint.textContent = "Camera band hai — Start dabao";
  startBtn.disabled = false;
  stopBtn.disabled = true;
  octx.clearRect(0, 0, overlay.width, overlay.height);
  renderDetections([]);
}

function syncOverlaySize() {
  overlay.width = video.clientWidth;
  overlay.height = video.clientHeight;
}
window.addEventListener("resize", () => { if (running) syncOverlaySize(); });

async function loop() {
  if (!running) return;
  if (!busy && video.videoWidth) {
    busy = true;
    const scale = CAPTURE_W / video.videoWidth;
    capCanvas.width = CAPTURE_W;
    capCanvas.height = Math.round(video.videoHeight * scale);
    capCtx.drawImage(video, 0, 0, capCanvas.width, capCanvas.height);
    const dataUrl = capCanvas.toDataURL("image/jpeg", 0.7);
    try {
      const res = await fetch("/api/recognize_frame", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image: dataUrl }),
      });
      const out = await res.json();
      drawFaces(out.faces, out.w, out.h);
      renderDetections(out.faces);
    } catch (e) {
      /* ek frame fail hua to ignore, agla try karenge */
    }
    busy = false;
  }
  setTimeout(loop, 250); // har ~0.25s par ek frame
}

function drawFaces(faces, srcW, srcH) {
  syncOverlaySize();
  octx.clearRect(0, 0, overlay.width, overlay.height);
  if (!srcW || !srcH) return;
  const sx = overlay.width / srcW;
  const sy = overlay.height / srcH;
  octx.lineWidth = 2;
  octx.font = "600 14px Inter, sans-serif";
  faces.forEach((f) => {
    const known = f.name !== "Unknown";
    const color = known ? "#15b26b" : "#f0436a";
    const x = f.left * sx, y = f.top * sy;
    const w = (f.right - f.left) * sx, h = (f.bottom - f.top) * sy;
    octx.strokeStyle = color;
    octx.strokeRect(x, y, w, h);
    const label = f.name;
    const tw = octx.measureText(label).width + 14;
    octx.fillStyle = color;
    octx.fillRect(x, y + h, tw, 22);
    octx.fillStyle = "#fff";
    octx.fillText(label, x + 7, y + h + 15);
  });
}

// ---------- VIDEO UPLOAD ----------
const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const analyzeBtn = document.getElementById("analyzeBtn");
const uploadStatus = document.getElementById("uploadStatus");
const result = document.getElementById("result");
const resultVideo = document.getElementById("resultVideo");
const resultFallback = document.getElementById("resultFallback");
const downloadLink = document.getElementById("downloadLink");

let chosenFile = null;

fileInput.addEventListener("change", () => setFile(fileInput.files[0]));
["dragover", "dragenter"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.add("is-drag"); })
);
["dragleave", "drop"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => { e.preventDefault(); dropzone.classList.remove("is-drag"); })
);
dropzone.addEventListener("drop", (e) => {
  if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
});

function setFile(file) {
  if (!file) return;
  chosenFile = file;
  fileName.textContent = file.name;
  analyzeBtn.disabled = false;
  result.hidden = true;
}

analyzeBtn.addEventListener("click", async () => {
  if (!chosenFile) return;
  analyzeBtn.disabled = true;
  uploadStatus.hidden = false;
  result.hidden = true;
  detectList.innerHTML = `<li class="detect-empty">Video process ho rahi hai…</li>`;

  const form = new FormData();
  form.append("video", chosenFile);
  try {
    const res = await fetch("/api/recognize_video", { method: "POST", body: form });
    const out = await res.json();
    if (out.error) throw new Error(out.error);

    resultVideo.src = out.video_url;
    downloadLink.href = out.video_url;
    result.hidden = false;
    resultFallback.hidden = false;

    if (out.people.length) {
      detectList.innerHTML = out.people
        .map(
          (p) => `<li class="detect-item known">
            <span>${escapeHtml(p.name)}</span>
            <span class="tag">${p.first_seen}s</span>
          </li>`
        )
        .join("");
    } else {
      detectList.innerHTML = `<li class="detect-empty">Koi known face nahi mila</li>`;
    }
  } catch (e) {
    detectList.innerHTML = `<li class="detect-empty">Error: ${escapeHtml(e.message || "process fail")}</li>`;
  } finally {
    uploadStatus.hidden = true;
    analyzeBtn.disabled = false;
  }
});

// ---------- util ----------
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])
  );
}
