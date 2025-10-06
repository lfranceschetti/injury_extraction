import zipfile
import xml.dom.minidom as minidom
import sys
import re
import xml.etree.ElementTree as ET
from datetime import datetime


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

    # Precompute paragraphs and their texts once
    paragraphs = list(root.findall('.//w:p', namespaces))
    para_texts = [''.join([t.text for t in p.findall('.//w:t', namespaces) if t.text]) for p in paragraphs]

    # Small helpers to DRY up repeated patterns
    def get_text_display_from_runs(runs, start_idx):
        """Return displayed text for a FORMTEXT field that begins at runs[start_idx]."""
        text_value = ""
        found_separate = False
        for j in range(start_idx + 1, len(runs)):
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
        return text_value.strip()

    def find_section_bounds(start_marker, end_marker):
        start_idx_local = None
        end_idx_local = None
        for idx, text in enumerate(para_texts):
            lowered = (text or '').lower()
            if start_idx_local is None and start_marker in lowered:
                start_idx_local = idx
            elif start_idx_local is not None and end_marker and end_marker in lowered:
                end_idx_local = idx
                break
        return start_idx_local, end_idx_local
    

    injury_data_names = [
        "NAME",
        "TEAM",
        "CODE",
        "INJURY_DATE",
        "RETURN_DATE",
        "INJURY_LOCATION",
        "INJURY_SIDE",
        "INJURY_TYPE",
        "OCCURRENCE",
        "OVERUSE_TRAUMA",
        "ONSET",
        "CONTACT",
        "ACTION",
        "ACTION_DESCRIPTION",
        "RE_INJURY",
        "REFEREE_SANCTION",
        "DIAGNOSTIC_EXAMINATION",
        "DIAGNOSIS",
        "SURGERY",
        "MENSTRUAL_PHASE",
        "ORAL_CONTRACEPTIVES",
        "HORMONAL_CONTRACEPTIVES",
        "OTHER_COMMENTS"
    ]

    injury_data = {name: "" for name in injury_data_names}

    
    
    # Extract text fields (FORMTEXT)
    text_fields = {}
    
    # Build a map of all text input fields and their displayed values
    for para in paragraphs:
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
                    if text_input is not None and field_name:
                        text_fields[field_name] = get_text_display_from_runs(elements, i)
    
    para_texts = []
    checkboxes = {}
    # Keep ordered entries with paragraph indices for section-scoped extraction
    checkbox_entries = []
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
                                    following_text = get_text_display_from_runs(elements, j)
                                    break
                                # If another field begins but it's not a text input, stop looking further in this paragraph
                                break
                        
                        if field_name or label:
                            key = field_name if field_name else label
                            entry = {'checked': is_checked, 'label': label.strip(), 'para_idx': para_idx, 'following_text': following_text}
                            checkboxes[key] = {'checked': is_checked, 'label': label.strip()}
                            checkbox_entries.append(entry)
    
     
    # Helper to collect checked labels between two section headers
    def extract_checkbox(start_marker, end_marker, only_one=False):
        start_idx_local, end_idx_local = find_section_bounds(start_marker, end_marker)
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
                    elif entry["label"] and entry["label"].strip().startswith("Yes") and not entry.get('following_text'):
                        label_text = "Yes"
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
        start_idx_local, end_idx_local = find_section_bounds(start_marker, end_marker)
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


    injury_data['NAME'] = extract_text('name', 'team')
    injury_data['TEAM'] = extract_text('team', 'code')
    injury_data['CODE'] = extract_text('code', 'date of injury')
    injury_date = extract_text('date of injury', 'date of return to full participation')
    return_date = extract_text('date of return to full participation', 'injury location')

    # Normalize dates to ISO (YYYY-MM-DD). If INJURY_DATE can't be parsed, warn and skip the file.
    def parse_date_to_iso(date_str):
        s = (date_str or '').strip()
        if not s:
            return ''
        # Already ISO?
        try:
            dt = datetime.strptime(s, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        except Exception:
            pass
        # Try common day-first formats and a few others
        candidates = [
            '%d-%m-%Y', '%d/%m/%Y', '%d.%m.%Y', '%d %m %Y',
            '%d %b %Y', '%d %B %Y',
            '%Y/%m/%d', '%Y.%m.%d',
            '%m/%d/%Y', '%m-%d-%Y',  # fallbacks if someone used US ordering
        ]
        for fmt in candidates:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime('%Y-%m-%d')
            except Exception:
                continue
        # Last resort: try extracting digits and reinterpreting dd-mm-yyyy like strings with mixed separators
        m = re.match(r'^(\d{1,2})[\./\-](\d{1,2})[\./\-](\d{2,4})$', s)
        if m:
            d, mo, y = m.groups()
            if len(y) == 2:
                y = '20' + y
            try:
                dt = datetime(int(y), int(mo), int(d))
                return dt.strftime('%Y-%m-%d')
            except Exception:
                pass
        raise ValueError(f"Unrecognized date format: '{s}'")

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