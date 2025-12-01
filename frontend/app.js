// Simple state management
const state = {
  file: null,
  fileUrl: null,
  isPlaying: false,
  isProcessing: false,
  showOverlay: true,
  stats: { cars: 0, trucks: 0, buses: 0, bikes: 0 },
  fps: 0,
  logs: [],
  confidenceThreshold: 0.5,
  iouThreshold: 0.45,
  lastTime: performance.now(),
  frameCount: 0,
  lastFpsTime: performance.now(),
  rafId: null,
  analytics: { total: 0, passedUp: 0, passedDown: 0 },
  linePos: 0.5,
};

const WS_URL = 'ws://localhost:8000/ws/detect';
let ws = null;
let wsConnected = false;
let wsBusy = false;
let currentDetections = [];
let lastRequestTime = 0;
const FRAME_INTERVAL_MS = 200;

const captureCanvas = document.createElement('canvas');
const captureCtx = captureCanvas.getContext('2d');

// Elements
const videoEl = document.getElementById('video');
const canvasEl = document.getElementById('canvas');
const emptyStateEl = document.getElementById('empty-state');
const fileInputEl = document.getElementById('file-input');
const playBtn = document.getElementById('play-btn');
const playIcon = document.getElementById('play-icon');
const pauseIcon = document.getElementById('pause-icon');
const fileNameEl = document.getElementById('file-name');
const overlayToggle = document.getElementById('overlay-toggle');
const eyeOn = document.getElementById('eye-on');
const eyeOff = document.getElementById('eye-off');
const clearBtn = document.getElementById('clear-btn');
const confSlider = document.getElementById('conf-slider');
const confLabel = document.getElementById('conf-label');
const iouSlider = document.getElementById('iou-slider');
const iouLabel = document.getElementById('iou-label');
const processingDot = document.getElementById('processing-dot');
const processingText = document.getElementById('processing-text');
const statCars = document.getElementById('stat-cars');
const statTrucks = document.getElementById('stat-trucks');
const statBikes = document.getElementById('stat-bikes');
const statBuses = document.getElementById('stat-buses');
const logList = document.getElementById('log-list');
const eventsCount = document.getElementById('events-count');
const inferenceTimeEl = document.getElementById('inference-time');
const exportBtn = document.getElementById('export-btn');
const gpuUsageText = document.getElementById('gpu-usage-text');
const gpuUsageBar = document.getElementById('gpu-usage-bar');
const navLive = document.getElementById('nav-live');
const navAnalytics = document.getElementById('nav-analytics');
const navSettings = document.getElementById('nav-settings');
const sectionLive = document.getElementById('section-live');
const sectionAnalytics = document.getElementById('section-analytics');
const sectionSettings = document.getElementById('section-settings');
const analyticsTotal = document.getElementById('analytics-total');
const analyticsUp = document.getElementById('analytics-up');
const analyticsDown = document.getElementById('analytics-down');
const analyticsFps = document.getElementById('analytics-fps');
const settingOverlay = document.getElementById('setting-overlay');
const linePosSlider = document.getElementById('line-pos-slider');
const linePosLabel = document.getElementById('line-pos-label');
const settingsConfSlider = document.getElementById('settings-conf-slider');
const settingsIouSlider = document.getElementById('settings-iou-slider');
const settingsConfLabel = document.getElementById('settings-conf-label');
const settingsIouLabel = document.getElementById('settings-iou-label');

function setProcessing(isProcessing) {
  state.isProcessing = isProcessing;
  processingDot.className = `w-2 h-2 rounded-full ${
    isProcessing ? "bg-emerald-500 animate-pulse" : "bg-amber-500"
  }`;
  processingText.textContent = isProcessing ? `PROCESSING ${state.fps} FPS` : "IDLE";
}

function updateStatsDisplay() {
  statCars.textContent = state.stats.cars;
  statTrucks.textContent = state.stats.trucks;
  statBikes.textContent = state.stats.bikes;
  statBuses.textContent = state.stats.buses;
}

