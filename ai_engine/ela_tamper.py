"""
ELA Tampering & Forensics Module
Function 2: detect_tampering_ela()
Performs Error Level Analysis (ELA) to detect localized Photoshop edits,
number modifications (marks/income), and produces visual heatmaps.
"""

from PIL import Image, ImageChops, ImageEnhance
import numpy as np
import io
import base64

def detect_tampering_ela(image_bytes: bytes, quality: int = 90) -> dict:
    """
    Performs Error Level Analysis (ELA) on input image bytes.
    Returns:
      - is_tampered (bool): True if localized tampering is detected
      - tamper_score (float): 0 (Clean) to 100 (Extremely Tampered)
      - max_difference (float): Peak pixel deviation
      - heatmap_base64 (str): Data URL for displaying the visual forensic heatmap in UI
      - explanation (str): Human-readable audit explanation
    """
    try:
        original = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    except Exception as e:
        return {
            "is_tampered": False,
            "tamper_score": 0.0,
            "max_difference": 0.0,
            "heatmap_base64": "",
            "explanation": f"Error parsing image: {str(e)}"
        }

    # 1. Resave image at standard JPEG quality (90) to establish compression baseline
    buffer = io.BytesIO()
    original.save(buffer, 'JPEG', quality=quality)
    buffer.seek(0)
    resaved = Image.open(buffer)

    # 2. Compute absolute difference between original and resaved
    diff = ImageChops.difference(original, resaved)

    # 3. Calculate extrema and scale difference for human/machine visibility
    extrema = diff.getextrema()
    max_diff = max([ex[1] for ex in extrema]) if extrema else 1
    if max_diff == 0:
        max_diff = 1

    scale = 255.0 / max_diff
    enhanced_diff = ImageEnhance.Brightness(diff).enhance(scale)

    # 4. Statistical Variance Analysis across image regions
    diff_arr = np.array(enhanced_diff)
    gray_diff = np.mean(diff_arr, axis=2)

    h, w = gray_diff.shape
    patch_h, patch_w = max(h // 12, 16), max(w // 12, 16)
    local_stds = []
    local_maxes = []
    
    for i in range(0, h - patch_h, patch_h):
        for j in range(0, w - patch_w, patch_w):
            patch = gray_diff[i:i + patch_h, j:j + patch_w]
            local_stds.append(np.std(patch))
            local_maxes.append(np.max(patch))

    local_stds = np.array(local_stds)
    local_maxes = np.array(local_maxes)
    
    mean_std = np.mean(local_stds) if len(local_stds) > 0 else 1.0
    max_local_std = np.max(local_stds) if len(local_stds) > 0 else 1.0

    # In a genuine document, compression variance across text regions is relatively uniform.
    # In a tampered document with spliced numbers/patches, max_local_std is much higher than surrounding text.
    spread_ratio = (max_local_std / (mean_std + 1e-4))

    # Base tamper score
    if spread_ratio > 2.8 and max_diff > 35:
        tamper_score = min(spread_ratio * 25.0, 96.0)
        is_tampered = True
    else:
        tamper_score = min(spread_ratio * 4.0, 22.0)
        is_tampered = False

    # 5. Convert visual heatmap to Base64 for the frontend UI
    heatmap_buf = io.BytesIO()
    enhanced_diff.save(heatmap_buf, format="JPEG")
    heatmap_b64 = "data:image/jpeg;base64," + base64.b64encode(heatmap_buf.getvalue()).decode('utf-8')

    if is_tampered:
        explanation = f"High compression disparity detected (Anomaly Score: {tamper_score:.1f}%). Localized pixels indicate Photoshop or digital alteration in text/number fields."
    else:
        explanation = f"Uniform compression signature verified (Tamper Score: {tamper_score:.1f}%). No digital splicing or localized text tampering detected."

    return {
        "is_tampered": is_tampered,
        "tamper_score": round(tamper_score, 1),
        "max_difference": round(float(max_diff), 1),
        "heatmap_base64": heatmap_b64,
        "explanation": explanation
    }
