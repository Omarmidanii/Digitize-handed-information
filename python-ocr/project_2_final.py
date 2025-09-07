def startProcess(image_bytes: bytes):
    import easyocr
    import cv2
    import os
    import requests
    import json
    import numpy as np
    import unicodedata
    from pathlib import Path
    # --------OCR --------
    reader = easyocr.Reader(['ar'])

    image_array = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
    output_dir = "cropped_fields"
    os.makedirs(output_dir, exist_ok=True)
    result = reader.readtext(image)
    target_words_settings = {
        'القيمة': {'pad_x1': 140, 'pad_x2': 140, 'pad_y1': 20, 'pad_y2': 500},
        'السعر':  {'pad_x1': 110,  'pad_x2': 80, 'pad_y1': 20, 'pad_y2': 500},
        'البيان': {'pad_x1': 170,  'pad_x2': 170,  'pad_y1': 80, 'pad_y2': 500},
        'الصنف': {'pad_x1': 170,  'pad_x2': 170,  'pad_y1': 80, 'pad_y2': 500},
        'الكمية': {'pad_x1': 10,  'pad_x2': 10,  'pad_y1': 20, 'pad_y2': 300},
        'الإجمالي': {'pad_x1': 1300, 'pad_x2': 800, 'pad_y1': 30,  'pad_y2': 50},
        'الطبيب':   {'pad_x1': 1000, 'pad_x2': 100, 'pad_y1': 50,  'pad_y2': 40},
        'المريض':   {'pad_x1': 1300, 'pad_x2': 100, 'pad_y1': 30,  'pad_y2': 30},
        'ملاحظات': {'pad_x1': 2000, 'pad_x2': 100, 'pad_y1': 60,  'pad_y2': 60},
        'السادة':   {'pad_x1': 130,  'pad_x2': 330, 'pad_y1': 20,  'pad_y2': 120},
        'التاريخ':  {'pad_x1': 160,  'pad_x2': 150, 'pad_y1': 10,  'pad_y2': 120},
        'الفاتورة': {'pad_x1': 120,  'pad_x2': 100, 'pad_y1': 10,  'pad_y2': 120},
    }
    for (bbox, text, prob) in result:
        for word, pad in target_words_settings.items():
            if word in text:
                x1, y1 = map(int, bbox[0])  # top-left
                x2, y2 = map(int, bbox[2])  # bottom-right

                x1 = max(x1 - pad['pad_x1'], 0)
                y1 = max(y1 - pad['pad_y1'], 0)
                x2 = min(x2 + pad['pad_x2'], image.shape[1])
                y2 = min(y2 + pad['pad_y2'], image.shape[0])

                cropped = image[y1:y2, x1:x2]

                filename = unicodedata.normalize("NFC", f"{word}.jpg")
                save_path = Path(output_dir) / filename
                ok, enc = cv2.imencode(".jpg", cropped)
                if not ok:
                    raise RuntimeError("JPEG encode failed")
                save_path.write_bytes(enc.tobytes())
                print(filename)
                # save_path = os.path.join(output_dir, filename)
                # cv2.imwrite(save_path, cropped)
                print(f"Saved: {save_path}")
                break

    #***************************************************************************************************

    import os
    import requests
    import json

    # -------- ScanDocFlow --------
    API_URL = "https://backend.scandocflow.com/v1/api/documents/extract"
    ACCESS_TOKEN = "hyPvO0RsNe0UaCfYJuEmXGkshmcmRrtCVZDFJSILVATIu5dHntBfoqCulC7WGhpd"
    WEBHOOK_URL = ""

    folder_path = "cropped_fields"


    finale_words = {}

    for filename in os.listdir(folder_path):
        img_path = os.path.join(folder_path, filename)

        if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
            continue

        print(f"\n Sending file {filename} to ScanDocFlow...")

        with open(img_path, 'rb') as file_data:
            response = requests.post(
                f"{API_URL}?access_token={ACCESS_TOKEN}",
                files={'files': (filename, file_data, 'image/jpeg')},
                data={
                    'webhookUrl': WEBHOOK_URL,
                    'type': 'financial',
                    'lang': 'ara'
                }
            )

        if response.status_code == 200:
            response_json = response.json()

            try:
                doc = response_json['documents'][0]['textAnnotation']
                words = doc['Pages'][0]['Words']

                #  descending
                sorted_words = sorted(words, key=lambda w: w['Outline'][0], reverse=True)

                print(f"\n Sorted (RTL Arabic) word list for {filename}:")
                text_line = ""
                for w in sorted_words:
                    text_line += " " + w['Text']
                    print(f"  → {w['Text']} at x={w['Outline'][0]}")

                finale_words[filename] = {"words": text_line.strip()}

            except Exception as e:
                print(f"Couldn't parse words for {filename}: {e}")
                finale_words[filename] = {"words": ""}

        else:
            print(f" Error: Status {response.status_code}")
            print(response.text)
            finale_words[filename] = {"words": ""}


    final_json_path = "finale_words.json"
    with open(final_json_path, "w", encoding="utf-8") as f:
        json.dump(finale_words, f, ensure_ascii=False, indent=4)

    print(f"\n Final results saved to {final_json_path}")

    import json
    import pandas as pd
    import re
    import os
    from sentence_transformers import SentenceTransformer, util
    import torch
    from rapidfuzz import fuzz

    # -------------------- downloude model --------------------
    model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')

    # -------------------- downloude tables --------------------
    df_products2 = pd.read_excel("products2.xlsx")
    materials_raw = df_products2["Material Name"].dropna().astype(str).tolist()
    latins_raw    = df_products2["Latin Name"].dropna().astype(str).tolist()

    df_doctors = pd.read_excel("doctors.xlsx")
    doctors_raw = df_doctors["اسم الطبيب"].dropna().astype(str).tolist()

    df_clients = pd.read_excel("clients.xlsx")
    clients_raw = df_clients["اسم العميل"].dropna().astype(str).tolist()

    # -------------------- tools for arabic--------------------
    AR_DIAC = re.compile(r'[\u0617-\u061A\u064B-\u0652]')
    TATWEEL = '\u0640'

    def normalize_ar(s: str) -> str:
        if not isinstance(s, str):
            return ""
        s = s.strip()
        s = s.replace(TATWEEL, '')
        s = AR_DIAC.sub('', s)
        s = re.sub('[إأآا]', 'ا', s)
        s = s.replace('ى', 'ي').replace('ئ', 'ي').replace('ؤ', 'و')
        s = s.replace('ة', 'ه')
        s = re.sub(r'[^\w\s]', ' ', s)
        s = re.sub(r'\s+', ' ', s).strip()
        return s

    def strip_titles(s: str) -> str:
        s = re.sub(r'\b(د|د\.|دكتور|الدكتور|دكتوره|الدكتوره|الطبيب|طبيب)\b', ' ', s)
        return re.sub(r'\s+', ' ', s).strip()

    def remove_al(word: str) -> str:
        return re.sub(r'^(ال)', '', word)

    def split_name(s: str):

        toks = s.split()
        if not toks:
            return "", ""
        first = toks[0]
        last = toks[-1] if len(toks) > 1 else ""
        return first, last

    # cleaning doctors
    doctors_norm = [normalize_ar(strip_titles(d)) for d in doctors_raw]
    doctors_emb = model.encode(doctors_norm, convert_to_tensor=True)

    # -------------------- OCR --------------------
    with open("finale_words.json", "r", encoding="utf-8") as f:
        finale_words = json.load(f)

    # -------------------- Embeddings --------------------
    materials_norm = [normalize_ar(m) for m in materials_raw]
    latins_norm    = [normalize_ar(l) for l in latins_raw]

    materials_emb = model.encode(materials_norm, convert_to_tensor=True)
    latins_emb    = model.encode(latins_norm, convert_to_tensor=True)



    clients_norm = [normalize_ar(c) for c in clients_raw]
    clients_emb = model.encode(clients_norm, convert_to_tensor=True)

    # -------------------- extact numbers--------------------
    def extract_int_digits(text: str):
        if not isinstance(text, str):
            return None
        digits = re.sub(r'[^\d]', '', text)
        return int(digits) if digits else None

    # -------------------- compare doctor -------------------
    def best_doctor_match(query_text: str):

        q_clean = normalize_ar(strip_titles(query_text))
        if not q_clean:
            return None, 0.0

        q_first, q_last = split_name(q_clean)
        q_last_noal = remove_al(q_last)

        #first name
        cand_idx = [i for i, d in enumerate(doctors_norm) if q_first and q_first in d.split()]
        # last name
        if not cand_idx and q_last_noal:
            cand_idx = [i for i, d in enumerate(doctors_norm) if q_last_noal and remove_al(d.split()[-1] if d.split() else '') == q_last_noal]
        # first + last
        if not cand_idx:
            cand_idx = list(range(len(doctors_norm)))

        q_emb = model.encode(q_clean, convert_to_tensor=True)

        best_score = -1.0
        best_i = None

        for i in cand_idx:
            d = doctors_norm[i]
            toks = d.split()
            d_first = toks[0] if toks else ""
            d_last = toks[-1] if len(toks) > 1 else ""
            d_last_noal = remove_al(d_last)


            first_exact = 1.0 if q_first and d_first == q_first else 0.0
            last_exact  = 1.0 if q_last_noal and d_last_noal == q_last_noal else 0.0

            fuzz_score = fuzz.token_set_ratio(q_clean, d) / 100.0
            cos_score = util.cos_sim(q_emb, doctors_emb[i]).item()

            # best scour
            final_score = 1.2*first_exact + 1.0*last_exact + 0.5*fuzz_score + 0.3*cos_score

            if final_score > best_score:
                best_score = final_score
                best_i = i

        if best_i is None:
            return None, 0.0
        return doctors_raw[best_i], float(best_score)

    # -------------------- compare client -------------------
    def best_client_match(query_text: str):
        q_clean = normalize_ar(query_text)
        if not q_clean:
            return None, 0.0

        q_emb = model.encode(q_clean, convert_to_tensor=True)

        best_score = -1.0
        best_i = None

        for i, c in enumerate(clients_norm):
            fuzz_score = fuzz.token_set_ratio(q_clean, c) / 100.0
            cos_score = util.cos_sim(q_emb, clients_emb[i]).item()
            final_score = 0.6*fuzz_score + 0.4*cos_score

            if final_score > best_score:
                best_score = final_score
                best_i = i

        if best_i is None:
            return None, 0.0
        return clients_raw[best_i], float(best_score)





    #----------------------------------- best_product_match --------------------
    def best_product2_match(query_text: str):
        q_clean = normalize_ar(query_text)
        if not q_clean:
            return None, 0.0

        q_emb = model.encode(q_clean, convert_to_tensor=True)

        # --- search in Material Name ---
        best_score_m = -1.0
        best_i_m = None
        for i, m in enumerate(materials_norm):
            fuzz_score = fuzz.token_set_ratio(q_clean, m) / 100.0
            cos_score  = util.cos_sim(q_emb, materials_emb[i]).item()
            final_score = 0.6*fuzz_score + 0.4*cos_score
            if final_score > best_score_m:
                best_score_m = final_score
                best_i_m = i

        # --- search in Latin Name ---
        best_score_l = -1.0
        best_i_l = None
        for i, l in enumerate(latins_norm):
            fuzz_score = fuzz.token_set_ratio(q_clean, l) / 100.0
            cos_score  = util.cos_sim(q_emb, latins_emb[i]).item()
            final_score = 0.6*fuzz_score + 0.4*cos_score
            if final_score > best_score_l:
                best_score_l = final_score
                best_i_l = i

        # --- choose best between both ---
        if best_score_m >= best_score_l:
            return materials_raw[best_i_m], float(best_score_m)
        else:
            return latins_raw[best_i_l], float(best_score_l)
    #----------------------------------------------------------------------------


    final_results = {}
    for fname, content in finale_words.items():
        ocr_text = content.get("words", "")
        key = os.path.splitext(fname)[0]

        if key == "الطبيب":
            match, score = best_doctor_match(ocr_text)
            final_results[key] = {"ocr": ocr_text, "match": match, "score": score}

        elif key == "البيان":
            match, score = best_product2_match(ocr_text)
            final_results[key] = {"ocr": ocr_text, "match": match, "score": score}

        else:
            final_results[key] = {"ocr": ocr_text, "match": None, "score": None}

    import re
    from datetime import datetime


    def extract_int_digits(text: str):

        if not isinstance(text, str):
            return None
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    def extract_date(text: str):

        if not isinstance(text, str):
            return None
        m = re.search(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})', text)
        if not m:
            return None
        d, mth, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        try:
            return datetime(int(y), int(mth), int(d)).strftime("%d/%m/%Y")
        except:
            return None

    # -------------------- validation qty / value / total /--------------------
    qty_text   = finale_words.get("الكمية.jpg",   {}).get("words", "")
    value_text = finale_words.get("القيمة.jpg",   {}).get("words", "")
    total_text = finale_words.get("الإجمالي.jpg", {}).get("words", "")
    price_text = finale_words.get("السعر.jpg",   {}).get("words", "")

    qty   = extract_int_digits(qty_text)
    value = extract_int_digits(value_text)
    total = extract_int_digits(total_text)
    price = extract_int_digits(price_text)

    for k, txt in [("القيمة", value_text), ("الإجمالي", total_text), ("السعر", price_text)]:
        if k not in final_results:
            final_results[k] = {"ocr": txt, "match": None, "score": None}


    candidates = [v for v in [value, total, price] if v is not None]
    if candidates:
        bigger = max(candidates)

        final_results["القيمة"]["match"]   = bigger
        final_results["القيمة"]["score"]   = 1.0

        final_results["الإجمالي"]["match"] = bigger
        final_results["الإجمالي"]["score"] = 1.0

        final_results["السعر"]["match"]    = bigger
        final_results["السعر"]["score"]    = 1.0

    # الكمية دائماً = 1
    final_results["الكمية"] = {
        "ocr": qty_text,
        "match": 1,
        "score": 1.0
    }



    for key, content in final_results.items():
        ocr_text = content.get("ocr", "")

        if key == "الفاتورة":
            num = extract_int_digits(ocr_text)
            if num:
                final_results[key]["match"] = num

        elif key == "التاريخ":
            date_val = extract_date(ocr_text)
            if date_val:
                final_results[key]["match"] = date_val

        elif key == "السادة":
            match, score = best_client_match(ocr_text)
            final_results[key] = {"ocr": ocr_text, "match": match, "score": score}


        elif key == "المريض":
            if ocr_text.strip():
                final_results[key]["match"] = ocr_text.replace("المريض", "").strip()

        elif key == "الكمية":
            qty_val = 1
            final_results[key]["match"] = qty_val


    for needed in ["الفاتورة","التاريخ","البيان","الصنف","السعر","القيمة","الإجمالي","الطبيب","المريض","الكمية","ملاحظات"]:
        if needed not in final_results:
            final_results[needed] = {"ocr": "", "match": None, "score": None}


    out_path = "final_db_ready.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)

    print(" Final JSON saved to:", out_path)

    import json
    import pandas as pd
    import re
    import os



    # -------------------- downloude tables --------------------
    df_products2 = pd.read_excel("products2.xlsx")
    materials_raw = df_products2["Material Name"].dropna().astype(str).tolist()
    latins_raw    = df_products2["Latin Name"].dropna().astype(str).tolist()

    df_doctors = pd.read_excel("doctors.xlsx")
    doctors_raw = df_doctors["اسم الطبيب"].dropna().astype(str).tolist()

    df_clients = pd.read_excel("clients.xlsx")
    clients_raw = df_clients["اسم العميل"].dropna().astype(str).tolist()



    # -------------------- OCR --------------------
    with open("finale_words.json", "r", encoding="utf-8") as f:
        finale_words = json.load(f)


    # -------------------- extact numbers--------------------
    def extract_int_digits(text: str):
        if not isinstance(text, str):
            return None
        digits = re.sub(r'[^\d]', '', text)
        return int(digits) if digits else None



    # -------------------- N-gram Similarity function --------------------
    def ngram_similarity(s1, s2, n=2):
        def get_ngrams(text, n):
            text = text.lower()
            return set([text[i:i+n] for i in range(len(text)-n+1)])

        ngrams1 = get_ngrams(s1, n)
        ngrams2 = get_ngrams(s2, n)
        if not ngrams1 or not ngrams2:
            return 0.0
        intersection = ngrams1 & ngrams2
        union = ngrams1 | ngrams2
        return len(intersection) / len(union)

    # -------------------- compare doctor -------------------
    def best_doctor_match(text):
        best_score = 0
        best_match = None
        for doc in doctors_raw:
            score = ngram_similarity(text, doc, n=2)
            if score > best_score:
                best_score = score
                best_match = doc
        return best_match, best_score

    # -------------------- compare client -------------------
    def best_client_match(text):
        best_score = 0
        best_match = None
        for client in clients_raw:
            score = ngram_similarity(text, client, n=2)
            if score > best_score:
                best_score = score
                best_match = client
        return best_match, best_score

    # -------------------- best_product_match --------------------
    def best_product2_match(text):
        best_score = 0
        best_match = None
        for mat, lat in zip(materials_raw, latins_raw):
            score_ar = ngram_similarity(text, mat, n=2)
            score_lat = ngram_similarity(text, lat, n=2)
            score = max(score_ar, score_lat)
            if score > best_score:
                best_score = score
                best_match = mat
        return best_match, best_score


    #----------------------------------------------------------------------------


    final_results = {}
    for fname, content in finale_words.items():
        ocr_text = content.get("words", "")
        key = os.path.splitext(fname)[0]

        if key == "الطبيب":
            match, score = best_doctor_match(ocr_text)
            final_results[key] = {"ocr": ocr_text, "match": match, "score": score}

        elif key == "البيان":
            match, score = best_product2_match(ocr_text)
            final_results[key] = {"ocr": ocr_text, "match": match, "score": score}

        else:
            final_results[key] = {"ocr": ocr_text, "match": None, "score": None}

    import re
    from datetime import datetime


    def extract_int_digits(text: str):

        if not isinstance(text, str):
            return None
        digits = re.sub(r"[^\d]", "", text)
        return int(digits) if digits else None

    def extract_date(text: str):

        if not isinstance(text, str):
            return None
        m = re.search(r'(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{2,4})', text)
        if not m:
            return None
        d, mth, y = m.groups()
        if len(y) == 2:
            y = "20" + y
        try:
            return datetime(int(y), int(mth), int(d)).strftime("%d/%m/%Y")
        except:
            return None

    # -------------------- validation qty / value / total /--------------------
    qty_text   = finale_words.get("الكمية.jpg",   {}).get("words", "")
    value_text = finale_words.get("القيمة.jpg",   {}).get("words", "")
    total_text = finale_words.get("الإجمالي.jpg", {}).get("words", "")
    price_text = finale_words.get("السعر.jpg",   {}).get("words", "")

    qty   = extract_int_digits(qty_text)
    value = extract_int_digits(value_text)
    total = extract_int_digits(total_text)
    price = extract_int_digits(price_text)


    for k, txt in [("القيمة", value_text), ("الإجمالي", total_text), ("السعر", price_text)]:
        if k not in final_results:
            final_results[k] = {"ocr": txt, "match": None, "score": None}


    if price:
        final_results["السعر"]["match"] = price
        final_results["السعر"]["score"] = None

    if value and total:
        if value != total:
            bigger = max(value, total)
            final_results["القيمة"]["match"] = bigger
            final_results["الإجمالي"]["match"] = bigger
            final_results["القيمة"]["score"] = 1.0
            final_results["الإجمالي"]["score"] = 1.0
        else:
            final_results["القيمة"]["match"] = value
            final_results["الإجمالي"]["match"] = total
            final_results["القيمة"]["score"] = 1.0
            final_results["الإجمالي"]["score"] = 1.0


    if qty and value:
        computed_total = qty * value
        if total != computed_total:
            final_results["الإجمالي"]["match"] = computed_total
            final_results["الإجمالي"]["score"] = 1.0


    for key, content in final_results.items():
        ocr_text = content.get("ocr", "")

        if key == "الفاتورة":
            num = extract_int_digits(ocr_text)
            if num:
                final_results[key]["match"] = num

        elif key == "التاريخ":
            date_val = extract_date(ocr_text)
            if date_val:
                final_results[key]["match"] = date_val

        elif key == "السادة":
            match, score = best_client_match(ocr_text)
            final_results[key] = {"ocr": ocr_text, "match": match, "score": score}


        elif key == "المريض":
            if ocr_text.strip():
                final_results[key]["match"] = ocr_text.replace("المريض", "").strip()

        elif key == "الكمية":
            qty_val = extract_int_digits(ocr_text)
            if qty_val is None:
                qty_val = 1
            final_results[key]["match"] = qty_val


    for needed in ["الفاتورة","التاريخ","البيان","الصنف","السعر","القيمة","الإجمالي","الطبيب","المريض","الكمية","ملاحظات"]:
        if needed not in final_results:
            final_results[needed] = {"ocr": "", "match": None, "score": None}


    out_path = "final_db_ready.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_results, f, ensure_ascii=False, indent=4)

    print(" Final JSON saved to:", out_path)
    folder = Path(output_dir)
    for file in folder.iterdir():
        if file.is_file():
            file.unlink()




