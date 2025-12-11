import cv2
import torch
from ultralytics import YOLO

# ------------------ CONFIG ------------------
MODEL_PATH = "yolo11n_finetuned.pt"   # your YOLO11 .pt model
VIDEO = 0                   # webcam or path to video
CONF_THRESH = 0.50
# --------------------------------------------

# Check CUDA
device = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", device)

# Load YOLO11 model
model = YOLO(MODEL_PATH)
model.to(device)

# Start video capture
cap = cv2.VideoCapture("C:\\Users\\Samarth\\Downloads\\stock-footage-mysore-karnataka-india-a-bustling-street-scene-in-the-center-of-the-south-indian.mp4")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Run detection
    results = model(frame, conf=CONF_THRESH, verbose=False)[0]

    # Draw detections manually using OpenCV
    for box in results.boxes:
        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
        cls = int(box.cls)
        conf = float(box.conf)

        label = f"{results.names[cls]} {conf:.2f}"

        # Draw box
        cv2.rectangle(
            frame,
            (int(x1), int(y1)),
            (int(x2), int(y2)),
            (0, 255, 0), 2
        )

        # Draw label
        cv2.putText(
            frame,
            label,
            (int(x1), int(y1) - 8),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2
        )

    cv2.imshow("YOLO11 Detection (CUDA)", frame)

    if cv2.waitKey(1) & 0xFF == 27:  # ESC to quit
        break

cap.release()
cv2.destroyAllWindows()
