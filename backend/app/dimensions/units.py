import re
from typing import List, Tuple, Optional

def parse_single_value(text: str) -> Tuple[Optional[float], float]:
    """
    Parse a single dimension string (no 'x' or 'by') into mm.
    Returns (value_in_mm, parse_confidence).
    """
    text = text.strip().lower()
    
    # 1. Imperial formats (e.g. 12'-6", 12' 6", 12'6", 12'-6, 10'-0", 12.5', 10.25")
    # Matches <feet>' [optional - or space] <inches>[" or nothing]
    imperial_match = re.match(r"^(\d+(?:\.\d+)?)\s*'\s*(?:-?\s*(\d+(?:\.\d+)?)\s*\"?)?$", text)
    if imperial_match:
        feet = float(imperial_match.group(1))
        inches = float(imperial_match.group(2)) if imperial_match.group(2) else 0.0
        return (feet * 304.8) + (inches * 25.4), 0.98

    # Matches standalone inches: 10.25"
    inch_match = re.match(r"^(\d+(?:\.\d+)?)\s*\"$", text)
    if inch_match:
        inches = float(inch_match.group(1))
        return inches * 25.4, 0.98
        
    # 2. Metric formats with units
    # Matches <number> <mm|cm|m>
    metric_match = re.match(r"^(\d+(?:\.\d+)?)\s*(mm|cm|m)$", text)
    if metric_match:
        val = float(metric_match.group(1))
        unit = metric_match.group(2)
        if unit == 'mm':
            return val, 0.98
        elif unit == 'cm':
            return val * 10.0, 0.95
        elif unit == 'm':
            return val * 1000.0, 0.95
            
    # 3. Pure number (no unit)
    # Architectural default is often mm. If it's a small decimal (e.g., 3.5), it might be meters.
    num_match = re.match(r"^(\d+(?:\.\d+)?)$", text)
    if num_match:
        val = float(num_match.group(1))
        # Determine confidence based on value heuristics (very simple for now)
        if "." in text:
            # e.g., 3.5 -> 3500 mm assuming meters, but could be inches.
            # Without unit, it's ambiguous. Let's return as mm (if it's already mm) 
            # OR if it's < 100 with a decimal, it's highly likely meters in metric plans.
            if val < 50.0:
                return val * 1000.0, 0.60
            return val, 0.70
        else:
            # integer, probably mm
            return val, 0.85
            
    return None, 0.0

def parse_dimension_string(text: str) -> Tuple[List[float], float]:
    """
    Parse a potentially compound dimension string into a list of mm values.
    E.g. "12' x 10'" -> [3657.6, 3048.0], "4200" -> [4200.0]
    Returns (values_in_mm, overall_parse_confidence)
    """
    # Check for 'x' or 'X' or '*' as a separator for compound dimensions
    # Also handle possible spaces
    parts = re.split(r'\s*[xX\*]\s*', text.strip())
    
    # If no 'x' was found, it might be a chained dimension separated by spaces (e.g. '1200 2500 1800')
    if len(parts) == 1 and ' ' in text.strip() and not re.match(r'^.*[\'\"mcmmm]\s*$', text.strip().lower()):
        # Try to split by spaces, but be careful not to split "12' 6"" or "3.5 m"
        space_parts = re.split(r'\s+', text.strip())
        valid_space_parts = []
        confs = []
        for sp in space_parts:
            v, c = parse_single_value(sp)
            if v is not None:
                valid_space_parts.append(v)
                confs.append(c)
        if len(valid_space_parts) == len(space_parts) and len(space_parts) > 1:
            # It's a chained dimension!
            return valid_space_parts, sum(confs) / len(confs)
            
    values = []
    confidences = []
    
    for part in parts:
        if not part.strip():
            continue
        val, conf = parse_single_value(part)
        if val is not None:
            values.append(val)
            confidences.append(conf)
            
    if not values:
        return [], 0.0
        
    avg_conf = sum(confidences) / len(confidences)
    
    # If it was split but some parts failed, penalize
    if len(values) < len(parts):
        avg_conf *= (len(values) / len(parts))
        
    return values, avg_conf
