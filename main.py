import cv2
import numpy as np
import base64
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import time

try:
    import torch
except Exception:
    torch = None

try:
    import pynvml
    pynvml.nvmlInit()
    _pynvml_available = True
except Exception:
    _pynvml_available = False

# -------------------------
# Initialize FastAPI
# -------------------------
app = FastAPI(title="YOLOv11 Vehicle Detection API")

# Allow CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Load YOLO model with BoT-SORT
# -------------------------
print("Loading YOLO11 Model...")
model = YOLO("yolo11n.pt")
print("Model Loaded Successfully (BoT-SORT enabled).")


# -------------------------
# Helper: Base64 → CV2 image
# -------------------------
def base64_to_cv2(base64_string):
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Error decoding image: {e}")
        return None


@app.get("/")
def home():
    return {"status": "running", "model": "YOLOv11 + BoT-SORT"}


# -------------------------
# GPU System Stats
# -------------------------
@app.get("/system/stats")
def system_stats():
    gpu_available = False
    gpu_util = None
    gpu_mem_total = None
    gpu_mem_used = None
    device = "cuda"

    try:
        if torch is not None and torch.cuda.is_available():
            gpu_available = True
            device = "cuda"
            mem_alloc = torch.cuda.memory_allocated(0)
            mem_total = torch.cuda.get_device_properties(0).total_memory
            gpu_mem_total = int(mem_total)
            gpu_mem_used = int(mem_alloc)

            if _pynvml_available:
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                util = pynvml.nvmlDeviceGetUtilizationRates(handle)
                gpu_util = int(util.gpu)
        else:
            device = "cpu"
    except Exception:
        pass

    percent_mem = None
    if gpu_mem_total and gpu_mem_total > 0 and gpu_mem_used is not None:
        percent_mem = round((gpu_mem_used / gpu_mem_total) * 100)

    return {
        "gpu_available": gpu_available,
        "device": device,
        "gpu_utilization_percent": gpu_util,
        "gpu_memory_total_bytes": gpu_mem_total,
        "gpu_memory_used_bytes": gpu_mem_used,
        "gpu_memory_used_percent": percent_mem,
        "timestamp": time.time(),
    }


# -------------------------
# Websocket Video Detection (BoT-SORT)
# -------------------------
@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:

            # 1. Receive frame in Base64
            data = await websocket.receive_text()
            frame = base64_to_cv2(data)
            if frame is None:
                continue

            # 2. Run YOLO + BoT-SORT tracking
            results = model.track(
                frame,
                persist=True,
                tracker="botsort.yaml",    # << Using BoT-SORT
                stream=True,
                verbose=False
            )

            detections_output = []
            class_counts = {"cars": 0, "trucks": 0, "buses": 0, "bikes": 0}

            vehicle_classes = ["car", "motorcycle", "bus", "truck"]

            # 3. Extract tracked detections
            for r in results:
                boxes = r.boxes

                if boxes is None or len(boxes) == 0:
                    continue

                xyxy = boxes.xyxy.cpu().numpy()
                conf = boxes.conf.cpu().numpy()
                cls = boxes.cls.cpu().numpy().astype(int)

                # BoT-SORT IDs
                track_ids = None
                if boxes.id is not None:
                    track_ids = boxes.id.cpu().numpy().astype(int)
                else:
                    continue  # Without ID, skip (shouldn't happen with BoT-SORT)

                for box, c, class_id, tid in zip(xyxy, conf, cls, track_ids):

                    class_name = model.names[class_id]

                    if class_name not in vehicle_classes:
                        continue

                    # Normalize name for frontend
                    if class_name == "motorcycle":
                        class_name = "motorbike"

                    x1, y1, x2, y2 = box
                    w = x2 - x1
                    h = y2 - y1

                    # update counts
                    if class_name == "car":
                        class_counts["cars"] += 1
                    elif class_name == "truck":
                        class_counts["trucks"] += 1
                    elif class_name == "bus":
                        class_counts["buses"] += 1
                    elif class_name == "motorbike":
                        class_counts["bikes"] += 1

                    detections_output.append({
                        "id": f"{class_name}_{tid}",   # BoT-SORT track ID
                        "class": class_name,
                        "confidence": float(c),
                        "x": float(x1),
                        "y": float(y1),
                        "w": float(w),
                        "h": float(h)
                    })

            # 4. Send JSON result to frontend
            await websocket.send_json({
                "detections": detections_output,
                "stats": class_counts
            })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        try:
            await websocket.close()
        except:
            pass
