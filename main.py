import cv2
import numpy as np
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from ultralytics import YOLO
import time
import torch

# -------------------------
# Initialize FastAPI
# -------------------------
app = FastAPI(title="YOLOv11 Vehicle Detection API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Load YOLO model
# -------------------------
print("Loading YOLO11 Model...")
model = YOLO("yolo11n_finetuned.pt")
# Force GPU if available
if torch.cuda.is_available():
    model.to("cuda")
    print("Using GPU: CUDA")
else:
    print("Using CPU")
print("Model Loaded Successfully.")

# -------------------------
# System Stats
# -------------------------
@app.get("/system/stats")
def system_stats():
    # Basic dummy stats if nvidia-smi isn't queried directly
    # You can keep your complex stats logic here if you wish
    return {
        "status": "online",
        "timestamp": time.time()
    }

@app.get("/")
def home():
    return {"status": "running", "mode": "Binary/Blob"}

# -------------------------
# Websocket Video Detection
# -------------------------
@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")

    try:
        while True:
            # 1. Receive Raw Bytes
            # If the frontend sends text/base64, receive_bytes() might fail or receive_text() is needed.
            # We strictly expect bytes here for speed.
            try:
                data = await websocket.receive_bytes()
            except RuntimeError:
                # This often happens if the frontend sends Text but we expect Bytes
                print("Error: Received text frame instead of bytes. ignoring.")
                continue

            # 2. Decode Image directly from memory (Fastest)
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                continue

            # 3. Run YOLO + BoT-SORT
            # Optimized parameters for speed
            results = model.track(
                frame,
                persist=True,
                tracker="botsort.yaml",
                verbose=False,
                iou=0.5,
                conf=0.45 
            )

            detections_output = []
            class_counts = {"cars": 0, "trucks": 0, "buses": 0, "bikes": 0}
            vehicle_classes = ["car", "motorcycle", "bus", "truck"]

            for r in results:
                boxes = r.boxes
                if boxes is None or len(boxes) == 0:
                    continue

                xyxy = boxes.xyxy.cpu().numpy()
                conf = boxes.conf.cpu().numpy()
                cls = boxes.cls.cpu().numpy().astype(int)
                
                # Handle IDs (BoT-SORT)
                if boxes.id is not None:
                    track_ids = boxes.id.cpu().numpy().astype(int)
                else:
                    track_ids = [-1] * len(boxes)

                for box, c, class_id, tid in zip(xyxy, conf, cls, track_ids):
                    class_name = model.names[class_id]

                    if class_name not in vehicle_classes:
                        continue
                    
                    if class_name == "motorcycle":
                        class_name = "motorbike"

                    # Update counts
                    if class_name == "car": class_counts["cars"] += 1
                    elif class_name == "truck": class_counts["trucks"] += 1
                    elif class_name == "bus": class_counts["buses"] += 1
                    elif class_name == "motorbike": class_counts["bikes"] += 1

                    x1, y1, x2, y2 = box
                    detections_output.append({
                        "id": f"{class_name}_{tid}",
                        "class": class_name,
                        "confidence": float(c),
                        "x": float(x1),
                        "y": float(y1),
                        "w": float(x2 - x1),
                        "h": float(y2 - y1)
                    })

            # 4. Send JSON Result
            await websocket.send_json({
                "detections": detections_output,
                "stats": class_counts
            })

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Server Error: {e}")
        try:
            await websocket.close()
        except:
            pass