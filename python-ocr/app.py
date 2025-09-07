# app.py
from processor import analyze
from project_2_final import startProcess,build_final_words
from starlette.concurrency import run_in_threadpool
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import numpy as np, cv2
app = FastAPI()

@app.post("/analyze")
async def analyze_endpoint(
    file: UploadFile = File(...),
    filename: str = Form(None),  # optional
    # img_path: str = Form(None)  # no longer needed
):
    print("hello")
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "empty file")

    return analyze(image_bytes, filename=filename )


@app.post("/analyze/hand")
async def analyze_endpoint_hand(
    file: UploadFile = File(...),
    filename: str = Form(None),  # optional
    # img_path: str = Form(None)  # no longer needed
):
    print("hello from hand") 
    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(400, "empty file")
    await run_in_threadpool(startProcess, image_bytes)
    return build_final_words("final_db_ready.json")


@app.post("/route-invoice")
def route_invoice(file: UploadFile = File(...)):
    import easyocr
    img = np.frombuffer(file.file.read(), np.uint8)
    bgr = cv2.imdecode(img, cv2.IMREAD_COLOR)
    printed, score, feats = is_printed_image(bgr)
    reader = easyocr.Reader(['ar'])
    result = reader.readtext(img)
    print(result)
    route = "/analyze/print" if printed else "/analyze/hand"
    return {"printed": printed, "score": score, "features": feats, "route": route}


import cv2, numpy as np
from typing import Tuple, Dict, Any

def is_printed_image(bgr: np.ndarray) -> Tuple[bool, float, Dict[str, Any]]:
    """
    Heuristic classifier for printed vs handwritten.
    Returns: (printed: bool, score: 0..1, features: dict)
    """
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # robust binarization for photos of paper
    gray = cv2.medianBlur(gray, 3)
    th = cv2.adaptiveThreshold(gray, 255,
                               cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY_INV, 35, 15)

    # connected components -> measure character sizes
    n, labels, stats, _ = cv2.connectedComponentsWithStats(th, connectivity=8)
    # skip background (label 0) and filter tiny blobs
    H, W = th.shape
    areas   = stats[1:, cv2.CC_STAT_AREA]
    heights = stats[1:, cv2.CC_STAT_HEIGHT]
    widths  = stats[1:, cv2.CC_STAT_WIDTH]
    keep = (areas > max(15, 0.00002 * H * W)) & (heights < 0.25 * H) & (widths < 0.25 * W)
    if not np.any(keep):
        return (False, 0.0, {"reason": "no text-like components"})

    idxs = np.where(keep)[0] + 1  # shift back to label ids

    # stroke-width proxy via distance transform (SWT-lite)
    # more uniform stroke widths => more likely printed
    dt = cv2.distanceTransform(th, cv2.DIST_L2, 5)
    sw = np.array([dt[labels == i].mean() for i in idxs])

    # character size uniformity
    h = heights[keep].astype(np.float32)

    def coeff_var(x: np.ndarray) -> float:
        m = float(np.mean(x))
        return float(np.std(x) / (m + 1e-6))

    height_cv = coeff_var(h)
    sw_cv     = coeff_var(sw)

    # combine into a "printedness" score (1 = very printed-like)
    s_height = 1.0 - min(height_cv, 1.0)     # lower variation -> higher score
    s_sw     = 1.0 - min(sw_cv, 1.0)
    score = 0.5 * s_height + 0.5 * s_sw

    printed = (height_cv < 0.50) and (sw_cv < 0.60)

    return printed, round(score, 3), {
        "components": int(len(idxs)),
        "height_cv": round(height_cv, 3),
        "stroke_cv": round(sw_cv, 3),
    }
