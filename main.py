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

# Initialize FastAPI
app = FastAPI(title="YOLOv11 Vehicle Detection API")

# Allow CORS (Cross-Origin Resource Sharing) so React can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOAD MODEL ---
# Ensure you have the model weights. YOLO11 will download 'yolo11n.pt' automatically if missing.
# You can switch to 'yolo11s.pt' or 'yolo11m.pt' for better accuracy but slower speed.
print("Loading YOLO11 Model...")
model = YOLO("yolo11n.pt") 
print("Model Loaded Successfully.")

# Helper: Decode Base64 Image to OpenCV format
def base64_to_cv2(base64_string):
    try:
        # Remove header if present (e.g., "data:image/jpeg;base64,")
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
    return {"status": "running", "model": "YOLOv11"}

@app.get("/system/stats")
def system_stats():
    gpu_available = False
    gpu_util = None
    gpu_mem_total = None
    gpu_mem_used = None
    device = "cpu"

    try:
        if torch is not None and torch.cuda.is_available():
            gpu_available = True
            device = "cuda"
            # Memory usage via torch
            mem_alloc = torch.cuda.memory_allocated(0)
            mem_total = torch.cuda.get_device_properties(0).total_memory
            gpu_mem_total = int(mem_total)
            gpu_mem_used = int(mem_alloc)
            # Utilization via NVML if available
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

@app.websocket("/ws/detect")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("Client connected")
    
    try:
        while True:
            # 1. Receive frame data from Frontend (Base64 string)
            data = await websocket.receive_text()
            
            # 2. Decode image
            frame = base64_to_cv2(data)
            
            if frame is None:
                continue

            # 3. Run YOLO11 Inference
            # stream=True is efficient for videos. verbose=False quiets console output.
            results = model(frame, stream=True, verbose=False)

            detections = []
            class_counts = {}

            # 4. Process Results
            for r in results:
                boxes = r.boxes
                for box in boxes:
                    # Bounding Box Coordinates (x, y, w, h)
                    x, y, w, h = box.xywh[0].tolist()
                    
                    # Confidence
                    conf = float(box.conf[0])
                    
                    # Class Name
                    cls_id = int(box.cls[0])
                    cls_name = model.names[cls_id]

                    # Filter for vehicles only (COCO dataset IDs)
                    # 2: car, 3: motorcycle, 5: bus, 7: truck
                    vehicle_classes = ['car', 'motorcycle', 'bus', 'truck']
                    
                    if cls_name in vehicle_classes:
                        # Add to list
                        detections.append({
                            "id": f"{cls_name}_{len(detections)}", # Simple ID generation
                            "class": cls_name if cls_name != 'motorcycle' else 'motorbike', # Match frontend naming
                            "confidence": conf,
                            "x": x - (w / 2), # Convert center-x to top-left x
                            "y": y - (h / 2), # Convert center-y to top-left y
                            "w": w,
                            "h": h
                        })

                        # Count stats
                        class_key = cls_name + 's' if cls_name != 'bus' else 'buses'
                        if cls_name == 'motorcycle': class_key = 'bikes'
                        
                        class_counts[class_key] = class_counts.get(class_key, 0) + 1

            # 5. Send JSON response back to React
            response = {
                "detections": detections,
                "stats": class_counts
            }
            
            await websocket.send_json(response)

    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close()