function addLogItem({ type, time, confidence }) {
  const container = document.createElement("div");
  container.className =
    "flex items-center justify-between p-3 border-b border-slate-800 hover:bg-slate-800/50 transition-colors text-sm";
  container.dataset.type = type;
  container.dataset.time = time;
  container.dataset.confidence = (confidence * 100).toFixed(0);

  const left = document.createElement("div");
  left.className = "flex items-center gap-3";

  const iconWrap = document.createElement("span");
  iconWrap.className = "p-1.5 rounded-md bg-slate-800";
  const color =
    type === "truck"
      ? "text-orange-400"
      : type === "motorbike"
      ? "text-purple-400"
      : "text-blue-400";

  iconWrap.classList.add(color);
  iconWrap.innerHTML =
    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>';

  const textWrap = document.createElement("div");
  const title = document.createElement("p");
  title.className = "font-medium text-slate-200 capitalize";
  title.textContent = type;

  const sub = document.createElement("p");
  sub.className = "text-xs text-slate-500";
  sub.textContent = time;

  textWrap.appendChild(title);
  textWrap.appendChild(sub);

  left.appendChild(iconWrap);
  left.appendChild(textWrap);

  const right = document.createElement("div");
  right.className = "flex items-center gap-2";

  const bar = document.createElement("div");
  bar.className = "h-1.5 w-16 bg-slate-800 rounded-full overflow-hidden";

  const fill = document.createElement("div");
  fill.className = "h-full bg-emerald-500 rounded-full";
  fill.style.width = `${confidence * 100}%`;

  bar.appendChild(fill);

  const pct = document.createElement("span");
  pct.className = "text-xs font-mono text-slate-400";
  pct.textContent = `${(confidence * 100).toFixed(0)}%`;

  right.appendChild(bar);
  right.appendChild(pct);

  container.appendChild(left);
  container.appendChild(right);

  logList.prepend(container);
  while (logList.children.length > 50) logList.removeChild(logList.lastChild);

  eventsCount.textContent = `${logList.children.length} Events`;
}

// Simple tracking for counting line crossings
const tracks = [];
function updateTracks(scaledDetections) {
  const maxDist = 50;
  const lineY = canvasEl.height * state.linePos;
  scaledDetections.forEach((d) => {
    const cx = d.x + d.w / 2;
    const cy = d.y + d.h / 2;
    let bestIdx = -1;
    let bestDist = Infinity;
    for (let i = 0; i < tracks.length; i++) {
      const t = tracks[i];
      if (t.class !== d.class) continue;
      const dist = Math.hypot(t.cx - cx, t.cy - cy);
      if (dist < maxDist && dist < bestDist) { bestDist = dist; bestIdx = i; }
    }
    if (bestIdx >= 0) {
      const t = tracks[bestIdx];
      const prevCy = t.cy;
      t.cx = cx; t.cy = cy; t.lastSeen = performance.now();
      if (prevCy < lineY && cy >= lineY && !t.markedDown) { state.analytics.passedDown++; t.markedDown = true; t.markedUp = false; }
      if (prevCy > lineY && cy <= lineY && !t.markedUp) { state.analytics.passedUp++; t.markedUp = true; t.markedDown = false; }
    } else {
      tracks.push({ class: d.class, cx, cy, lastSeen: performance.now(), markedUp: false, markedDown: false });
    }
  });
  for (let i = tracks.length - 1; i >= 0; i--) {
    if (performance.now() - tracks[i].lastSeen > 2000) tracks.splice(i, 1);
  }
}

function handleFileUpload(file) {
  if (!file) return;
  state.file = file;
  state.fileUrl = URL.createObjectURL(file);
  videoEl.src = state.fileUrl;
  fileNameEl.textContent = file.name || "Unknown source";
  emptyStateEl.style.display = "none";

  state.stats = { cars: 0, trucks: 0, buses: 0, bikes: 0 };
  logList.innerHTML = "";
  updateStatsDisplay();
}

function togglePlayback() {
  if (!videoEl.src) return;

  if (state.isPlaying) {
    videoEl.pause();
    state.isPlaying = false;
    setProcessing(false);
    cancelAnimationFrame(state.rafId);
  } else {
    videoEl.play();
    state.isPlaying = true;
    setProcessing(true);
    startProcessingLoop();
  }

  playIcon.classList.toggle("hidden", state.isPlaying);
  pauseIcon.classList.toggle("hidden", !state.isPlaying);
}

