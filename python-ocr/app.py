# app.py
from processor import analyze

from fastapi import FastAPI, UploadFile, File, Form, HTTPException

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

