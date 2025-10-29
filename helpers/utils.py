def get_form_type(text: str) -> str:
    """
    Determine the form type based on text content.
    
    Args:
        text: The text content to analyze (can be full text or joined paragraphs)
        
    Returns:
        Form type: "HEAD", "ILLNESS", "INJURY", "LOWER_EXTREMITIES", "KNEE", or "UNKNOWN"
    """
    if "Location of impact on head and/or body" in text:
        return "HEAD"
    elif "Type of illness" in text:
        return "ILLNESS"
    elif "Injury location" in text:
        return "INJURY"
    elif "Location of injury (Check all that may apply)" in text:
        return "LOWER_EXTREMITIES"
    elif "Combination of injuries" in text:
        return "KNEE"
    
    return "UNKNOWN"