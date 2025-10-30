import zipfile
import xml.dom.minidom as minidom
import sys
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from constants.columns import row_new
from helpers.iso import parse_date_to_iso
from helpers.word import extract_xml_from_docx, get_text_display_from_runs, find_section_bounds, extract_form_fields
from helpers.utils import get_form_type




def extract_info_from_word(docx_path):
    """
    Extract structured data from UEFA injury form Word document
    """
    
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'w14': 'http://schemas.microsoft.com/office/word/2010/wordml'
    }
    
    # Open docx and read XML
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        xml_content = docx_zip.read('word/document.xml')
    
    root = ET.fromstring(xml_content)

    # Precompute paragraphs and their texts once
    paragraphs = list(root.findall('.//w:p', namespaces))
    para_texts = [''.join([t.text for t in p.findall('.//w:t', namespaces) if t.text]) for p in paragraphs]


    injury_data = row_new.copy()
    
    # Extract all form fields
    text_fields, checkbox_entries, para_texts = extract_form_fields(root, paragraphs, namespaces)
   
    # Helper to collect checked labels between two section headers
    def extract_checkbox(start_marker, end_marker=None, only_one=False, num_paragraphs=None, give_additional_info=False):
        start_idx_local, end_idx_local = find_section_bounds(para_texts, start_marker, end_marker, num_paragraphs)
        print("start_idx_local: ", start_idx_local)
        print("end_idx_local: ", end_idx_local)
        results = []

        #Hacky way to get additional information out of text fields that should go into other columns
        match_minute = None
        diagnostic_dates = []
        recurrence_return_date = None
        player_substitution_time = None
        acl_mcl_specs = []

        if start_idx_local is not None:
            for entry in checkbox_entries:
                if entry['para_idx'] > start_idx_local and (end_idx_local is None or entry['para_idx'] < end_idx_local):
                    print("entry: ", entry)
                
                if entry['checked'] and entry['para_idx'] > start_idx_local and (end_idx_local is None or entry['para_idx'] < end_idx_local):

                    label = entry['label'].strip()

                    #OCCURRENCE DURING MATCH
                    if label.startswith("Match"):
                        label_text = "Match"
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            match_minute = entry.get('following_text').strip()
                        else:
                            match_minute = "N/A"
                

                    elif label.startswith("Ultrasono") or label.startswith("Anthro") or label.startswith("X-ray") or label.startswith("MRI") or label.startswith("Arthroscopy"):
                        label_text = label.replace(" (date):", "").replace("(date):", "")
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            diagnostic_dates.append(entry.get('following_text').strip())
                    elif label.startswith("LET") or label.startswith("Allograft") or label.startswith("Synthetic"):
                        label_text = label.replace(" (specify):", "")
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            acl_mcl_specs.append(entry.get('following_text').strip())


                    elif label == "Knee (please use separate card for ACL/MCL injuries)":
                        label_text = "Knee"
                    
                    elif label.startswith("Mild Traumatic"):
                        label_text = label
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            label_text += " " + entry.get('following_text').strip()

                    #ALL CASES WHERE YES IS ANSWERED and there is a following text
                    elif label and label.startswith("Yes (If know"):
                        label_text = "Yes"
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            recurrence_return_date = parse_date_to_iso(entry.get('following_text').strip())
                        else:
                            recurrence_return_date = "N/A"
                    elif label and label.startswith("Yes, after"):
                        label_text = "Yes"
                        player_substitution_time = entry.get('following_text').strip()
                    elif label and label.startswith("Yes") and entry.get('following_text'):
                        label_text = "Yes"
                        if entry.get('following_text') != '':
                            label_text += ", " + entry.get('following_text')
                    elif label and label.startswith("Yes (specify)") and not entry.get('following_text'):
                        label_text = "Yes"
                    elif label and label.startswith("Yes (give") and not entry.get('following_text'):
                        label_text = "Yes"

                    #ALL CASES WHERE OTHER IS ANSWERED

                    elif label and label.startswith("Other (specify)") and ("ACL" in start_marker or "MCL" in start_marker):
                        label_text = "Other"
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            acl_mcl_specs.append(entry.get('following_text').strip())
                        



                    elif label and label.startswith("Other") and not label.startswith("Other training") and not label.startswith("Other cup match") and not label.startswith("Other player action"):
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            label_text = (entry.get('following_text') or '').strip()
                        else:
                            label_text = "Other"
                    else:
                        label_text = (entry.get('following_text') or '').strip() or label
                    
                    label_text = re.sub(r' {2,}', ' ', label_text)

                    if label_text:  
                        results.append(label_text)

        final_string = ""
        print("RESULTS: ", results)
        if len(results) == 0:
            pass
        elif only_one and len(results) == 1:
            final_string = results[0]
        elif only_one and len(results) > 1:
            final_string = "Too many answers"
        else:
            final_string = ", ".join(results)

        if give_additional_info:
            additional_info = None
            if match_minute:
                additional_info = match_minute
            if len(diagnostic_dates) > 0:
                additional_info = diagnostic_dates
            if recurrence_return_date:
                additional_info = recurrence_return_date
            if player_substitution_time:
                additional_info = player_substitution_time
            if len(acl_mcl_specs) > 0:
                additional_info = acl_mcl_specs
            return final_string, additional_info
        else:
            return final_string


    # Helper to collect displayed text from any FORMTEXT inputs between two section headers
    def extract_text(start_marker, end_marker=None, only_one=False, num_paragraphs=None):
        start_idx_local, end_idx_local = find_section_bounds(para_texts, start_marker, end_marker, num_paragraphs)
        collected = []
        if start_idx_local is None:
            return ""
        # Always include the header paragraph to capture inline fields after the label
        start_p = start_idx_local
        end_p = len(paragraphs) if end_idx_local is None else end_idx_local
        for p_idx in range(start_p, end_p):
            para = paragraphs[p_idx]
            runs = list(para.findall('.//w:r', namespaces))
            for i, run in enumerate(runs):
                fld_begin = run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces)
                if fld_begin is None:
                    continue
                ffdata = fld_begin.find('.//w:ffData', namespaces)
                if ffdata is None:
                    continue
                if ffdata.find('.//w:textInput', namespaces) is None:
                    continue
                text_value = get_text_display_from_runs(runs, i)
                if text_value:
                    if only_one:
                        return text_value
                    collected.append(text_value)
        return '; '.join(collected)


    # print("para_texts: ", para_texts)
    # print("text_fields: ", text_fields)
    # print("checkbox_entries: ", checkbox_entries)

    injury_data = row_new.copy()
    form_type = get_form_type("\n".join(para_texts))
    injury_data['FORM_TYPE'] = form_type
    

    injury_data['NAME'] = extract_text('name', 'date')
    print("NAME: ", injury_data['NAME'])
    injury_date = extract_text('date of', 'date of return to full participation')
    return_date = extract_text('date of return to full participation', 'send', only_one=True)
   

    injury_data['INJURY_DATE'] = parse_date_to_iso(injury_date)
    injury_data['RETURN_DATE'] = parse_date_to_iso(return_date)
       


    if form_type == "INJURY":
        print("INJURY FORM TYPE")
        injury_data['INJURY_LOCATION'] = extract_checkbox('injury location', 'injury side')
        injury_data['INJURY_SIDE'] = extract_checkbox('injury side', 'injury type')
        injury_data['TYPE'] = extract_checkbox('injury type', 'when did the injury occur?')
    elif form_type == "HEAD":
        injury_data['INJURY_LOCATION'] = extract_checkbox('location of impact', 'injury type')
        injury_data['TYPE'] = extract_checkbox('injury type', 'when did the injury occur?')
    elif form_type == "ILLNESS":
        injury_data['TYPE'] = extract_checkbox('type of illness', 'If other illness')
        injury_data['AFFECTED_ORGAN'] = extract_checkbox('If other illness', 'Other information')
    elif form_type == "KNEE":
        injury_data['INJURY_CLASSIFICATION'] = extract_checkbox('combination of injuries', 'injury side')
        injury_data['INJURY_SIDE'] = extract_checkbox('injury side', 'injury grading')
        injury_data['ACL_GRADING'] = extract_checkbox('ACL:', num_paragraphs=2)
        injury_data['MCL_GRADING'] = extract_checkbox('MCL:', num_paragraphs=3)
    elif form_type == "LOWER_EXTREMITIES":
        injury_data['INJURY_LOCATION'] = extract_checkbox('location of injury', 'injury side')
        injury_data['INJURY_SIDE'] = extract_checkbox('injury side', 'injury site')
        injury_data['INJURY_SITE'] = extract_checkbox('injury site', 'injury type')
        injury_data['TYPE'] = extract_checkbox('injury type', 'injury classification')
        injury_data['INJURY_CLASSIFICATION'] = extract_checkbox('injury classification', 'when did the injury occur?')

   

    #FOR ALL
    occurence_onset_type, occurence_match_minute = extract_checkbox('onset during', num_paragraphs=3, give_additional_info=True, only_one=True)
    injury_data['OCCURRENCE_ONSET_TYPE'] = occurence_onset_type
    injury_data['OCCURRENCE_MATCH_MINUTE'] = occurence_match_minute

    injury_data['OCCURRENCE_CONTEXT'] = extract_checkbox('N/A', 'Injury mechanism')
    injury_data['OVERUSE_TRAUMA'] = extract_checkbox('Was the injury caused by overuse or trauma?', num_paragraphs=2)
    injury_data['ONSET'] = extract_checkbox('did symptoms have', num_paragraphs=2, only_one=True)

    if form_type == "INJURY" or form_type == "KNEE" or form_type == "LOWER_EXTREMITIES":
        injury_data['CONTACT'] = extract_checkbox('Was the injury caused by contact?', num_paragraphs=3)
    if form_type == "HEAD":
        injury_data['HEADER_DUEL'] = extract_checkbox('header duel?', num_paragraphs=2, only_one=True)
        injury_data['CONTACT'] = extract_checkbox('Was the injury caused by contact?', num_paragraphs=4)
        contact_point1 = extract_checkbox("In case of player contact", "In case of object contact")
        contact_point2 = extract_checkbox("In case of object contact", "Circumstances")
        contact_points = [cp for cp in [contact_point1, contact_point2] if cp]
        if contact_points and len(contact_points) > 0:
            injury_data['CONTACT_POINT'] = ", ".join(contact_points)


        player_substitution, player_substitution_time = extract_checkbox("Was the player substituted?", num_paragraphs=4, give_additional_info=True)
        if player_substitution.strip() == "Yes, immediately":
            player_substitution = "Yes"
            player_substitution_time = "Immediately"
        injury_data['PLAYER_SUBSTITUTION'] = player_substitution
        injury_data['PLAYER_SUBSTITUTION_TIME'] = player_substitution_time
        injury_data['REVIEW_SYSTEM'] = extract_checkbox("Did you use the medical review system to inform your pitch side decision?", num_paragraphs=3)
        injury_data['CONCUSSION_DOMAINS'] = extract_checkbox("In case of concussion", num_paragraphs=10)

    if form_type == "HEAD":
        injury_data['REFEREE_SANCTION'] = extract_checkbox("sanction (Only for sudden onset match injuries):", num_paragraphs=7)
    else:
        injury_data['REFEREE_SANCTION'] = extract_checkbox("sanction:", num_paragraphs=7)

    injury_data['ACTION'] = extract_checkbox("Circumstances and player", "Injury mechanism/player action")
    injury_data['ACTION_DESCRIPTION'] = extract_text("Injury mechanism/player action", num_paragraphs=2)

    recurrence, recurrence_return_date = extract_checkbox("Was this a", num_paragraphs=4, give_additional_info=True)
    injury_data['RECURRENCE'] = recurrence
    if recurrence_return_date:
        injury_data['PREVIOUS_RETURN_DATE'] = recurrence_return_date

    prv_cntrl_injury, prv_cntrl_injury_return_date = extract_checkbox("Previous contralateral injury of same diagnosis?", num_paragraphs=4, give_additional_info=True)
    injury_data['PREVIOUS_CONTRALATERAL_INJURY'] = prv_cntrl_injury
    if prv_cntrl_injury_return_date:
        injury_data['PREVIOUS_CONTRALATERAL_INURY_RETURN_DATE'] = prv_cntrl_injury_return_date

    diagnostic_examination, diagnostic_dates = extract_checkbox("Diagnostic examination", num_paragraphs=7, give_additional_info=True)
    injury_data['DIAGNOSTIC_EXAMINATION'] = diagnostic_examination
    diagnostic_dates_string = ""
    if diagnostic_dates and len(diagnostic_dates) > 0:
        diagnostic_dates_string = ", ".join(parse_date_to_iso(date) for date in diagnostic_dates)
    injury_data['DIAGNOSTIC_EXAMINATION_DATE'] = diagnostic_dates_string


    injury_data['BRACING'] = extract_checkbox("Was any bracing used?", num_paragraphs=3, only_one=True)
    injury_data['DIAGNOSIS'] = extract_text("Diagnosis (specify results of examination):", num_paragraphs=1)
    injury_data['SURGERY'] = extract_checkbox("Was any surgery performed?", num_paragraphs=3, only_one=True)
    injury_data['OTHER_COMMENTS'] = extract_text("Other comments", num_paragraphs=1)
    
    
    
    acl_repair, acl_repair_spec = extract_checkbox("ACL repair", "MCL repair", give_additional_info=True)
    mcl_repair, mcl_repair_spec = extract_checkbox("MCL repair", "Other comments", give_additional_info=True)
    injury_data['ACL_REPAIR'] = acl_repair
    injury_data['MCL_REPAIR'] = mcl_repair
    if acl_repair_spec and len(acl_repair_spec) > 0:
        injury_data['ACL_REPAIR_SPECIFICATION'] = ", ".join(acl_repair_spec)
    if mcl_repair_spec and len(mcl_repair_spec) > 0:
        injury_data['MCL_REPAIR_SPECIFICATION'] = ", ".join(mcl_repair_spec)


    return injury_data





def print_injury_data(data):
    """Print extracted data in a readable format"""
    print("\n" + "="*60)
    print("EXTRACTED INJURY FORM DATA")
    print("="*60)
    
    for section, section_value in data.items():
        print(f"\n{section.replace('_', ' ').title()}: {section_value}")
    return
    

    
    print("\n" + "="*60)



    


if __name__ == "__main__":
    # Usage examples
    print("Word Document XML Extractor")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage: python script.py <path_to_docx> [output_xml_file]")
        print("\nExample:")
        print("  python script.py injury_form.docx")
        print("  python script.py injury_form.docx output.xml")
        sys.exit(1)
    
    docx_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Extract and display main XML
    extract_xml_from_docx(docx_file, output_file)

    injury_data = extract_info_from_word(docx_file)
    
    # Print to console
    print_injury_data(injury_data)