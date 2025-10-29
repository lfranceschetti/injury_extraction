import zipfile
import xml.dom.minidom as minidom
import sys
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from constants.columns import row
from helpers.iso import parse_date_to_iso
from helpers.word import extract_xml_from_docx, get_text_display_from_runs, find_section_bounds, extract_form_fields





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


    injury_data = row.copy()
    
    # Extract text fields (FORMTEXT)
    text_fields = {}

    # Extract all form fields
    text_fields, checkbox_entries, para_texts = extract_form_fields(root, paragraphs, namespaces)
    
   
    # Helper to collect checked labels between two section headers
    def extract_checkbox(start_marker, end_marker, only_one=False):
        start_idx_local, end_idx_local = find_section_bounds(para_texts, start_marker, end_marker)
        results = []
        if start_idx_local is not None:
            for entry in checkbox_entries:
                if entry['checked'] and entry['para_idx'] > start_idx_local and (end_idx_local is None or entry['para_idx'] < end_idx_local):
                    # Prefer the following text field content if present; otherwise use the checkbox label
                    if entry['label'] == "Match":
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            label_text = "Match (min. of injury: " + entry.get('following_text') + ")"
                        else:
                            label_text = "Match"

                    elif entry["label"] and entry["label"].strip().startswith("Yes") and entry.get('following_text'):
                        label_text = "Yes"
                        if entry.get('following_text') != '':
                            label_text += ", " + entry.get('following_text')
                    elif entry["label"] and entry["label"].strip().startswith("Yes (specify)") and not entry.get('following_text'):
                        label_text = "Yes"
                    elif entry["label"] and entry["label"].strip().startswith("Yes (give") and not entry.get('following_text'):
                        label_text = "Yes"
                    elif entry["label"] and entry["label"].strip().startswith("Other injury"):
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            label_text = (entry.get('following_text') or '').strip()
                        else:
                            label_text = "Other injury"
                    elif entry["label"] and entry["label"].strip().startswith("Other (specify)"):
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            label_text = (entry.get('following_text') or '').strip()
                        else:
                            label_text = "Other"
                    else:
                        label_text = (entry.get('following_text') or '').strip() or entry['label']

            
                    if label_text:
                        results.append(label_text)

        if only_one and len(results) == 1:
            return results[0]
        elif only_one and len(results) == 0:
            return ""
        elif only_one and len(results) > 1:
            return "Too many answers"
        else:
            return ", ".join(results)
                    

    # Helper to collect displayed text from any FORMTEXT inputs between two section headers
    def extract_text(start_marker, end_marker):
        start_idx_local, end_idx_local = find_section_bounds(para_texts, start_marker, end_marker)
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
                    collected.append(text_value)
        return '; '.join(collected)


    injury_data = row.copy()

    injury_data['NAME'] = extract_text('name', 'team')
    injury_data['TEAM'] = extract_text('team', 'code')
    injury_data['CODE'] = extract_text('code', 'date of injury')
    injury_date = extract_text('date of injury', 'date of return to full participation')
    return_date = extract_text('date of return to full participation', 'injury location')

    try:
        injury_iso = parse_date_to_iso(injury_date)
        injury_data['INJURY_DATE'] = injury_iso
    except Exception as e:
        injury_data['INJURY_DATE'] = "Wrong date format"

    try:
        return_iso = parse_date_to_iso(return_date)
        injury_data['RETURN_DATE'] = return_iso
    except Exception as e:
        injury_data['RETURN_DATE'] = "Wrong date format"


    injury_data['INJURY_LOCATION'] = extract_checkbox('injury location', 'injury side')
    injury_data['INJURY_SIDE'] = extract_checkbox('injury side', 'injury type')
    injury_data['INJURY_TYPE'] = extract_checkbox('injury type', 'training')
    injury_data['OCCURRENCE'] = extract_checkbox('training', 'injury mechanism')
    injury_data['OVERUSE_TRAUMA'] = extract_checkbox('overuse or trauma', 'onset', only_one=True)
    injury_data['ONSET'] = extract_checkbox('gradual or sudden', 'contact', only_one=True)
    injury_data['CONTACT'] = extract_checkbox('contact', 'running/sprinting', only_one=True)
    injury_data['ACTION'] = extract_checkbox('indirect contact', 'injury mechanism')
    injury_data['RE_INJURY'] = extract_checkbox('re-injury', 'referee', only_one=True)
    injury_data['REFEREE_SANCTION'] = extract_checkbox('referee', 'diagnostic exam')
    injury_data['DIAGNOSTIC_EXAMINATION'] = extract_checkbox('diagnostic exam', 'diagnosis')
    injury_data['SURGERY'] = extract_checkbox('surgery', 'menstrual phase', only_one=True)
    injury_data['MENSTRUAL_PHASE'] = extract_checkbox('menstrual phase', 'oral contraceptives', only_one=True)
    injury_data['ORAL_CONTRACEPTIVES'] = extract_checkbox('oral contraceptives', 'hormonal contraceptives', only_one=True)
    injury_data['HORMONAL_CONTRACEPTIVES'] = extract_checkbox('hormonal contraceptives', 'other information', only_one=True)
    
    # Action description and other comments as free-text inputs
    injury_data['ACTION_DESCRIPTION'] = extract_text('player action', 'other information')
    injury_data['DIAGNOSIS'] = extract_text('diagnosis', 'surgery')
    injury_data['OTHER_COMMENTS'] = extract_text('other comments', None)

    #Not nice fix making overuse and onset not exclusive
    if injury_data['OVERUSE_TRAUMA'] == "Too many answers":
        injury_data['OVERUSE_TRAUMA'] = "Both, Overuse and Trauma"
    if injury_data['ONSET'] == "Too many answers":
        injury_data['ONSET'] = "Both, Gradual and Sudden"

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