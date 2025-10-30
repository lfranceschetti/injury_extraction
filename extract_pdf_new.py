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
from constants.checkbox_map import checkbox_map, checkbox_map_by_type
from constants.columns import row_new
from helpers.iso import parse_date_to_iso
from helpers.pdf import get_text_info, detect_checkboxes, number_boxes_reading_order, get_checkbox_info, pdf_to_images, save_debug_visualization_with_labels
from helpers.utils import get_form_type

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SPLIT_RULES = [

    {"key": "name", "start": "Name:", "end": "Date of injury:"},
    {"key": "injury_date", "start": "Date of injury:", "end": "Date of return"},
    {"key": "return_date", "start": "Date of return to full participation:", "end": " (Send"},
    {"key": "match", "start": "Match", "end": "(min. of injury)"},
    {"key": "injury_mechanism", "start": "(Describe in words)", "end": "Continues on the next page"},
    {"key": "other_diagnostic_examination", "start": "Other (specify):", "end": "\n"},
    {"key": "diagnosis", "start": "Diagnosis (Specify results of examination): ", "end": "\n"},
    {"key": "other_comments", "start": "Other comments:", "end": "\n"},
    {"key": "re_injury", "start": "return from previous injury):", "end": "\n"},
]

HEAD_SPLIT_RULES = [
    {"key": "other_location", "start": "Occipital  Other:", "end": "Injury type"},
    {"key": "tbi", "start": "Mild Traumatic Brain Injury (TBI) with abnormality on MRI:", "end": "Moderate TBI"},
    {"key": "other_type", "start": "Severe TBI\n", "end": "\n"},
    {"key": "other_player_contact", "start": "Other body part:", "end": "\n"},
    {"key": "other_object_contact", "start": "Other object:", "end": "\n"},
    {"key": "player_substitution", "start": "Yes, after ", "end": " minutes"},
    {"key": "other_concussion", "start": "vision etc..) \n Other:", "end": "\n"},
]

INJURY_SPLIT_RULES = [
    {"key": "ultrasonography_date", "start": "Ultrasonography (date): \n", "end": "\n"},
    {"key": "arthroscopy_date", "start": "Arthroscopy (date): ", "end": "\n  X-ray"},
    {"key": "x_ray_date", "start": "X-ray (date): ", "end": "MRI"},
    {"key": "mri_date", "start": "MRI (date): ", "end": "Other (specify):"},
    {"key": "other_diagnostic_examination", "start": "Other (specify):", "end": "\n"},
]

LOWER_EXTREMITIES_SPLIT_RULES = INJURY_SPLIT_RULES + [
    {"key": "other_location", "start": "ilis  Other: ", "end": "\n"},
]

KNEE_SPLIT_RULES = [
    {"key": "other_injury_classification", "start": "ge PF  Other::", "end": "\n"},
    {"key": "prev_ctrl_injury", "start": "nosis?  No  Unknown \n  Yes (If know, date of return from previous injury):", "end": "\n"},
    {"key": "let_all", "start": "LET/ALL (specify): ", "end": "Patella te"},
    {"key": "acl_allograft", "start": " band  Allograft (specify):", "end": "Hamstring te"},
    {"key": "other_acl_repair", "start": "endon  Other (specify):", "end": "MCL repai"},
    {"key": "synthetic", "start": "Synthetic (specify):", "end": "Allogr"},
    {"key": "mcl_allograft", "start": "Allograft (specify):", "end": "Hamstring", "second_start": True},
    {"key": "other_mcl_repair", "start": "don  Other (specify):", "end": "Other comments", "second_start": True},
] + INJURY_SPLIT_RULES

ILLNESS_SPLIT_RULES = [
    {"key": "name", "start": "Name:", "end": "Date of illness:"},
    {"key": "injury_date", "start": "Date of illness:", "end": "Date of return"},
    {"key": "other_illness", "start": "ver \n Other:", "end": "\n"},
    {"key": "other_affected_organ", "start": "nological Other:", "end": "\n"},
    {"key": "re_injury", "start": "return from previous illness):", "end": "\n"},

]



