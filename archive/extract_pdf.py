# pip install pypdf
import re
from pypdf import PdfReader
# pip install pdf2image pytesseract opencv-python pillow
# And install Tesseract on your OS (e.g., brew install tesseract, apt-get install tesseract-ocr)
from pdf2image import convert_from_path
import pytesseract, cv2, numpy as np
import os
from PIL import Image
from constants.checkbox_map import checkbox_map
from constants.columns import row
from helpers.iso import parse_date_to_iso


pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SPLIT_RULES = [

    {"key": "name", "start": "Name:", "end": "Team:"},
    {"key": "team", "start": "Team:", "end": "Code no:"},
    {"key": "code", "start": "Code no:", "end": "\n"},
    {"key": "injury_date", "start": "Date of injury:", "end": "Date of return"},
    {"key": "return_date", "start": " Date of return to full participation: ", "end": " (Send"},
    {"key": "other_injury", "start": "Other injury (please specify):", "end": "\n"},
    {"key": "match", "start": "Match", "end": "(min. of injury)"},
    {"key": "injury_mechanism", "start": "Injury mechanism/player action (describe in words):", "end": "\n"},
    {"key": "re_injury", "start": "Yes (give date of return from previous injury):", "end": "\n"},
    {"key": "other_diagnostic_examination", "start": "Other (specify):", "end": "\n"},
    {"key": "diagnosis", "start": "Diagnosis (specify results of examination): ", "end": "\n"},
    {"key": "oral_contraceptives", "start": "Yes (specify):", "end": "\nPlay"},
    {"key": "hormonal_contraceptives", "start": "other hormonal contraceptives?  No  Yes (specify): ", "end": "\nOther"},
    {"key": "other_comments", "start": "Other comments:", "end": "\n"},
]

def get_text_info(pdf_path: str) -> dict:
    reader = PdfReader(pdf_path)
    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)
    out = {}


    for rule in SPLIT_RULES:
        start_pat = rule["start"]
        end_pat = rule["end"]

        # Find absolute start index
        abs_start = full_text.find(start_pat)
        if abs_start == -1:
            out[rule["key"]] = ""
            continue

        # Start searching right after the start pattern
        cursor = abs_start + len(start_pat)
        remainder = full_text[cursor:]

        if end_pat == "\n":
            # Capture only until the very next newline
            nl_idx = remainder.find("\n")
            if nl_idx == -1:
                value = remainder.strip()
            else:
                value = remainder[:nl_idx].strip()
        else:
            # Capture across lines until the exact end token
            end_idx = remainder.find(end_pat)
            if end_idx == -1:
                value = ""
            else:
                value = remainder[:end_idx].strip()

        out[rule["key"]] = value.strip()

    return out





def pdf_to_images(pdf_path: str, dpi=300):
    pages = convert_from_path(pdf_path, dpi=dpi)
    return [np.array(p) for p in pages]  # RGB arrays

