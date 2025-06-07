from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
import requests
import random
import time
import os
from PIL import Image
from pyzbar.pyzbar import decode
from io import BytesIO

router = APIRouter(tags=["Image & Barcode"])  # ✅ Removed prefix

# Cache to store barcode results and avoid repeated API calls
_cache = {}
CACHE_TTL = 60 * 60  # 1 hour

UPLOAD_DIR = "uploaded_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 1. Simulated Ingredient Scanner
@router.post("/scan-ingredients")
async def scan_ingredients(file: UploadFile = File(...)):
    possible_ingredients = ["tomato", "onion", "carrot", "potato", "spinach", "garlic", "pepper"]
    detected = random.sample(possible_ingredients, k=3)
    return {"detected_ingredients": detected}

# 2. Manual Barcode Scanner
class BarcodeRequest(BaseModel):
    barcode: str

@router.post("/barcode-scan/")
async def barcode_scan(data: BarcodeRequest):
    barcode = data.barcode.strip()

    cached = _cache.get(barcode)
    if cached and (time.time() - cached['timestamp'] < CACHE_TTL):
        return cached['data']

    url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
    response = requests.get(url)

    if response.status_code != 200:
        raise HTTPException(status_code=503, detail="Open Food Facts API not reachable")

    data = response.json()
    if data.get("status") != 1:
        raise HTTPException(status_code=404, detail="Product not found")

    product = data.get("product", {})
    nutriments = product.get("nutriments", {})

    key_nutrients = {
        "energy_kcal": nutriments.get("energy-kcal_100g"),
        "fat_g": nutriments.get("fat_100g"),
        "sugars_g": nutriments.get("sugars_100g"),
        "proteins_g": nutriments.get("proteins_100g"),
        "salt_g": nutriments.get("salt_100g"),
    }

    ingredients_text = product.get("ingredients_text", "").replace("\n", " ").strip()

    result = {
        "product_name": product.get("product_name", "Unknown"),
        "brands": product.get("brands", "Unknown"),
        "ingredients_text": ingredients_text or "Not available",
        "nutrients_per_100g": key_nutrients,
        "image_url": product.get("image_front_url")
    }

    _cache[barcode] = {"timestamp": time.time(), "data": result}
    return result

# 3. Barcode Scanner from Image Upload
@router.post("/upload-and-scan-barcode/")
async def upload_and_scan_barcode(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        img = Image.open(BytesIO(img_bytes))
        barcodes = decode(img)

        if not barcodes:
            raise HTTPException(status_code=400, detail="No barcode detected in image.")

        barcode_data = barcodes[0].data.decode("utf-8")
        return await barcode_scan(BarcodeRequest(barcode=barcode_data))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image barcode scan failed: {str(e)}")
