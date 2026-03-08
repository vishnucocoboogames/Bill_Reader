from typing import Tuple, List, Dict, Any

class ValidationService:
    def __init__(self, static_fields: List[str] = None):
        # We check the specific mapped keys extracted by the file parser
        self.static_fields = static_fields or (
            # --- Table 1: Meter Config (specific rows from column D) ---
            ["cfg_R5", "cfg_R13", "cfg_R64", "cfg_R66", "cfg_R67", "cfg_R68", "cfg_R121"] +
            # --- Table 3: Bill Parameters (L5:L19) ---
            [
                "Cno",            # Consumer Number
                "Cname",          # Consumer Name
                "Caddress",       # Consumer address
                "Eduty",          # Electricity Duty
                "GST",            # GST No
                "CntdLoad",       # Connected Load
                "CnnDate",        # Connection Date
                "Fsrcharge",      # Fuel Surcharge
                "FxdCharge",      # Fixed Charge
                "gstper",         # GST %
                "lowvsurcharge",  # Low Voltage Surcharge
                "KFC",            # KFC%
                "Communication Charges / Meter Hire"
            ]
        )
        
    def validate_consumer_records(self, prev_data: Dict[str, Any], curr_data: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Compares data dictionaries to validate static fields and reading continuity.
        Returns (is_valid, reason)
        """
        if not prev_data or not curr_data:
            return False, "Data extraction resulted in empty records."

        # 1. Compare static fields
        for field in self.static_fields:
            prev_val = prev_data.get(field)
            curr_val = curr_data.get(field)
            
            # Normalize strings for comparison (strip whitespace, normalize to string)
            prev_norm = str(prev_val).strip().lower() if prev_val is not None else ""
            curr_norm = str(curr_val).strip().lower() if curr_val is not None else ""
            
            if prev_norm != curr_norm:
                return False, f"Static field mismatch on '{field}': Expected {prev_val}, Got {curr_val}"

        # 2. Compare continuity of readings for Normal, Peak, Offpeak
        reading_pairs = [
            ("Normal -FR", "Normal-IR"),
            ("Peak-FR", "Peak-IR"),
            ("Offpeak-FR", "Offpeak-IR")
        ]

        for prev_key, curr_key in reading_pairs:
            prev_val = prev_data.get(prev_key)
            curr_val = curr_data.get(curr_key)

            if prev_val is None or curr_val is None:
                return False, f"Missing reading values ('{prev_key}' or '{curr_key}') for continuity check."

            try:
                # Float conversion handles numeric differences correctly
                prev_val_float = float(prev_val)
                curr_val_float = float(curr_val)
                
                # Excel often rounds visible numbers to 2 decimal places (e.g., 3033620.11) 
                # while storing the backend float at full precision (e.g., 3033620.105).
                # We add a small tolerance to ignore these floating point mismatches.
                if abs(prev_val_float - curr_val_float) > 0.05:
                    return False, f"Reading mismatch on {prev_key[:-3]}: Previous FR={prev_val_float}, Current IR={curr_val_float}"
                    
            except ValueError:
                return False, f"Non-numeric reading values encountered for '{prev_key}' or '{curr_key}'."

        return True, "Valid"