def detect_checkboxes(img, use_hierarchy=False):
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    bw = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                               cv2.THRESH_BINARY_INV, 31, 10)

    mode = cv2.RETR_TREE if use_hierarchy else cv2.RETR_EXTERNAL
    cnts, hierarchy = cv2.findContours(bw, mode, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for i, c in enumerate(cnts):
        x,y,w,h = cv2.boundingRect(c)
        if w == 0 or h == 0:
            continue
        aspect_ratio = w/float(h)
        # Stricter size and aspect to ignore small round letters
        if not (20 <= w <= 60 and 20 <= h <= 60 and 0.92 <= aspect_ratio <= 1.08):
            continue


        # polygonal approximation to prefer rectangular shapes
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.03*peri, True)
        # Allow 4-6 vertices, but prefer convex quads; relax to avoid missing noisy boxes
        if len(approx) < 4 or len(approx) > 6 or not cv2.isContourConvex(approx):
            continue

        # Check that all angles are near 90 degrees
        def angle_cosine(p0, p1, p2):
            v1 = p0 - p1
            v2 = p2 - p1
            num = float(v1.dot(v2))
            den = (np.linalg.norm(v1) * np.linalg.norm(v2)) or 1.0
            return abs(num/den)

        pts = approx.reshape(-1, 2).astype(np.float32)
        # order points consistently via their centroid for stability
        cX = np.mean(pts[:,0])
        cY = np.mean(pts[:,1])
        pts_ordered = sorted(pts, key=lambda p: (np.arctan2(p[1]-cY, p[0]-cX)))
        cosines = [angle_cosine(np.array(pts_ordered[(i-1)%4]), np.array(pts_ordered[i]), np.array(pts_ordered[(i+1)%4])) for i in range(4)]
        # cos(90°) ~ 0; allow tolerance
        if not all(cos <= 0.35 for cos in cosines):
            continue


        # Measure fill ratio excluding a small border to avoid counting the outline
        roi = bw[y:y+h, x:x+w]
        border = max(1, min(w, h)//7)
        inner = roi[border:h-border, border:w-border] if (h-2*border) > 0 and (w-2*border) > 0 else roi
        fill = inner.mean()/255.0  # 0..1

        boxes.append({"bbox": (x,y,w,h), "fill_ratio": fill})

    # Heuristic: filled if inside mean > threshold
    for b in boxes:
        b["checked"] = b["fill_ratio"] > 0.25

    return boxes

def number_boxes_reading_order(boxes, row_merge_px=25):
    # Assign a reading-order number to each box: left-to-right within rows, rows top-to-bottom
    if not boxes:
        return boxes
    # Prepare centers for stable grouping
    enriched = []
    for b in boxes:
        x,y,w,h = b["bbox"]
        cx = x + w // 2
        cy = y + h // 2
        enriched.append((cy, cx, x, b))
    # Sort by y, then x
    enriched.sort(key=lambda t: (t[0], t[1]))
    # Group into rows using row_merge_px threshold on y center
    rows = []
    for cy, cx, x, b in enriched:
        if not rows:
            rows.append([(cx, x, b, cy)])
            continue
        last_row = rows[-1]
        # Compare with the first element's cy in the current row for stability
        ref_cy = last_row[0][3]
        if abs(cy - ref_cy) <= row_merge_px:
            last_row.append((cx, x, b, cy))
        else:
            rows.append([(cx, x, b, cy)])
    # Within each row, sort by x (use cx/x)
    ordered = []
    for row in rows:
        row.sort(key=lambda t: (t[0], t[1]))
        ordered.extend([t[2] for t in row])
    
    ordered_copy = ordered.copy()
    
    # This is done to have the same order as in the word extraction
    swap_map = {
        80: 81,
        81: 80,
        84: 86,
        85: 84,
        86: 87,
        87: 85,
    }

    for dst_idx, src_idx in swap_map.items():
        ordered[dst_idx] = ordered_copy[src_idx]


    # Assign numbers 1..N in order
    for idx, b in enumerate(ordered, start=1):
        b["number"] = idx

    
    return boxes



def save_debug_visualization_with_labels(img, boxes, out_path):
    vis = img.copy()
    for b in boxes:
        x,y,w,h = b["bbox"]
        color = (0,255,0) if b.get("checked") else (0,0,255)
        cv2.rectangle(vis, (x,y), (x+w, y+h), color, 2)
        # Place the assigned number above the box (or inside if too close to top)
        number_text = str(b.get("number")) if b.get("number") is not None else ""
        if number_text:
            text_org = (x, max(0, y-5))
            cv2.putText(vis, number_text, text_org, cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2, cv2.LINE_AA)
    cv2.imwrite(out_path, cv2.cvtColor(vis, cv2.COLOR_RGB2BGR))



def get_checkbox_info(pdf_path: str, save_debug=True, debug_dir="debug"):
    imgs = pdf_to_images(pdf_path)
    box_map = {}
    if save_debug:
        os.makedirs(debug_dir, exist_ok=True)
    for idx, img in enumerate(imgs):
        boxes = detect_checkboxes(img, use_hierarchy=False)
        # Validate expected checkbox count
        if len(boxes) != 96:
            print(f"Page {idx+1}: Expected 96 boxes, found {len(boxes)}. Returning empty result.")
            return {}
        # Number boxes in reading order
        number_boxes_reading_order(boxes)
        if save_debug:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            out_labeled = os.path.join(debug_dir, f"{base_name}.png")
            save_debug_visualization_with_labels(img, boxes, out_labeled)
            # Save intermediates for tuning
            # Recompute the intermediates used in detection for export
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            blur = cv2.GaussianBlur(gray, (3,3), 0)
            bw = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 31, 10)
            open_k = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    
            cv2.imwrite(os.path.join(debug_dir, f"page_{idx+1}_bw.png"), bw)
   
        # Stop assigning textual labels; rely on numeric ordering instead
        assigns = []
        #Delete the fill_ratio from the boxes
        for box in boxes:
            box_map[str(box["number"])] = box["checked"]
        
    return box_map


