import zipfile
import xml.dom.minidom as minidom
import sys
import re
import xml.etree.ElementTree as ET
from datetime import datetime

namespaces = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'w14': 'http://schemas.microsoft.com/office/word/2010/wordml'
}
    

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

def find_section_bounds(para_texts, start_marker, end_marker=None, num_paragraphs=None):
    if num_paragraphs is None and end_marker is None:
        raise ValueError("Either end_marker or num_paragraphs must be provided")
    
    start_idx_local = None
    end_idx_local = None
    start_marker_lower = start_marker.lower() if start_marker else None
    end_marker_lower = end_marker.lower() if end_marker else None
    
    for idx, text in enumerate(para_texts):
        lowered = (text or '').lower()
        if start_idx_local is None and start_marker_lower and start_marker_lower in lowered:
            start_idx_local = idx
        elif start_idx_local is not None and end_marker_lower and end_marker_lower in lowered:
            end_idx_local = idx
            break
    if num_paragraphs is not None and start_idx_local is not None:
        end_idx_local = start_idx_local + num_paragraphs + 1
    return start_idx_local, end_idx_local

def extract_form_fields(root, paragraphs, namespaces):
    """
    Extract all form fields (text inputs and checkboxes) from Word document XML.
    
    Args:
        root: XML root element
        paragraphs: List of paragraph elements
        namespaces: XML namespace dictionary
        
    Returns:
        tuple: (text_fields dict, checkbox_entries list, para_texts list)
    """
    from helpers.word import get_text_display_from_runs
    
    # Build a map of all text input fields and their displayed values
    text_fields = {}
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
                        
                        # Get the label text that follows the checkbox
                        label = ""
                        for j in range(i + 1, len(elements)):
                            next_run = elements[j]
                            if next_run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces) is not None:
                                break
                            text_elem = next_run.find('.//w:t', namespaces)
                            if text_elem is not None and text_elem.text:
                                label += text_elem.text
                        label = (label or "").strip()
                        
                        # If the label is suspiciously short, append next paragraph text
                        if (not label) or len(label) <= 2:
                            if para_idx + 1 < len(para_texts):
                                next_para_text = (para_texts[para_idx + 1] or "").strip()
                                if next_para_text:
                                    prefix = next_para_text[:30]
                                    label = (label + prefix).strip()
                        
                        # Capture following text field content
                        following_text = ""
                        for j in range(i + 1, len(elements)):
                            next_run = elements[j]
                            fld_begin_ahead = next_run.find('.//w:fldChar[@w:fldCharType="begin"]', namespaces)
                            if fld_begin_ahead is not None:
                                ffdata_ahead = fld_begin_ahead.find('.//w:ffData', namespaces)
                                if ffdata_ahead is not None and ffdata_ahead.find('.//w:textInput', namespaces) is not None:
                                    following_text = get_text_display_from_runs(elements, j)
                                    break
                                break
                        
                        if field_name or label:
                            key = field_name if field_name else label
                            entry = {'checked': is_checked, 'label': label.strip(), 'para_idx': para_idx, 'following_text': following_text}
                            checkboxes[key] = {'checked': is_checked, 'label': label.strip()}
                            checkbox_entries.append(entry)
    
    return text_fields, checkbox_entries, para_texts