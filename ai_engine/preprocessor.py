"""
Preprocessor Module
Function 1: preprocess_and_deskew()
Handles auto-cropping, deskewing (perspective transformation), shadow removal, and compression.
"""

import cv2
import numpy as np
from PIL import Image
import io

def preprocess_and_deskew(image_bytes: bytes) -> tuple[np.ndarray, bytes]:
    """
    Takes raw image bytes from camera/upload,
    straightens perspective, removes shadows, enhances contrast,
    and returns (processed_cv2_image, optimized_compressed_bytes).
    """
    # 1. Decode image bytes to OpenCV matrix
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Invalid image data provided")

    orig_h, orig_w = img.shape[:2]

    # 2. Convert to grayscale and apply Gaussian Blur
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. Detect edges for paper boundary contour
    edged = cv2.Canny(blurred, 50, 200)
    contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:5]

    doc_contour = None
    for c in contours:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        # If 4-point polygon found and large enough area (> 20% of image)
        if len(approx) == 4 and cv2.contourArea(c) > (orig_h * orig_w * 0.2):
            doc_contour = approx
            break

    # 4. Perform Perspective Transform if 4 corners found
    if doc_contour is not None:
        pts = doc_contour.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        
        # Top-left has smallest sum, bottom-right has largest sum
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        
        # Top-right has smallest diff, bottom-left has largest diff
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        (tl, tr, br, bl) = rect
        width_a = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
        width_b = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
        max_w = max(int(width_a), int(width_b))

        height_a = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
        height_b = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
        max_h = max(int(height_a), int(height_b))

        dst = np.array([
            [0, 0],
            [max_w - 1, 0],
            [max_w - 1, max_h - 1],
            [0, max_h - 1]
        ], dtype="float32")

        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(img, M, (max_w, max_h))
    else:
        warped = img.copy()

    # 5. Shadow Reduction and Contrast Equalization
    rgb_planes = cv2.split(warped)
    result_planes = []
    for plane in rgb_planes:
        dilated = cv2.dilate(plane, np.ones((7, 7), np.uint8))
        bg_img = cv2.medianBlur(dilated, 21)
        diff_img = 255 - cv2.absdiff(plane, bg_img)
        norm_img = cv2.normalize(diff_img, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX, dtype=cv2.CV_8UC1)
        result_planes.append(norm_img)

    enhanced = cv2.merge(result_planes)

    # 6. Compress for 2G network resilience (< 50KB)
    pil_img = Image.fromarray(cv2.cvtColor(enhanced, cv2.COLOR_BGR2RGB))
    buf = io.BytesIO()
    # Save optimized JPEG at quality 82
    pil_img.save(buf, format="JPEG", quality=82, optimize=True)
    compressed_bytes = buf.getvalue()

    return enhanced, compressed_bytes
