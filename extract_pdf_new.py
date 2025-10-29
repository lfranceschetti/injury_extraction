# pip install pypdf
import re
from pypdf import PdfReader
# pip install pdf2image pytesseract opencv-python pillow
# And install Tesseract on your OS (e.g., brew install tesseract, apt-get install tesseract-ocr)
from pdf2image import convert_from_path
import pytesseract, cv2, numpy as np
import sys
import os
from PIL import Image
from constants.checkbox_map import checkbox_map
from constants.columns import row_new
from helpers.iso import parse_date_to_iso
from helpers.pdf import get_text_info, detect_checkboxes, number_boxes_reading_order, get_checkbox_info, pdf_to_images, save_debug_visualization_with_labels
from helpers.utils import get_form_type

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SPLIT_RULES = [

    {"key": "name", "start": "Name:", "end": "Team:"},
    {"key": "injury_date", "start": "Date of injury:", "end": "Date of return"},
    {"key": "return_date", "start": "Date of return to full participation:", "end": " (Send"},
    {"key": "match", "start": "Match", "end": "(min. of injury)"},
    {"key": "injury_mechanism", "start": "(Describe in words)", "end": "Continues on the next page"},
    {"key": "other_diagnostic_examination", "start": "Other (specify):", "end": "\n"},
    {"key": "diagnosis", "start": "Diagnosis (specify results of examination): ", "end": "\n"},
    {"key": "other_comments", "start": "Other comments:", "end": "\n"},
]

HEAD_SPLIT_RULES = [
    {"key": "other_location", "start": "Occipital  Other:", "end": "Injury type"},
    {"key": "tbi", "start": "Mild Traumatic Brain Injury (TBI) with abnormality on MRI:", "end": "Moderate TBI"},
    {"key": "other_type", "start": "Severe TBI\n", "end": "\n"},
    {"key": "other_player_contact", "start": "Other body part:", "end": "\n"},
    {"key": "other_object_contact", "start": "Other object:", "end": "\n"},
    {"key": "re_injury", "start": "Yes (If known, date of return from previous injury):", "end": "\n"},
    {"key": "player_substitution", "start": "Yes, after ", "end": " minutes"},
    {"key": "other_concussion", "start": "ion etc..)\n Other:", "end": "\n"},
]


#To-do other concussion with head split rules does not work




def extract_info_from_pdf(pdf_path):

    injury_data = row_new.copy()

    reader = PdfReader(pdf_path)
    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)

    form_type = get_form_type(full_text)
    injury_data['FORM_TYPE'] = form_type

    checkboxes = get_checkbox_info(pdf_path)

    print("checkboxes: ", checkboxes)
    if form_type == "HEAD":
        split_rules = SPLIT_RULES + HEAD_SPLIT_RULES

    text_info = get_text_info(pdf_path, split_rules)

    print("text_info: ", text_info)

    injury_data["NAME"] = text_info["name"]

    injury_data["INJURY_DATE"] = parse_date_to_iso(text_info["injury_date"])
    injury_data["RETURN_DATE"] = parse_date_to_iso(text_info["return_date"])


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

    print("PDF Extractor")
    print("=" * 50)
    
    
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    pdf_path = sys.argv[1]


    injury_data = extract_info_from_pdf(pdf_path)
    for key, value in injury_data.items():
        print(f"{key}: {value}")



 
