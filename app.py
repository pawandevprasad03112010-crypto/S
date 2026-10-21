import os
import zipfile
import io
import json
import uuid
import asyncio
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import boto3
from fastapi import FastAPI, UploadFile, File, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# आपके डायनेमोडीबी क्रेडेंशियल्स
AWS_ACCESS_KEY_ID = "AKIA32VVAONMQV5QKNED"
AWS_SECRET_ACCESS_KEY = "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"
REGION = "ap-south-1"
TABLE_NAME = "LARGE_PROPERTY_LISTING"
PRIMARY_KEY = "property_id"

executor = ThreadPoolExecutor(max_workers=5) # सुरक्षित स्पीड ताकि AWS थ्रॉटल न करे

def clean_and_convert_data(obj):
    """ डेटा को DynamoDB के अनुकूल बनाने का फंक्शन """
    if isinstance(obj, list):
        return [clean_and_convert_data(v) for v in obj if v is not None]
    elif isinstance(obj, dict):
        return {str(k): clean_and_convert_data(v) for k, v in obj.items() if v is not None and v != ""}
    elif isinstance(obj, float):
        return Decimal(str(obj))
    elif isinstance(obj, int):
        return int(obj)
    else:
        return str(obj) if isinstance(obj, str) else obj

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/parse-zip")
async def parse_zip(zippfile: UploadFile = File(...)):
    contents = await zippfile.read()
    listings = []

    try:
        with zipfile.ZipFile(io.BytesIO(contents), 'r') as z:
            for filename in z.namelist():
                if filename.endswith('.json') and not filename.startswith('__MACOSX'):
                    file_bytes = z.read(filename)
                    try:
                        data = json.loads(file_bytes.decode('utf-8'))
                        
                        # प्रॉपर्टी आईडी ढूँढना या फ़ाइल नाम से बनाना
                        prop_id = data.get(PRIMARY_KEY)
                        if not prop_id:
                            prop_id = filename.split('_')[1].split('.')[0] if '_' in filename else str(uuid.uuid4())
                            data[PRIMARY_KEY] = str(prop_id)
                        else:
                            data[PRIMARY_KEY] = str(prop_id)

                        # डेटा को पूरी तरह साफ़ करना
                        cleaned_data = clean_and_convert_data(data)

                        listings.append({
                            "filename": filename,
                            "property_id": str(prop_id),
                            "data": cleaned_data
                        })
                    except Exception as e:
                        print(f"Error parsing {filename}: {e}")
    except Exception as ex:
        raise HTTPException(status_code=400, detail=f"Invalid ZIP file: {str(ex)}")

    return {"total": len(listings), "listings": listings}

@app.post("/upload-dynamodb")
async def upload_dynamodb(payload: dict):
    listings = payload.get("listings", [])
    if not listings:
        raise HTTPException(status_code=400, detail="No listings found to upload.")

    try:
        dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=REGION
        )
        table = dynamodb.Table(TABLE_NAME)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"DynamoDB connection failed: {str(e)}")

    saved_ids = []

    def save_item(item_info):
        try:
            # हर एक JSON लिस्टिंग को अलग-अलग डेटाबेस में पुट करना
            table.put_item(Item=item_info["data"])
            return item_info["property_id"]
        except Exception as ex:
            print(f"Failed to save {item_info['filename']}: {str(ex)}")
            return None

    # एक साथ सारे भेजने के बजाय छोटे-छोटे चंक्स (Batches) में भेजना ताकि बोटो3 एरर न दे
    chunk_size = 10 
    for i in range(0, len(listings), chunk_size):
        chunk = listings[i:i + chunk_size]
        loop = asyncio.get_running_loop()
        tasks = [loop.run_in_executor(executor, save_item, item) for item in chunk]
        results = await asyncio.gather(*tasks)
        
        for pid in results:
            if pid:
                saved_ids.append(pid)
        
        # छोटे बैच के बीच हल्का सा विराम ताकि AWS थ्रॉटलिंग से बचे
        await asyncio.sleep(0.2)

    return {
        "message": f"सफलतापूर्वक {len(saved_ids)} लिस्टिंग DynamoDB टेबल '{TABLE_NAME}' में अलग-अलग सेव हो गई हैं!",
        "saved_ids": saved_ids
    }
    
