import zipfile
import xml.dom.minidom as minidom
import sys



def extract_xml_from_docx(docx_path, output_file=None):
    """
    Extract and display the XML content from a Word document (.docx)
    
    Args:
        docx_path: Path to the .docx file
        output_file: Optional path to save the formatted XML
    """
    try:
        # Open the docx file as a zip archive
        with zipfile.ZipFile(docx_path, 'r') as docx_zip:
            # List all files in the archive
            
            # Extract the main document XML
            xml_content = docx_zip.read('word/document.xml')
            
            # Pretty print the XML
            dom = minidom.parseString(xml_content)
            pretty_xml = dom.toprettyxml(indent="  ")
            
            
            # Save to file if requested
            if output_file:
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(pretty_xml)
                print(f"\nXML saved to: {output_file}")
            
    except FileNotFoundError:
        print(f"Error: File '{docx_path}' not found!")
        sys.exit(1)
    except zipfile.BadZipFile:
        print(f"Error: '{docx_path}' is not a valid .docx file!")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

import zipfile
import xml.etree.ElementTree as ET

def extract_injury_form_data(docx_path):
    """
    Extract structured data from UEFA injury form Word document
    """
    
    # Define namespaces
    namespaces = {
        'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
        'w14': 'http://schemas.microsoft.com/office/word/2010/wordml'
    }
    
    # Open docx and read XML
    with zipfile.ZipFile(docx_path, 'r') as docx_zip:
        xml_content = docx_zip.read('word/document.xml')
    
    root = ET.fromstring(xml_content)
    

    injury_data_names = [
        "Name",
        "Team",
        "Code",
        "Injury Date",
        "Return Date",
        "Injury Location",
        "Injury Side",
        "Injury Type",
        "Occurrence",
        "Overuse/Trauma",
        "Onset",
        "Contact",
        "Action",
        "Action Description",
        "Re-injury",
        "Referee Sanction",
        "Diagnostic Examination",
        "Diagnosis",
        "Surgery",
        "Menstrual Phase",
        "Oral Contraceptives",
        "Hormonal Contraceptives",
        "Other Comments"
    ]

    injury_data = {name: "" for name in injury_data_names}

    
    
    # Extract text fields (FORMTEXT)
    text_fields = {}
    
    # Build a map of all paragraphs and their elements
    for para in root.findall('.//w:p', namespaces):
        elements = list(para.findall('.//w:r', namespaces))
        
        for i, run in enumerate(elements):
            fld_begin = run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces)
            if fld_begin is not None:
                ffdata = fld_begin.find('.//w:ffData', namespaces)
                if ffdata is not None:
                    name_elem = ffdata.find('.//w:name', namespaces)
                    field_name = name_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if name_elem is not None else None
                    
                    # Check if it's a text input (not checkbox)
                    text_input = ffdata.find('.//w:textInput', namespaces)
                    if text_input is not None:
                        # Find text between separate and end
                        text_value = ""
                        found_separate = False
                        
                        for j in range(i + 1, len(elements)):
                            next_run = elements[j]
                            
                            if found_separate:
                                text_elem = next_run.find('.//w:t', namespaces)
                                if text_elem is not None and text_elem.text:
                                    text_value += text_elem.text
                                
                                end_char = next_run.find('.//w:fldChar[@w:fldCharType="end"]', namespaces)
                                if end_char is not None:
                                    break
                            
                            separate_char = next_run.find('.//w:fldChar[@w:fldCharType="separate"]', namespaces)
                            if separate_char is not None:
                                found_separate = True
                        
                        if field_name:
                            text_fields[field_name] = text_value.strip()
    
    # Extract checkboxes
    checkboxes = {}
    # Keep ordered entries with paragraph indices for section-scoped extraction
    checkbox_entries = []
    para_texts = []
    
    for para_idx, para in enumerate(root.findall('.//w:p', namespaces)):
        # Aggregate full paragraph text (runs may split words)
        para_text = ''.join([t.text for t in para.findall('.//w:t', namespaces) if t.text])
        para_texts.append(para_text)
        elements = list(para.findall('.//w:r', namespaces))
        
        for i, run in enumerate(elements):
            fld_begin = run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces)
            if fld_begin is not None:
                ffdata = fld_begin.find('.//w:ffData', namespaces)
                if ffdata is not None:
                    checkbox = ffdata.find('.//w:checkBox', namespaces)
                    if checkbox is not None:
                        name_elem = ffdata.find('.//w:name', namespaces)
                        checked_elem = checkbox.find('.//w:checked', namespaces)
                        
                        field_name = name_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val') if name_elem is not None else None
                        # Consider both <w:checked/> and <w:checked w:val="1"/> as checked
                        if checked_elem is not None:
                            checked_val = checked_elem.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            is_checked = (checked_val is None) or (checked_val == '1')
                        else:
                            is_checked = False
                        
                        # Get the label text that follows the checkbox.
                        # Concatenate subsequent run texts within this paragraph until another field starts.
                        label = ""
                        for j in range(i + 1, len(elements)):
                            next_run = elements[j]
                            # Stop if we hit another field begin (start of next form field)
                            if next_run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces) is not None:
                                break
                            text_elem = next_run.find('.//w:t', namespaces)
                            if text_elem is not None and text_elem.text:
                                label += text_elem.text
                        label = (label or "").strip()
                        # If the label is suspiciously short (e.g., split across paragraphs like 'L' + 'umbosacral'),
                        # try to append the beginning of the next paragraph's text.
                        if (not label) or len(label) <= 2:
                            # Find parent paragraph index from para_idx captured above
                            # para_idx is available in this loop scope
                            if para_idx + 1 < len(para_texts):
                                next_para_text = (para_texts[para_idx + 1] or "").strip()
                                # Only append a small prefix to avoid pulling entire next line
                                if next_para_text:
                                    # Take up to first 30 chars to complete the word/phrase
                                    prefix = next_para_text[:30]
                                    label = (label + prefix).strip()
                        
                        # Capture the displayed text of an immediately following text field (used for 'Other' etc.)
                        following_text = ""
                        for j in range(i + 1, len(elements)):
                            next_run = elements[j]
                            fld_begin_ahead = next_run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces)
                            if fld_begin_ahead is not None:
                                ffdata_ahead = fld_begin_ahead.find('.//w:ffData', namespaces)
                                if ffdata_ahead is not None and ffdata_ahead.find('.//w:textInput', namespaces) is not None:
                                    text_value_tmp = ""
                                    found_separate_tmp = False
                                    for k in range(j + 1, len(elements)):
                                        look_run = elements[k]
                                        if found_separate_tmp:
                                            t_el = look_run.find('.//w:t', namespaces)
                                            if t_el is not None and t_el.text:
                                                text_value_tmp += t_el.text
                                            end_char_tmp = look_run.find('.//w:fldChar[@w:fldCharType="end"]', namespaces)
                                            if end_char_tmp is not None:
                                                break
                                        separate_char_tmp = look_run.find('.//w:fldChar[@w:fldCharType="separate"]', namespaces)
                                        if separate_char_tmp is not None:
                                            found_separate_tmp = True
                                    following_text = text_value_tmp.strip()
                                    break
                                # If another field begins but it's not a text input, stop looking further in this paragraph
                                break
                        
                        if field_name or label:
                            key = field_name if field_name else label
                            entry = {'checked': is_checked, 'label': label.strip(), 'para_idx': para_idx, 'following_text': following_text}
                            checkboxes[key] = {'checked': is_checked, 'label': label.strip()}
                            checkbox_entries.append(entry)
    
    # Parse player details from text fields
    # Extract all text content to find specific values
    all_text = ' '.join([t.text for t in root.findall('.//w:t', namespaces) if t.text])
    

     
    # Helper to collect checked labels between two section headers
    def extract_checkbox(start_marker, end_marker, only_one=False):
        start_idx_local = None
        end_idx_local = None
        for idx, text in enumerate(para_texts):
            lowered = (text or '').lower()
            if start_idx_local is None and start_marker in lowered:
                start_idx_local = idx
            elif start_idx_local is not None and end_marker and end_marker in lowered:
                end_idx_local = idx
                break
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
                        if entry.get('following_text') is not None and entry.get('following_text') != '':
                            label_text = entry.get('following_text')
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
        start_idx_local = None
        end_idx_local = None
        for idx, text in enumerate(para_texts):
            lowered = (text or '').lower()
            if start_idx_local is None and start_marker in lowered:
                start_idx_local = idx
            elif start_idx_local is not None and end_marker and end_marker in lowered:
                end_idx_local = idx
                break
        collected = []
        if start_idx_local is None:
            return ""
        # Iterate paragraphs in range and extract displayed text from text inputs
        paragraphs = list(root.findall('.//w:p', namespaces))
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
                # Capture displayed text between separate and end for this text field
                text_value = ""
                found_separate = False
                for j in range(i + 1, len(runs)):
                    nxt = runs[j]
                    if found_separate:
                        t_el = nxt.find('.//w:t', namespaces)
                        if t_el is not None and t_el.text:
                            text_value += t_el.text
                        end_char = nxt.find('.//w:fldChar[@w:fldCharType="end"]', namespaces)
                        if end_char is not None:
                            break
                    separate_char = nxt.find('.//w:fldChar[@w:fldCharType="separate"]', namespaces)
                    if separate_char is not None:
                        found_separate = True
                text_value = text_value.strip()
                if text_value:
                    collected.append(text_value)
        return '; '.join(collected)


    injury_data['Name'] = extract_text('name', 'team')
    injury_data['Team'] = extract_text('team', 'code')
    injury_data['Code'] = extract_text('code', 'date of injury')
    injury_data['Injury Date'] = extract_text('date of injury', 'date of return to full participation')
    injury_data['Return Date'] = extract_text('date of return to full participation', 'injury location')


    injury_data['Injury Location'] = extract_checkbox('injury location', 'injury side')
    injury_data['Injury Side'] = extract_checkbox('injury side', 'injury type')
    injury_data['Injury Type'] = extract_checkbox('injury type', 'training')
    injury_data['Occurrence'] = extract_checkbox('training', 'injury mechanism')
    injury_data['Overuse/Trauma'] = extract_checkbox('overuse or trauma', 'onset', only_one=True)
    injury_data['Onset'] = extract_checkbox('gradual or sudden', 'contact', only_one=True)
    injury_data['Contact'] = extract_checkbox('contact', 'running/sprinting', only_one=True)
    injury_data['Action'] = extract_checkbox('indirect contact', 'injury mechanism')
    injury_data['Re-injury'] = extract_checkbox('re-injury', 'referee', only_one=True)
    injury_data['Referee Sanction'] = extract_checkbox('referee', 'diagnostic exam')
    injury_data['Diagnostic Examination'] = extract_checkbox('diagnostic exam', 'diagnosis', only_one=True)
    injury_data['Surgery'] = extract_checkbox('surgery', 'menstrual phase', only_one=True)
    injury_data['Menstrual Phase'] = extract_checkbox('menstrual phase', 'oral contraceptives', only_one=True)
    injury_data['Oral Contraceptives'] = extract_checkbox('oral contraceptives', 'hormonal contraceptives', only_one=True)
    injury_data['Hormonal Contraceptives'] = extract_checkbox('hormonal contraceptives', 'other information', only_one=True)
    
    # Action description and other comments as free-text inputs
    injury_data['Action Description'] = extract_text('player action', 'other information')
    injury_data['Diagnosis'] = extract_text('diagnosis', 'surgery')
    injury_data['Other Comments'] = extract_text('other comments', None)

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

    injury_data = extract_injury_form_data(docx_file)
    
    # Print to console
    print_injury_data(injury_data)