   # Normalize dates to ISO (YYYY-MM-DD). If INJURY_DATE can't be parsed, warn and skip the file.
import re
from datetime import datetime

def parse_date_to_iso(date_str):
    try:
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
    except Exception as e:
        return "Wrong date format"