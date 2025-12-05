# SORT tracker by Alex Bewley (modified minimal version)
import numpy as np
from filterpy.kalman import KalmanFilter

def iou(bb_test, bb_gt):
    xx1 = max(bb_test[0], bb_gt[0])
    yy1 = max(bb_test[1], bb_gt[1])
    xx2 = min(bb_test[2], bb_gt[2])
    yy2 = min(bb_test[3], bb_gt[3])
    w = max(0., xx2 - xx1)
    h = max(0., yy2 - yy1)
    wh = w * h
    o = wh / ((bb_test[2]-bb_test[0])*(bb_test[3]-bb_test[1])
              + (bb_gt[2]-bb_gt[0])*(bb_gt[3]-bb_gt[1]) - wh)
    return o

class KalmanBoxTracker:
    count = 0

    def __init__(self, bbox):
        self.kf = KalmanFilter(dim_x=7, dim_z=4)
        self.kf.F = np.array([[1,0,0,0,1,0,0],
                              [0,1,0,0,0,1,0],
                              [0,0,1,0,0,0,1],
                              [0,0,0,1,0,0,0],
                              [0,0,0,0,1,0,0],
                              [0,0,0,0,0,1,0],
                              [0,0,0,0,0,0,1]])
        self.kf.H = np.array([[1,0,0,0,0,0,0],
                              [0,1,0,0,0,0,0],
                              [0,0,1,0,0,0,0],
                              [0,0,0,1,0,0,0]])

        self.kf.R *= 1.
        self.kf.P *= 10.
        self.kf.Q *= 0.01
 
        self.kf.x[:4] = np.array(bbox).reshape((4,1))
        self.time_since_update = 0
        self.id = KalmanBoxTracker.count
        KalmanBoxTracker.count += 1
        self.history = []

    def update(self, bbox):
        self.time_since_update = 0
        self.kf.update(bbox)

    def predict(self):
        self.kf.predict()
        return self.kf.x[:4]

class Sort:
    def __init__(self, max_age=10, min_hits=3, iou_threshold=0.3):
        self.max_age = max_age
        self.min_hits = min_hits
        self.iou_threshold = iou_threshold
        self.trackers = []

    def update(self, dets):
        updated_tracks = []

        for det in dets:
            best_iou = 0
            best_tracker = None

            for trk in self.trackers:
                iou_score = iou(det[:4], trk.kf.x[:4])
                if iou_score > best_iou and iou_score > self.iou_threshold:
                    best_iou = iou_score
                    best_tracker = trk

            if best_tracker:
                best_tracker.update(det[:4])
            else:
                self.trackers.append(KalmanBoxTracker(det[:4]))

        for trk in self.trackers:
            trk.predict()
            updated_tracks.append(
                np.concatenate((trk.kf.x[:4].reshape(-1), [trk.id]))
            )

        return np.array(updated_tracks)
