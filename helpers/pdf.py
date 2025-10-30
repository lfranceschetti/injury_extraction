# pip install pypdf
import re
from pypdf import PdfReader
# pip install pdf2image pytesseract opencv-python pillow
# And install Tesseract on your OS (e.g., brew install tesseract, apt-get install tesseract-ocr)
from pdf2image import convert_from_path
import pytesseract, cv2, numpy as np
import os
from PIL import Image
from constants.checkbox_map import checkbox_map, checkbox_map_by_type
from constants.columns import row
from helpers.iso import parse_date_to_iso



def get_text_info(pdf_path: str, split_rules: list) -> dict:
    reader = PdfReader(pdf_path)
    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)
    out = {}

    for rule in split_rules:
        start_pat = rule["start"]
        end_pat = rule["end"]

        # Find absolute start index
        abs_start = full_text.find(start_pat)
        if "second_start" in rule:
            #Start from the second time the start pattern is found
            abs_start = full_text.find(start_pat, abs_start + len(start_pat))
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


def detect_checkboxes(img, use_hierarchy=False, crop_top=0, crop_bottom=0, crop_left=0, crop_right=0):
    # Crop the image if needed
    h, w = img.shape[:2]
    img_cropped = img[crop_top:h-crop_bottom, crop_left:w-crop_right]
    
    gray = cv2.cvtColor(img_cropped, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (3,3), 0)
    # Replace adaptive threshold with OTSU (automatic global threshold)
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    mode = cv2.RETR_TREE if use_hierarchy else cv2.RETR_EXTERNAL
    cnts, _ = cv2.findContours(bw, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for i, c in enumerate(cnts):
        x,y,w,h = cv2.boundingRect(c)
        # if w == 0 or h == 0:
        #     continue
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

        # Adjust coordinates back to original image space
        boxes.append({"bbox": (x+crop_left, y+crop_top, w, h), "fill_ratio": fill})

    # Heuristic: filled if inside mean > threshold
    for b in boxes:
        b["checked"] = b["fill_ratio"] > 0.2

    boxes = remove_duplicate_boxes(boxes)

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
    swap_map = { }

    for dst_idx, src_idx in swap_map.items():
        ordered[dst_idx] = ordered_copy[src_idx]


    # Assign numbers 1..N in order
    for idx, b in enumerate(ordered, start=1):
        b["number"] = idx

    
    return boxes


def get_checkbox_info(pdf_path: str, save_debug=True, debug_dir="debug", crop_top=0, crop_bottom=0, crop_left=0, crop_right=0):
    imgs = pdf_to_images(pdf_path)
    box_map = {}
    if save_debug:
        os.makedirs(debug_dir, exist_ok=True)
    
    # Track cumulative box number across all pages
    cumulative_box_number = 0
    
    for idx, img in enumerate(imgs):
        boxes = detect_checkboxes(img, use_hierarchy=False, crop_top=crop_top, crop_bottom=crop_bottom, crop_left=crop_left, crop_right=crop_right)

        
        # Number boxes in reading order
        number_boxes_reading_order(boxes)
        
        # Renumber boxes to be cumulative across pages
        for box in boxes:
            cumulative_box_number += 1
            box["number"] = cumulative_box_number
        
        if save_debug:
            base_name = os.path.splitext(os.path.basename(pdf_path))[0]
            out_labeled = os.path.join(debug_dir, f"{base_name}_page{idx+1}.png")
            save_debug_visualization_with_labels(img, boxes, out_labeled)
            # Save intermediates for tuning
            # Recompute the intermediates used in detection for export
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            blur = cv2.GaussianBlur(gray, (3,3), 0)
            bw = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                       cv2.THRESH_BINARY_INV, 31, 10)
            open_k = cv2.getStructuringElement(cv2.MORPH_RECT, (3,3))
    
            cv2.imwrite(os.path.join(debug_dir, f"page_{idx+1}_bw.png"), bw)
   
        # Store checkbox states in box_map
        for box in boxes:
            box_map[str(box["number"])] = box["checked"]
        
    print(f"Total checkboxes across all pages: {cumulative_box_number}")
    return box_map

def pdf_to_images(pdf_path: str, dpi=300):
    pages = convert_from_path(pdf_path, dpi=dpi)
    return [np.array(p) for p in pages]  # RGB arrays


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


def remove_duplicate_boxes(boxes, iou_threshold=0.5):
    """Remove duplicate/overlapping boxes using Non-Maximum Suppression approach"""
    if not boxes:
        return boxes
    
    # Sort by position (top-to-bottom, left-to-right) to maintain reading order
    # This ensures deduplication preserves spatial ordering
    boxes_sorted = sorted(boxes, key=lambda b: (b["bbox"][1], b["bbox"][0]))  # (y, x)
    
    keep = []
    while boxes_sorted:
        current = boxes_sorted.pop(0)
        keep.append(current)
        
        # Remove boxes that overlap significantly with current
        boxes_sorted = [b for b in boxes_sorted if calculate_iou(current["bbox"], b["bbox"]) < iou_threshold]
    
    return keep

def calculate_iou(box1, box2):
    """Calculate Intersection over Union (IoU) of two bounding boxes"""
    x1, y1, w1, h1 = box1
    x2, y2, w2, h2 = box2
    
    # Calculate intersection
    x_left = max(x1, x2)
    y_top = max(y1, y2)
    x_right = min(x1 + w1, x2 + w2)
    y_bottom = min(y1 + h1, y2 + h2)
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    intersection = (x_right - x_left) * (y_bottom - y_top)
    area1 = w1 * h1
    area2 = w2 * h2
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0