def extract_info_from_pdf(pdf_path):

    injury_data = row_new.copy()

    reader = PdfReader(pdf_path)
    full_text = "\n".join((page.extract_text() or "") for page in reader.pages)

    form_type = get_form_type(full_text)
    injury_data['FORM_TYPE'] = form_type

    print("FULL TEXT: ", repr(full_text))

    # Adjust these values to crop top/bottom/left/right (in pixels)
    # For 300 DPI: ~100px = 0.33 inches, ~200px = 0.67 inches
    checkboxes = get_checkbox_info(pdf_path, crop_top=400, crop_bottom=400, crop_left=0, crop_right=0)
    print("checkboxes: ", checkboxes)

    if form_type == "HEAD":
        split_rules = SPLIT_RULES + HEAD_SPLIT_RULES
    elif form_type == "INJURY":
        split_rules = SPLIT_RULES + INJURY_SPLIT_RULES
    elif form_type == "LOWER_EXTREMITIES":
        split_rules = SPLIT_RULES + LOWER_EXTREMITIES_SPLIT_RULES
    elif form_type == "ILLNESS":
        split_rules = SPLIT_RULES + ILLNESS_SPLIT_RULES
    elif form_type == "KNEE":
        split_rules = SPLIT_RULES + KNEE_SPLIT_RULES


    text_info = get_text_info(pdf_path, split_rules)

    print("text_info: ", text_info)

    injury_data["NAME"] = text_info["name"]

    injury_data["INJURY_DATE"] = parse_date_to_iso(text_info["injury_date"])
    injury_data["RETURN_DATE"] = parse_date_to_iso(text_info["return_date"])

    def get_checkbox_data(start, end, get_string=True, has_other=False, other_text="", only_one=False):
        array = [checkbox_map_by_type[form_type][str(i)] for i in range(start, end) if checkboxes[str(i)]]
        print("ARRAY: ", array)
        if has_other and checkboxes[str(end-1)] == True:
            if other_text != "":
                #Remove the one that starts with "Other"
                array = [item for item in array if not item.startswith("Other")]
                array.append(other_text)
         
        
        if only_one:
            if len(array) == 1:
                return array[0]
            elif len(array) > 1:
                return "Too many answers"
            else:
                return ""
        
        if get_string:
            return ", ".join(array)
        else:
            return array

    def add_occurence_info(start, injury_data, text_info):
        end = start + 3
        occurrence = get_checkbox_data(start, end)
        injury_data["OCCURRENCE_ONSET_TYPE"] = occurrence
        if "," in occurrence:
            injury_data["OCCURRENCE_ONSET_TYPE"] = "Too many answers"
      

        if "Match" in occurrence:
            if text_info["match"] != "":
                injury_data["OCCURRENCE_MATCH_MINUTE"] = text_info["match"]
            else:
                injury_data["OCCURRENCE_MATCH_MINUTE"] = "N/A"
    
        injury_data["OCCURRENCE_CONTEXT"] = get_checkbox_data(end, end + 12)
        return injury_data


    def add_injury_mechanism_info(start, injury_data, text_info, form_type):
        injury_data["OVERUSE_TRAUMA"] = get_checkbox_data(start, start + 2)
        injury_data["ONSET"] = get_checkbox_data(start + 2, start + 4, only_one=True)
        if form_type == "HEAD":
            injury_data["HEADER_DUEL"] = get_checkbox_data(start + 4, start + 6, only_one=True)
            injury_data["CONTACT"] = get_checkbox_data(start + 6, start + 10)
            player_contact = get_checkbox_data(start + 10, start + 15, has_other=True, other_text=text_info["other_player_contact"])
            object_contact = get_checkbox_data(start + 15, start + 20, has_other=True, other_text=text_info["other_object_contact"])
            contact_points = [cp for cp in [player_contact, object_contact] if cp]
            if contact_points and len(contact_points) > 0:
                injury_data['CONTACT_POINT'] = ", ".join(contact_points)
            second_start = start + 20
        elif form_type != "HEAD":
            injury_data["CONTACT"] = get_checkbox_data(start + 4, start + 7)
            second_start = start + 7
        injury_data["ACTION"] = get_checkbox_data(second_start, second_start + 15)
        injury_data["ACTION_DESCRIPTION"] = text_info["injury_mechanism"]
        return injury_data
    
    def add_recurrence_info(start, injury_data, text_info):
        recurrence = get_checkbox_data(start, start + 3, only_one=True)
        injury_data["RECURRENCE"] = recurrence
        if recurrence == "Yes":
            if text_info["re_injury"] != "":
                injury_data["PREVIOUS_RETURN_DATE"] = parse_date_to_iso(text_info["re_injury"])
            else:
                injury_data["PREVIOUS_RETURN_DATE"] = "N/A"
        return injury_data

    def add_diagnostic_examination_info(start, injury_data, text_info):
        diagnostic_examination = get_checkbox_data(start, start + 6)
        injury_data["DIAGNOSTIC_EXAMINATION"] = diagnostic_examination
        examination_dates = []
        if "Ultrasono" in diagnostic_examination:
            examination_dates.append(parse_date_to_iso(text_info["ultrasonography_date"]).replace("\n", ""))
        if "Arthroscopy" in diagnostic_examination:
            print("ARTHROSCOPY DATE: ", repr(text_info["arthroscopy_date"].replace("\n", "")))
            examination_dates.append(parse_date_to_iso(text_info["arthroscopy_date"].replace("\n", "")))
        if "X-ray" in diagnostic_examination:
            examination_dates.append(parse_date_to_iso(text_info["x_ray_date"].replace("\n", "")))
        if "MRI" in diagnostic_examination:
            examination_dates.append(parse_date_to_iso(text_info["mri_date"].replace("\n", "")))
        if "Other" in diagnostic_examination:
            examination_dates.append(text_info["other_diagnostic_examination"].replace("\n", ""))

        print("EXAMINATION_DATES: ", repr(examination_dates))
        if examination_dates and len(examination_dates) > 0:
            injury_data["DIAGNOSTIC_EXAMINATION_DATE"] = ", ".join(examination_dates)

        injury_data["DIAGNOSIS"] = text_info["diagnosis"]
        return injury_data

    #Because its the same for INJURY and LOWER_EXTREMITIES
    def add_other_info(start, injury_data, text_info):
        injury_data = add_recurrence_info(start, injury_data, text_info)
        injury_data["REFEREE_SANCTION"] = get_checkbox_data(start + 3, start + 8)
        injury_data = add_diagnostic_examination_info(start + 8, injury_data, text_info)
        injury_data["SURGERY"] = get_checkbox_data(start + 14, start + 17, only_one=True)
        injury_data["OTHER_COMMENTS"] = text_info["other_comments"]
        return injury_data




  
    if form_type == "HEAD":
        injury_data["INJURY_LOCATION"] = get_checkbox_data(1, 13, has_other=True, other_text=text_info["other_location"])
        injury_type = get_checkbox_data(13, 22, has_other=True, other_text=text_info["other_type"])
        if "Mild Traumatic Brain Injury (TBI) with abnormality on MRI:" in injury_type and text_info["tbi"] is not None and text_info["tbi"] != "":
            injury_type = injury_type.split("MRI:")[0] + "MRI: " + text_info["tbi"] + injury_type.split("MRI:")[1]
        injury_data["TYPE"] = injury_type
        occurrence = get_checkbox_data(22, 25, get_string=False, only_one=True)
        injury_data = add_occurence_info(22, injury_data, text_info)
        injury_data = add_injury_mechanism_info(37, injury_data, text_info, form_type)
        injury_data = add_recurrence_info(72, injury_data, text_info)
        injury_data["REFEREE_SANCTION"] = get_checkbox_data(75, 80)
        player_substitution = get_checkbox_data(80, 83, only_one=True)
        if player_substitution == "Yes":
            injury_data["PLAYER_SUBSTITUTION_TIME"] = text_info["player_substitution"]
        elif player_substitution == "Yes, immediately":
            player_substitution_time = "Yes"
            injury_data["PLAYER_SUBSTITUTION_TIME"] = "Immediately"
        injury_data["PLAYER_SUBSTITUTION"] = player_substitution

        injury_data["REVIEW_SYSTEM"] = get_checkbox_data(83, 86, only_one=True)
        injury_data["CONCUSSION_DOMAINS"] = get_checkbox_data(86, 93, get_string=True, has_other=True, other_text=text_info["other_concussion"])



    elif form_type == "INJURY":
        injury_data["INJURY_LOCATION"] = get_checkbox_data(1, 20)
        injury_data["INJURY_SIDE"] = get_checkbox_data(20, 22)
        injury_data["TYPE"] = get_checkbox_data(22, 39)
        injury_data = add_occurence_info(39, injury_data, text_info)
        injury_data = add_injury_mechanism_info(54, injury_data, text_info, form_type)
        injury_data = add_other_info(76, injury_data, text_info)

    elif form_type == "LOWER_EXTREMITIES":
        injury_data["INJURY_LOCATION"] = get_checkbox_data(1, 16, has_other=True, other_text=text_info["other_location"])
        injury_data["INJURY_SIDE"] = get_checkbox_data(16, 19)
        injury_data["INJURY_SITE"] = get_checkbox_data(19, 22)
        injury_data["TYPE"] = get_checkbox_data(22, 26)
        injury_data["INJURY_CLASSIFICATION"] = get_checkbox_data(26, 33)
        injury_data = add_occurence_info(33, injury_data, text_info)
        injury_data = add_injury_mechanism_info(48, injury_data, text_info, form_type)
        injury_data = add_other_info(70, injury_data, text_info)


    elif form_type == "KNEE":
        injury_data["INJURY_CLASSIFICATION"] = get_checkbox_data(1, 16, has_other=True, other_text=text_info["other_injury_classification"])
        injury_data["INJURY_SIDE"] = get_checkbox_data(16, 19)
        injury_data["ACL_GRADING"] = get_checkbox_data(19, 21)
        injury_data["MCL_GRADING"] = get_checkbox_data(21, 24)
        injury_data = add_occurence_info(24, injury_data, text_info)
        injury_data = add_injury_mechanism_info(39, injury_data, text_info, form_type)
        injury_data = add_recurrence_info(61, injury_data, text_info)
        previous_contralateral_injury = get_checkbox_data(64, 67, only_one=True)
        injury_data["PREVIOUS_CONTRALATERAL_INJURY"] = previous_contralateral_injury
        if previous_contralateral_injury == "Yes":
            if text_info["prev_ctrl_injury"] != "":
                injury_data["PREVIOUS_CONTRALATERAL_INURY_RETURN_DATE"] = parse_date_to_iso(text_info["prev_ctrl_injury"])
            else:
                injury_data["PREVIOUS_CONTRALATERAL_INURY_RETURN_DATE"] = "N/A"
        injury_data["REFEREE_SANCTION"] = get_checkbox_data(67, 72)
        injury_data = add_diagnostic_examination_info(72, injury_data, text_info)
        injury_data["BRACING"] = get_checkbox_data(78, 81, only_one=True)
        injury_data["SURGERY"] = get_checkbox_data(81, 84, only_one=True)
        acl_repair = get_checkbox_data(84, 92)
        mcl_repair = get_checkbox_data(92, 97)
        acl_specs = []
        mcl_specs = []
        if "LET/ALL" in acl_repair and text_info["let_all"] != "":
            acl_specs.append(text_info["let_all"])
        if "Allograft" in acl_repair and text_info["acl_allograft"] != "":
            acl_specs.append(text_info["allograft"])
        if "Other" in acl_repair and text_info["other_acl_repair"] != "":
            acl_specs.append(text_info["other_acl_repair"])
        if "Synthetic" in mcl_repair and text_info["synthetic"] != "":
            mcl_specs.append(text_info["synthetic"])
        if "Allograft" in mcl_repair and text_info["mcl_allograft"] != "":
            mcl_specs.append(text_info["mcl_allograft"])
        if "Other" in mcl_repair and text_info["other_mcl_repair"] != "":
            print("OTHER MCL REPAIR: ", repr(text_info["other_mcl_repair"]))
            mcl_specs.append(text_info["other_mcl_repair"])

        injury_data["ACL_REPAIR"] = acl_repair
        injury_data["MCL_REPAIR"] = mcl_repair
        injury_data["ACL_REPAIR_SPECIFICATION"] = ", ".join(acl_specs)
        injury_data["MCL_REPAIR_SPECIFICATION"] = ", ".join(mcl_specs)
        injury_data["OTHER_COMMENTS"] = text_info["other_comments"]

    elif form_type == "ILLNESS":
        injury_data["TYPE"] = get_checkbox_data(1, 8, has_other=True, other_text=text_info["other_illness"])
        injury_data["AFFECTED_ORGAN"] = get_checkbox_data(8, 22, has_other=True, other_text=text_info["other_affected_organ"])
        injury_data = add_recurrence_info(22, injury_data, text_info)
        injury_data["DIAGNOSIS"] = text_info["diagnosis"]
        injury_data["OTHER_COMMENTS"] = text_info["other_comments"]

    return injury_data


if __name__ == "__main__":

    print("PDF Extractor")
    print("=" * 50)
    
    
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    pdf_path = sys.argv[1]


    injury_data = extract_info_from_pdf(pdf_path)
    for key, value in injury_data.items():
        print(f"{key}: {value}")



 
