import cv2
import pytesseract
from PIL import Image
import numpy as np
import random
from pytesseract import Output


def preprocess_image(image_path, crop_box=None):
    """Preprocess the image with optional cropping"""
    image = cv2.imread(image_path)

    if crop_box:
        x1, y1, x2, y2 = crop_box
        image = image[y1:y2, x1:x2]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, thresholded = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return thresholded


def perform_ocr(image_path, psm=3, lang="eng", crop_box=None):
    """
    Perform OCR with preprocessing, confidence scoring, and heuristic accuracy estimation.
    crop_box: (x1, y1, x2, y2) format
    """
    image = Image.open(image_path)
    width, height = image.size
    total_pixels = width * height

    # Optional Crop
    if crop_box:
        image = image.crop(crop_box)

    image_cv = np.array(image)
    image_cv = cv2.cvtColor(image_cv, cv2.COLOR_RGB2BGR)

    # Preprocessing
    gray = cv2.cvtColor(image_cv, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    _, processed = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    config = f'--psm {psm}'
    text = pytesseract.image_to_string(processed, config=config, lang=lang)

    # Confidence Scores
    try:
        data = pytesseract.image_to_data(processed, config=config, lang=lang, output_type=Output.DICT)
        confidences = [int(conf) for conf in data['conf'] if conf != '-1']
        avg_conf = sum(confidences) / len(confidences) if confidences else 0
    except:
        avg_conf = 0  # fallback

    # Heuristic OCR quality estimation
    text_length = len(text.strip())
    density_score = (text_length / (total_pixels / 1000)) * 1.5 if total_pixels else 0
    estimated_accuracy = min((0.6 * avg_conf + 0.4 * density_score), 100)

    return text, round(estimated_accuracy, 2)


def simulate_damaged_text(text, mask_ratio=0.1):
    """Simulate corrupted text for restoration use cases"""
    words = text.split()
    num_masks = int(len(words) * mask_ratio)
    mask_indices = random.sample(range(len(words)), num_masks)
    for i in mask_indices:
        words[i] = "[MASK]"
    return " ".join(words)
