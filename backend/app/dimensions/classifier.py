import re
from typing import List

def classify_dimension(raw_text: str, values: List[float], parse_confidence: float) -> str:
    """
    Classify a string into one of:
    DIMENSION, ROOM_DIMENSION, NUMERIC_ANNOTATION, TEXT, UNKNOWN
    """
    text = raw_text.strip()
    text_upper = text.upper()
    
    # 1. Text checks
    if re.search(r'[a-zA-Z]{3,}', text) and not re.search(r'\d', text):
        return "TEXT"
        
    # Check for typical non-dimension annotations like "ROOM 204" or "A-102"
    if re.search(r'ROOM|BEDROOM|BATH|LIVING|KITCHEN', text_upper):
        return "TEXT"
        
    if re.match(r'^[A-Z]\s*-\s*\d+$', text_upper):
        return "NUMERIC_ANNOTATION" # e.g. A-102
        
    # 2. If it parsed multiple values, it's a compound dimension
    if len(values) >= 2:
        return "ROOM_DIMENSION"
        
    # 3. Single value logic
    if len(values) == 1:
        if parse_confidence >= 0.90:
            # Strong unit indicator (mm, ', ", etc)
            return "DIMENSION"
            
        # Weak indicator (just a number)
        # Check if it looks like a year or small annotation
        if re.match(r'^\d{1,3}$', text):
            # very small integer, unlikely a millimeter dimension for a wall unless cm is assumed
            return "NUMERIC_ANNOTATION"
            
        if re.match(r'^(19|20)\d{2}$', text):
            # looks like a year
            return "NUMERIC_ANNOTATION"
            
        # Standard wall lengths are usually 1000+, or ends with 0 or 5
        if re.match(r'^\d+$', text):
            val = int(text)
            if val >= 500 and (val % 5 == 0):
                return "DIMENSION"
            return "NUMERIC_ANNOTATION"
            
        return "DIMENSION" # Fallback if it has a decimal and parse_confidence > 0
        
    # 4. Unknown or unable to parse
    if re.search(r'\d', text):
        return "NUMERIC_ANNOTATION"
        
    return "UNKNOWN"
