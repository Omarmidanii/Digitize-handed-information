from io import BytesIO
from PIL import Image
from IPython.display import display
import os
import requests
import json
import difflib
API_URL = "https://backend.scandocflow.com/v1/api/documents/extract"
ACCESS_TOKEN = "TzsWvvv3c4p9tj8EBYpeyPc3w2ANMGKpAklAklIWRfQcAb8JqW4OkFR3920D4si2"
WEBHOOK_URL = ""

def string_similarity(word1, word2):
    return difflib.SequenceMatcher(None, word1, word2).ratio()

def analyze(image_bytes: bytes,filename: str = None):
    print(f"Sending file to ScanDocFlow...")
    response = requests.post(
        f"{API_URL}?access_token={ACCESS_TOKEN}",
        files={'files': (filename, image_bytes, 'image/jpeg')},
        data={
            'webhookUrl': WEBHOOK_URL,
            'type': 'financial',
            'lang': 'ara'
        }
    )
    if response.status_code == 200:
        print("Response:")
        print(response.json())
        response_json=response.json()
    else:
        print("Error: Status {response.status_code}")
        print(response.text)
    doc = response_json['documents'][0]['textAnnotation']
    words = doc['Pages'][0]['Words']
    main_regions=[
    {"region": "رقم","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "التاريخ","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "السادة","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "القيمة","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "الافرادي","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "الكمية","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "المواصفات","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "الاجمالي","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "الطبيب","similarity":0.0, "box": (0, 0, 0, 0)},
    {"region": "المريض","similarity":0.0, "box": (0, 0, 0, 0)}
    ]
    for region in main_regions:
            best_similarity = 0.0
            best_box = None

            for word in words:
                similarity = string_similarity(region["region"],word["Text"])

                if similarity > best_similarity and similarity >= 0.5:
                    best_similarity = similarity
                    best_word = word["Text"]
                    best_box = (word['Outline'][0], word['Outline'][1], word['Outline'][4], word['Outline'][5])

            # Update region with best match
            region["similarity"] = best_similarity
            region["box"] = best_box


    print(main_regions)
    
    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    
    # Define all crop boxes
    crop_boxes = [
    {"region": "رقم", "box": (-0.22035,-0.01094, -0.0681, 0.00547)},
    {"region": "التاريخ", "box": (-0.20973, -0.00742, -0.07611, 0.00898)},
    {"region": "السادة", "box": (-0.4823, -0.0082, -0.05708, 0.01367)},
    {"region": "القيمة", "box": (-0.06814, 0.0168, 0.07257, 0.05352)},
    {"region": "الافرادي", "box": (-0.03805, 0.01406, 0.0385, 0.05078)},
    {"region": "الكمية", "box": (-0.01061, 0.01602, 0.01416, 0.05235)},
    {"region": "المواصفات", "box": (-0.25531, 0.0168, 0.32213, 0.05469)},
    {"region": "الاجمالي", "box": (-0.23717, -0.0168, -0.10708, 0.01992)},
    {"region": "الطبيب", "box": (-0.45221, -0.00742, -0.07035, 0.01875)},
    {"region": "المريض", "box": (-0.44424, -0.00078, -0.06991, 0.01875)}
    ]
    width, height = image.size
    final_boxes = []   
    for i,item in enumerate(crop_boxes):
        x1, y1, x2, y2 = item["box"]
        xx1, yy1, xx2, yy2 = main_regions[i]["box"]
        norm_box = (
            x1 + xx1,
            y1 + yy1,
            x2 + xx2,
            y2 + yy2
        )
        final_boxes.append({
            "region": item["region"],
            "box": norm_box
        })
    pixel_boxes = []
    for item in final_boxes:
        x1, y1, x2, y2 = item["box"]
        pixel_box = (
            int(x1 * width),
            int(y1 * height),
            int(x2 * width),
            int(y2 * height)
        )
        pixel_boxes.append({
            "region": item["region"],
            "pixel_box": pixel_box
        })
    #calculate offset for boxes
    offsetx = round(10 / width, 5)
    offsety = round(10 / height, 5)
    ocr_box_matching=[
    {"region": "رقم", "words":[]},
    {"region": "تاريخ", "words":[]},
    {"region": "السادة", "words":[]},
    {"region": "القيمة", "words":[]},
    {"region": "الافرادي", "words":[]},
    {"region": "الكمية", "words":[]},
    {"region": "المواصفات", "words":[]},
    {"region": "الاجمالي", "words":[]},
    {"region": "الطبيب", "words":[]},
    {"region": "المريض", "words":[]}
    ]
    for i, word in enumerate(words):

        current_x1 = word['Outline'][0]+offsetx
        current_y1 = word['Outline'][1]+offsety
        current_x2 = word['Outline'][4]-offsetx
        current_y2 = word['Outline'][5]-offsety


        for j, box in enumerate(final_boxes):

            x1, y1, x2, y2 = box["box"]
            if x1< current_x1 and y1< current_y1 and x2> current_x2 and y2> current_y2:
                ocr_box_matching[j]["words"].append(i)
    for item in ocr_box_matching:
        region_name = item["region"]
        Cur_words = item["words"]
        print(f"📍 Region: {region_name} - words: ")
        for word in Cur_words:
            print(words[word]['Text'])
    finale_words=[
    {"region": "رقم", "words":""},
    {"region": "تاريخ", "words":""},
    {"region": "السادة", "words":""},
    {"region": "القيمة", "words":""},
    {"region": "الافرادي", "words":""},
    {"region": "الكمية", "words":""},
    {"region": "المواصفات", "words":""},
    {"region": "الاجمالي", "words":""},
    {"region": "الطبيب", "words":""},
    {"region": "المريض", "words":""}
    ]
    i=0
    for item in ocr_box_matching:
        region_name = item["region"]
        region_words = item["words"]

        print(f"\n📍 Region: {region_name}")
        print("🔢 Original word list:")
        for w in region_words:
            print(f"  - {words[w]['Text']} at x={words[w]['Outline'][0]}")

        # Decide sorting direction
        reverse_sort = region_name in ["الطبيب", "المريض", "السادة"]

        # Sort words by x-coordinate (left to right)
        sorted_words = sorted(region_words, key=lambda w: words[w]['Outline'][0], reverse=reverse_sort)

        print("📐 Sorted word list (left to right):")
        for w in sorted_words:
            finale_words[i]["words"]=finale_words[i]["words"]+" "+(words[w]['Text'])
            print(f"  → {words[w]['Text']} at x={words[w]['Outline'][0]}")
        i+=1

    print(finale_words)
    return {
            "finale_words": finale_words
    }
    
