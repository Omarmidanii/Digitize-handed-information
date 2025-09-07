from io import BytesIO
from PIL import Image
from IPython.display import display
import os
import requests
import json
import difflib
API_URL = "https://backend.scandocflow.com/v1/api/documents/extract"
ACCESS_TOKEN = "hyPvO0RsNe0UaCfYJuEmXGkshmcmRrtCVZDFJSILVATIu5dHntBfoqCulC7WGhpd"
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
        {"region": "الاجمالي","similarity":0.0, "box": (0, 0, 0, 0)},
        {"region": "الطبيب","similarity":0.0, "box": (0, 0, 0, 0)},
        {"region": "المريض","similarity":0.0, "box": (0, 0, 0, 0)},
        {"region": "القيمة","similarity":0.0, "box": (0, 0, 0, 0)},
        {"region": "الافرادي","similarity":0.0, "box": (0, 0, 0, 0)},
        {"region": "الكمية","similarity":0.0, "box": (0, 0, 0, 0)},
        {"region": "المواصفات","similarity":0.0, "box": (0, 0, 0, 0)}
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
        {"region": "الاجمالي", "box": (-0.23717, -0.0168, -0.10708, 0.01492)},
        {"region": "الطبيب", "box": (-0.45221, -0.00742, -0.07035, 0.01875)},
        {"region": "المريض", "box": (-0.44424, -0.00078, -0.06991, 0.01875)}
    ]

    items=[
        [
          (-0.06814, 0.0168, 0.07257, 0.035)      #القيمة
          ,(-0.03805, 0.01406, 0.0385, 0.035)     #الافرادي
          ,(-0.01061, 0.01602, 0.01416, 0.035)    #الكمية
          ,(-0.25531, 0.0168, 0.32213, 0.035)     #المواصفات
        ],
        [
          (-0.06814, 0.04, 0.07257, 0.055)
          ,(-0.03805, 0.04, 0.0385, 0.055)
          ,(-0.01061, 0.04, 0.01416, 0.055)
          ,(-0.25531, 0.04, 0.32213, 0.055)
        ],
        [
          (-0.06814, 0.063, 0.07257, 0.078)
          ,(-0.03805, 0.063, 0.0385, 0.078)
          ,(-0.01061, 0.063, 0.01416, 0.078)
          ,(-0.25531, 0.063, 0.32213, 0.078)
        ],
        [
          (-0.06814, 0.088, 0.07257, 0.103)
          ,(-0.03805, 0.088, 0.0385, 0.103)
          ,(-0.01061, 0.088, 0.01416, 0.103)
          ,(-0.25531, 0.088, 0.32213, 0.103)
        ]
    ]
    width, height = image.size
    
    final_boxes = []  
    final_items=[]
     
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
    
    for i, item_row  in enumerate(items):
        final_items.append([])
        for j in range(4):
          x1, y1, x2, y2 = item_row [j]
          xx1, yy1, xx2, yy2 = main_regions[6+j]["box"]
          norm_box = (
              x1 + xx1,
              y1 + yy1,
              x2 + xx2,
              y2 + yy2
          )
          final_items[i].append( norm_box )
    
    
    #calculate offset for boxes
    offsetx = round(10 / width, 5)
    offsety = round(10 / height, 5)
    ocr_box_matching=[
        {"region": "رقم", "words":[]},
        {"region": "تاريخ", "words":[]},
        {"region": "السادة", "words":[]},
        {"region": "الاجمالي", "words":[]},
        {"region": "الطبيب", "words":[]},
        {"region": "المريض", "words":[]},
    ]

    names=[
        {"region": "القيمة"},
        {"region": "الافرادي"},
        {"region": "الكمية"},
        {"region": "المواصفات"}]

    ocr_items=[
        [[],[],[],[]],
        [[],[],[],[]],
        [[],[],[],[]],
        [[],[],[],[]]
    ]
    for i, word in enumerate(words):

        current_x1 = word['Outline'][0]+offsetx
        current_y1 = word['Outline'][1]+offsety
        current_x2 = word['Outline'][4]-offsetx
        current_y2 = word['Outline'][5]-offsety


        for j, box in enumerate(final_boxes):

            x1, y1, x2, y2 = box["box"]
            if x1< current_x1 and y1< current_y1 and x2> current_x2 and y2> current_y2 and word['Text']!='|':
                ocr_box_matching[j]["words"].append(i)
                
        for j, row_item in enumerate(final_items):
            for k in range(4):
              x1, y1, x2, y2 = row_item[k]
              if x1< current_x1 and y1< current_y1 and x2> current_x2 and y2> current_y2 and word['Text']!='|':
                ocr_items[j][k].append(i)
        
        
    for item in ocr_box_matching:
        region_name = item["region"]
        Cur_words = item["words"]
        print(f"📍 Region: {region_name} - words: ")
        for word in Cur_words:
            print(words[word]['Text'])
            
    for i, item in enumerate(ocr_items):
      for k in range(4):
        region_name = names[k]["region"]
        print(f"📍 item {i}: {region_name} - words: ")
        for word in item[k]:
          print(words[word]['Text'])
      
      
    finale_words=[
        {"region": "رقم", "words":""},
        {"region": "تاريخ", "words":""},
        {"region": "السادة", "words":""},
        {"region": "الاجمالي", "words":""},
        {"region": "الطبيب", "words":""},
        {"region": "المريض", "words":""}
    ]

    final_Iwords=[ 
                   ["","","",""]
                  ,["","","",""]
                  ,["","","",""]
                  ,["","","",""]
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

    for j, item in enumerate(ocr_items):
      for k in range(4):
        region_name = names[k]["region"]
        region_words = item[k]

        print(f"\n📍item {j} Region: {region_name}")
        print("🔢 Original word list:")
        for w in region_words:
            print(f"  - {words[w]['Text']} at x={words[w]['Outline'][0]}")

            # Decide sorting direction
        reverse_sort = region_name in ["المواصفات"]

        # Sort words by x-coordinate (left to right)
        sorted_words = sorted(region_words, key=lambda w: words[w]['Outline'][0], reverse=reverse_sort)
        for w in sorted_words:
            final_Iwords[j][k]=final_Iwords[j][k]+" "+(words[w]['Text'])
            print(f"  → {words[w]['Text']} at x={words[w]['Outline'][0]}")
        
    print(finale_words)
    
    final_response={
        'data':finale_words,
        'items':[]
    }

    for i, item in enumerate(final_Iwords):
        if item[0]=="" : continue
        curr_item={'القيمة':item[0], 'الافرادي':item[1], 'الكمية':item[2], 'المواصفات':item[3]}
        final_response['items'].append(curr_item)

    print(final_response)
    return {
            "finale_words": final_response
    }
    