function startProcessingLoop() {
  const ctx = canvasEl.getContext("2d");

  const loop = () => {
    const now = performance.now();
    state.frameCount++;

    if (now - state.lastFpsTime >= 1000) {
      state.fps = Math.round(
        (state.frameCount * 1000) / (now - state.lastFpsTime)
      );
      state.frameCount = 0;
      state.lastFpsTime = now;
      processingText.textContent = `PROCESSING ${state.fps} FPS`;
    }

    canvasEl.width = videoEl.videoWidth || canvasEl.width;
    canvasEl.height = videoEl.videoHeight || canvasEl.height;
    ctx.clearRect(0, 0, canvasEl.width, canvasEl.height);

    const t0 = performance.now();

    // Send frame to backend
    if (
      wsConnected &&
      !wsBusy &&
      state.isProcessing &&
      now - lastRequestTime >= FRAME_INTERVAL_MS
    ) {
      const vw = videoEl.videoWidth;
      const vh = videoEl.videoHeight;

      if (vw && vh) {
        const targetW = 640;
        const targetH = Math.round(vh * (targetW / vw));

        captureCanvas.width = targetW;
        captureCanvas.height = targetH;

        captureCtx.drawImage(videoEl, 0, 0, targetW, targetH);
        const dataUrl = captureCanvas.toDataURL("image/jpeg", 0.7);

        try {
          wsBusy = true;
          lastRequestTime = performance.now();
          ws.send(dataUrl);
        } catch {}
      }
    }

    // Draw detections with correct scaling + offset
    if (state.showOverlay && currentDetections.length > 0) {
      const containerW = canvasEl.width;
      const containerH = canvasEl.height;

      const videoW = videoEl.videoWidth;
      const videoH = videoEl.videoHeight;

      const scale = Math.min(containerW / videoW, containerH / videoH);

      const drawW = videoW * scale;
      const drawH = videoH * scale;

      const offsetX = (containerW - drawW) / 2;
      const offsetY = (containerH - drawH) / 2;

      const yoloW = 640;
      const yoloH = Math.round(videoH * (640 / videoW));

      const scaleX = drawW / yoloW;
      const scaleY = drawH / yoloH;

      const scaled = [];
      currentDetections.forEach((det) => {
        if (det.confidence < state.confidenceThreshold) return;

        const x = offsetX + det.x * scaleX;
        const y = offsetY + det.y * scaleY;
        const w = det.w * scaleX;
        const h = det.h * scaleY;

        let color = "#3b82f6";
        if (det.class === "truck") color = "#f97316";
        if (det.class === "bus") color = "#eab308";
        if (det.class === "motorbike") color = "#a855f7";

        ctx.strokeStyle = color;
        ctx.lineWidth = 3;
        ctx.strokeRect(x, y, w, h);

        const label = `${det.class} ${Math.round(det.confidence * 100)}%`;
        const textWidth = ctx.measureText(label).width;

        ctx.fillStyle = color;
        ctx.globalAlpha = 0.9;
        ctx.fillRect(x, y - 22, textWidth + 10, 22);

        ctx.globalAlpha = 1;
        ctx.fillStyle = "#fff";
        ctx.font = "bold 14px sans-serif";
        ctx.fillText(label, x + 5, y - 6);
        scaled.push({ class: det.class, x, y, w, h });
      });
      updateTracks(scaled);
      const lineYDraw = containerH * state.linePos;
      ctx.strokeStyle = 'rgba(99,102,241,0.9)';
      ctx.lineWidth = 2;
      ctx.setLineDash([6,6]);
      ctx.beginPath();
      ctx.moveTo(0, lineYDraw);
      ctx.lineTo(containerW, lineYDraw);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    const t1 = performance.now();
    inferenceTimeEl.textContent = `${(t1 - t0).toFixed(1)}ms`;

    if (!videoEl.paused && !videoEl.ended) {
      state.rafId = requestAnimationFrame(loop);
    }
  };

  state.rafId = requestAnimationFrame(loop);
}

function connectWS() {
  ws = new WebSocket(WS_URL);

  ws.onopen = () => {
    wsConnected = true;
  };

  ws.onmessage = (event) => {
    wsBusy = false;

    let data;
    try {
      data = JSON.parse(event.data);
    } catch {
      data = null;
    }

    if (!data) return;

    currentDetections = data.detections || [];
    state.stats = data.stats || {};
    updateStatsDisplay();
    const nowDate = new Date();
    const timeString = `${nowDate.getHours()}:${String(nowDate.getMinutes()).padStart(2,'0')}:${String(nowDate.getSeconds()).padStart(2,'0')}`;
    currentDetections.forEach(det => addLogItem({ type: det.class, time: timeString, confidence: det.confidence }));
    state.analytics.total += currentDetections.length;
    analyticsTotal.textContent = state.analytics.total;
    analyticsUp.textContent = state.analytics.passedUp;
    analyticsDown.textContent = state.analytics.passedDown;
    analyticsFps.textContent = state.fps;
  };

  ws.onerror = () => {
    wsConnected = false;
    wsBusy = false;
  };

  ws.onclose = () => {
    wsConnected = false;
    wsBusy = false;
    setTimeout(connectWS, 1000);
  };
}

fileInputEl.addEventListener("change", (e) =>
  handleFileUpload(e.target.files[0])
);

playBtn.addEventListener("click", togglePlayback);

videoEl.addEventListener("play", () => {
  state.isPlaying = true;
  setProcessing(true);
  playIcon.classList.add("hidden");
  pauseIcon.classList.remove("hidden");
  startProcessingLoop();
});

videoEl.addEventListener("pause", () => {
  state.isPlaying = false;
  setProcessing(false);
  playIcon.classList.remove("hidden");
  pauseIcon.classList.add("hidden");
  cancelAnimationFrame(state.rafId);
});

overlayToggle.addEventListener("click", () => {
  state.showOverlay = !state.showOverlay;

  overlayToggle.className = `p-2 rounded-lg border ${
    state.showOverlay
      ? "bg-indigo-500/20 border-indigo-500 text-indigo-400"
      : "border-slate-600 text-slate-400"
  }`;

  eyeOn.classList.toggle("hidden", !state.showOverlay);
  eyeOff.classList.toggle("hidden", state.showOverlay);
});

clearBtn.addEventListener("click", () => {
  if (state.fileUrl) URL.revokeObjectURL(state.fileUrl);

  state.file = null;
  state.fileUrl = null;
  state.isPlaying = false;

  videoEl.pause();
  videoEl.removeAttribute("src");
  videoEl.load();

  emptyStateEl.style.display = "";
  cancelAnimationFrame(state.rafId);
});

confSlider.addEventListener("input", (e) => {
  state.confidenceThreshold = parseFloat(e.target.value);
  confLabel.textContent = `${(state.confidenceThreshold * 100).toFixed(0)}%`;
});

iouSlider.addEventListener("input", (e) => {
  state.iouThreshold = parseFloat(e.target.value);
  iouLabel.textContent = `${(state.iouThreshold * 100).toFixed(0)}%`;
});

// Export CSV
exportBtn && exportBtn.addEventListener('click', () => {
  const rows = ['time,type,confidence'];
  const children = Array.from(logList.children);
  children.forEach(child => {
    const type = child.dataset.type || '';
    const time = child.dataset.time || '';
    const conf = child.dataset.confidence || '';
    rows.push(`${time},${type},${conf}`);
  });
  const blob = new Blob([rows.join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'report.csv';
  a.click();
  URL.revokeObjectURL(url);
});

// Initial
updateStatsDisplay();
confLabel.textContent = `${state.confidenceThreshold * 100}%`;
iouLabel.textContent = `${state.iouThreshold * 100}%`;

connectWS();

// Tabs
function setTab(tab) {
  const showLive = tab === 'live';
  const showAnalytics = tab === 'analytics';
  const showSettings = tab === 'settings';
  sectionLive.classList.toggle('hidden', !showLive);
  sectionAnalytics.classList.toggle('hidden', !showAnalytics);
  sectionSettings.classList.toggle('hidden', !showSettings);
  navLive.classList.toggle('bg-indigo-600/10', showLive);
  navLive.classList.toggle('text-indigo-400', showLive);
  navAnalytics.classList.toggle('bg-indigo-600/10', showAnalytics);
  navAnalytics.classList.toggle('text-indigo-400', showAnalytics);
  navSettings.classList.toggle('bg-indigo-600/10', showSettings);
  navSettings.classList.toggle('text-indigo-400', showSettings);
}
navLive && navLive.addEventListener('click', () => setTab('live'));
navAnalytics && navAnalytics.addEventListener('click', () => setTab('analytics'));
navSettings && navSettings.addEventListener('click', () => setTab('settings'));
setTab('live');

// Settings bindings
settingOverlay && settingOverlay.addEventListener('change', (e) => { state.showOverlay = e.target.checked; });
linePosSlider && linePosSlider.addEventListener('input', (e) => { state.linePos = parseFloat(e.target.value); linePosLabel.textContent = `${Math.round(state.linePos*100)}%`; });
settingsConfSlider && settingsConfSlider.addEventListener('input', (e) => { state.confidenceThreshold = parseFloat(e.target.value); settingsConfLabel.textContent = `${(state.confidenceThreshold*100).toFixed(0)}%`; confSlider.value = state.confidenceThreshold; confLabel.textContent = settingsConfLabel.textContent; });
settingsIouSlider && settingsIouSlider.addEventListener('input', (e) => { state.iouThreshold = parseFloat(e.target.value); settingsIouLabel.textContent = `${(state.iouThreshold*100).toFixed(0)}%`; iouSlider.value = state.iouThreshold; iouLabel.textContent = settingsIouLabel.textContent; });

// GPU usage poll
async function fetchSystemStats() {
  try {
    const res = await fetch('http://localhost:8000/system/stats');
    const data = await res.json();
    const pct = typeof data.gpu_memory_used_percent === 'number' ? data.gpu_memory_used_percent : (typeof data.gpu_utilization_percent === 'number' ? data.gpu_utilization_percent : null);
    if (pct !== null) {
      gpuUsageText.textContent = `${pct}%`; gpuUsageBar.style.width = `${pct}%`;
    } else {
      gpuUsageText.textContent = '—'; gpuUsageBar.style.width = '0%';
    }
  } catch {}
}
setInterval(fetchSystemStats, 2000);
fetchSystemStats();
