import cv2
import numpy as np
import easyocr
import re
import unicodedata
import difflib
from ultralytics import YOLO
from config import MODEL_PATH
from duplicate_filter import SubtitleMemory
#from paddleocr import PaddleOCR

def increase_saturation(hsv, scale=1.5):
    hsv_copy = hsv.copy()
    s = hsv_copy[:, :, 1].astype(np.float32)
    s = np.clip(s * scale, 0, 255).astype(np.uint8)
    hsv_copy[:, :, 1] = s
    return hsv_copy

def preprocess_frame_color_background_white_text(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    hsv_saturated = increase_saturation(hsv, scale=1.5)  # 彩度
    lower_white = np.array([0, 0, 210])
    upper_white = np.array([180, 40, 255])
    mask_white = cv2.inRange(hsv_saturated, lower_white, upper_white)
    res_white = cv2.bitwise_and(frame, frame, mask=mask_white)
    gray_image = cv2.cvtColor(res_white, cv2.COLOR_BGR2GRAY)
    return gray_image


def extract_ocr_subtitles(video_path, interval=10):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("動画が読み込めませんでした。パスを確認してください。")
        return []

    reader = easyocr.Reader(['ch_sim', 'en'], gpu=True)
    #ocr = PaddleOCR(use_angle_cls=True, lang='ch', show_log=False)
    memory = SubtitleMemory()
    results = []
    frame_count = 0

    yolo_model = YOLO(MODEL_PATH)  # 自作字幕検出モデル

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % interval == 0:
            # YOLOで字幕領域を検出
            yolo_results = yolo_model.predict(frame, verbose=False)
            detections = yolo_results[0].boxes

            if detections is None:
                continue

            for box in detections:
                # 座標を取得
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())

                x1 = max(0, x1 - 10)
                y1 = max(0, y1 - 10)   
                x2 = min(frame.shape[1], x2 + 10)
                y2 = min(frame.shape[0], y2 + 10)

                subtitle_region = frame[y1:y2, x1:x2]

                # 前処理＋OCR
                processed = preprocess_frame_color_background_white_text(subtitle_region)
                ocr_results = reader.readtext(processed)
                for bbox, text, conf in ocr_results:
                    if conf < 0.5:
                        continue
                    if not memory.is_new(text):
                        continue
                    timestamp = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0
                    results.append({"timestamp": timestamp, "text": text.strip()})

        frame_count += 1

    cap.release()
    return results