import json
from typing import Any, Dict, List
import re
from itertools import zip_longest

def build_final_words(json_path: str) -> Dict[str, Any]:
    """
    Load the JSON at `json_path` and produce:

    {
      "final_words": {
        "data":  [ {"ragion": <field>, "words": <value>}, ... ],   # all fields except items_set
        "items": [ {<field>: <value>}, ... ]                        # only fields in items_set
      }
    }

    Selection rule:
      if score > 0.5 and match is not None/empty -> use match
      else -> use ocr (fallback to match if ocr missing)
    """
    with open(json_path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    # Fields that go under "items"
    # NOTE: 'الصنف' (source) becomes 'المواصفات' (output) per your requirement
    items_set = {"القيمة", "السعر", "الكمية", "الصنف"}

    def choose_value(entry: Dict[str, Any]) -> Any:
        score = entry.get("score")
        match = entry.get("match")
        ocr = entry.get("ocr")

        is_high = isinstance(score, (int, float)) and score > 0.5
        if is_high and match not in (None, ""):
            return match
        # Prefer OCR otherwise; if OCR missing/empty, fall back to match; else empty string
        return ocr if ocr not in (None, "") else (match if match not in (None, "") else "")

    # Select a single value for every field up-front (preserves JSON order on 3.7+)
    selected: Dict[str, Any] = {
        field: choose_value(entry if isinstance(entry, dict) else {})
        for field, entry in payload.items()
    }

    # ---- NEW: build the "items" rows (each row has the four fields together)
    def _to_list(v: Any) -> List[str]:
        """Normalize to list of strings; split on newline/pipe/Arabic semicolon (not comma)."""
        if v is None:
            return []
        if isinstance(v, (list, tuple)):
            return [str(x).strip() for x in v if str(x).strip() != ""]
        s = str(v).strip()
        if not s:
            return []
        parts = re.split(r"[|\n\r؛]+", s)
        return [p.strip() for p in parts if p.strip()]

    values  = _to_list(selected.get("القيمة"))     # goes to "القيمة"
    prices  = _to_list(selected.get("السعر"))       # becomes "الافرادي"
    qtys    = _to_list(selected.get("الكمية"))      # goes to "الكمية"
    specs   = _to_list(selected.get("الصنف"))       # becomes "المواصفات"

    # If no explicit unit prices, derive them from "القيمة" (simple fallback)
    if not prices and values:
        prices = values[:]

    items: List[Dict[str, Any]] = []
    # zip_longest so uneven column lengths won't crash; empty strings if missing
    for v, p, q, s in zip_longest(values, prices, qtys, specs, fillvalue=""):
        row = {
            "القيمة":     v or "",
            "الافرادي":   p or "",
            "الكمية":     q or "",
            "المواصفات":  s or "",
        }
        # skip a fully empty row
        if any(str(val).strip() for val in row.values()):
            items.append(row)

    # ---- Build "data" for everything NOT in items_set (same as before)
    data: List[Dict[str, Any]] = []
    for field, entry in payload.items():
        if field in items_set:
            continue
        value = selected.get(field, "")
        data.append({"region": field, "words": value})

    return {"finale_words": {"data": data, "items": items}}




if __name__ == "__main__":
    print(build_final_words("final_db_ready.json"))