def extract_info_from_pdf(pdf_path):
    injury_data = row.copy()

    checkboxes = get_checkbox_info(pdf_path)

    text_info = get_text_info(pdf_path)

    injury_data["NAME"] = text_info["name"]
    injury_data["TEAM"] = text_info["team"]
    injury_data["CODE"] = text_info["code"]


    try:
        injury_iso = parse_date_to_iso(text_info["injury_date"])
        injury_data['INJURY_DATE'] = injury_iso
    except Exception as e:
        injury_data['INJURY_DATE'] = "Wrong date format"

    try:
        return_iso = parse_date_to_iso(text_info["return_date"])
        injury_data['RETURN_DATE'] = return_iso
    except Exception as e:
        injury_data['RETURN_DATE'] = "Wrong date format"


    get_checkbox_array = lambda start, end: [checkbox_map[str(i)] for i in range(start, end) if checkboxes[str(i)]]


    #INJURY_LOCATION
    locations = get_checkbox_array(1, 20)
    injury_data["INJURY_LOCATION"] = ", ".join(locations)

    #INJURY_SIDE
    sides = get_checkbox_array(20, 23)
    injury_data["INJURY_SIDE"] = ", ".join(sides)

    #INJURY_TYPE
    injury_types = get_checkbox_array(23, 41)
    if checkboxes[str(41)]:
        if text_info["other_injury"] != "":
            injury_types.append(text_info["other_injury"])
        else:
            injury_types.append("Other injury")
    injury_data["INJURY_TYPE"] = ", ".join(injury_types)

    #OCCURRENCE
    #add other injury type
    occurrences = []
    for i in range(42, 55):
        if checkboxes[str(i)]:
            if i == 43:
                if text_info["match"] != "":
                    occurrences.append("Match (min. of injury: " + text_info["match"] + ")")
                else:
                    occurrences.append("Match")
            else:
                occurrences.append(checkbox_map[str(i)])

    injury_data["OCCURRENCE"] = ", ".join(occurrences)


    #OVERUSE_TRAUMA
    overuse_trauma = get_checkbox_array(55, 57)
    if len(overuse_trauma) == 1:
        injury_data["OVERUSE_TRAUMA"] = overuse_trauma[0]
    elif len(overuse_trauma) > 1:
        injury_data["OVERUSE_TRAUMA"] = "Too many answers"

    #ONSET
    onset = get_checkbox_array(57, 59)
    if len(onset) == 1:
        injury_data["ONSET"] = onset[0]
    elif len(onset) > 1:
        injury_data["ONSET"] = "Too many answers"

    #CONTACT
    contact = get_checkbox_array(59, 62)
    if len(contact) == 1:
        injury_data["CONTACT"] = contact[0]
    elif len(contact) > 1:
        injury_data["CONTACT"] = "Too many answers"

    #ACTION
    action = get_checkbox_array(62, 77)
    injury_data["ACTION"] = ", ".join(action)

    #ACTION_DESCRIPTION
    injury_data["ACTION_DESCRIPTION"] = text_info["injury_mechanism"]

    #RE_INJURY
    re_injury = get_checkbox_array(77, 79)
    if len(re_injury) == 1:
        if "Yes" in re_injury[0]:
            if text_info["re_injury"] != "":
                injury_data["RE_INJURY"] = "Yes, " + text_info["re_injury"]
            else:
                injury_data["RE_INJURY"] = "Yes"
        else:
            injury_data["RE_INJURY"] = "No"
    elif len(re_injury) > 1:
        injury_data["RE_INJURY"] = "Too many answers"

    #REFEREE_SANCTION
    referee_sanction = get_checkbox_array(79, 84)
    injury_data["REFEREE_SANCTION"] = ", ".join(referee_sanction)

    #DIAGNOSTIC_EXAMINATION
    diagnostic_examination = get_checkbox_array(84, 89)
    if "Other (specify)" in diagnostic_examination:
        if text_info["other_diagnostic_examination"] != "":
            diagnostic_examination.append(text_info["other_diagnostic_examination"])
        else:
            diagnostic_examination.append("Other")

        diagnostic_examination.remove("Other (specify)")

    injury_data["DIAGNOSTIC_EXAMINATION"] = ", ".join(diagnostic_examination)

    #DIAGNOSIS
    injury_data["DIAGNOSIS"] = text_info["diagnosis"]

    #SURGERY
    surgery = get_checkbox_array(89, 91)
    if len(surgery) == 1:
        injury_data["SURGERY"] = surgery[0]
    elif len(surgery) > 1:
        injury_data["SURGERY"] = "Too many answers"

    #MENSTRUAL_PHASE
    menstrual_phase = get_checkbox_array(91, 93)
    if len(menstrual_phase) == 1:
        injury_data["MENSTRUAL_PHASE"] = menstrual_phase[0]
    elif len(menstrual_phase) > 1:
        injury_data["MENSTRUAL_PHASE"] = "Too many answers"

    #ORAL_CONTRACEPTIVES
    oral_contraceptives = get_checkbox_array(93, 95)
    if len(oral_contraceptives) == 1:
        if "Yes" in oral_contraceptives[0]:
            if text_info["oral_contraceptives"] != "":
                injury_data["ORAL_CONTRACEPTIVES"] = "Yes, " + text_info["oral_contraceptives"]
            else:
                injury_data["ORAL_CONTRACEPTIVES"] = "Yes"
        else:
            injury_data["ORAL_CONTRACEPTIVES"] = "No"
    elif len(oral_contraceptives) > 1:
        injury_data["ORAL_CONTRACEPTIVES"] = "Too many answers"

    #HORMONAL_CONTRACEPTIVES
    hormonal_contraceptives = get_checkbox_array(95, 97)
    if len(hormonal_contraceptives) == 1:
        if "Yes" in hormonal_contraceptives[0]:
            if text_info["hormonal_contraceptives"] != "":
                injury_data["HORMONAL_CONTRACEPTIVES"] = "Yes, " + text_info["hormonal_contraceptives"]
            else:
                injury_data["HORMONAL_CONTRACEPTIVES"] = "Yes"
        else:
            injury_data["HORMONAL_CONTRACEPTIVES"] = "No"
    elif len(hormonal_contraceptives) > 1:
        injury_data["HORMONAL_CONTRACEPTIVES"] = "Too many answers"

    #OTHER_COMMENTS
    injury_data["OTHER_COMMENTS"] = text_info["other_comments"]



    #Not nice fix making overuse and onset not exclusive
    if injury_data['OVERUSE_TRAUMA'] == "Too many answers":
        injury_data['OVERUSE_TRAUMA'] = "Both, Overuse and Trauma"
    if injury_data['ONSET'] == "Too many answers":
        injury_data['ONSET'] = "Both, Gradual and Sudden"

    return injury_data


if __name__ == "__main__":

    pdf_path = "pdf.pdf"
    injury_data = extract_info_from_pdf(pdf_path)
    for key, value in injury_data.items():
        print(f"{key}: {value}")



 
