#!/usr/bin/env python3
from PIL import Image, ImageOps, ImageFilter
import cv2
import numpy as np
from pathlib import Path

def preprocess_image(path: Path) -> Image.Image:
    """
    Returns a preprocessed PIL Image for OCR.
    """
    # Open image
    img = Image.open(path).convert("RGB")

    # Convert to grayscale
    gray = ImageOps.grayscale(img)

    # Enhance contrast
    gray = ImageOps.autocontrast(gray)

    # Convert to numpy for OpenCV operations
    np_img = np.array(gray)

    # Denoise / remove small artifacts
    np_img = cv2.fastNlMeansDenoising(np_img, None, 30, 7, 21)

    # Threshold (binarize)
    _, np_img = cv2.threshold(np_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Deskew
    coords = np.column_stack(np.where(np_img > 0))
    if coords.size != 0:
        angle = cv2.minAreaRect(coords)[-1]
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
        (h, w) = np_img.shape
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        np_img = cv2.warpAffine(np_img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

    # Convert back to PIL
    processed_img = Image.fromarray(np_img)

    return processed_img
