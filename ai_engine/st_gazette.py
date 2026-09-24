"""
Ministry of Tribal Affairs (MoTA) ST Gazette Validator
Function 5: validate_st_gazette()
Validates if a claimed tribe is recognized under Article 342 of the Constitution of India.
"""

import json
from pathlib import Path
from thefuzz import fuzz

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "st_tribes_gazette.json"

class STGazetteValidator:
    def __init__(self, gazette_file: Path = DATA_PATH):
        self.gazette = {}
        if gazette_file.exists():
            with open(gazette_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.gazette = data.get("states", {})

    def validate_tribe(self, tribe_name: str, state: str = "jharkhand") -> dict:
        """
        Validates tribe name against recognized list for the specified state.
        Supports fuzzy matching for phonetic spelling variations (e.g., Santal vs Santhal).
        """
        if not tribe_name:
            return {
                "is_recognized_st": False,
                "confidence": 0,
                "official_tribe_name": None,
                "state": state,
                "message": "No tribe name provided for verification."
            }

        state_key = state.lower().replace(" ", "_")
        recognized_tribes = self.gazette.get(state_key, [])

        # If state not directly found, check all recognized tribes across India
        if not recognized_tribes:
            all_tribes = set()
            for t_list in self.gazette.values():
                all_tribes.update(t_list)
            recognized_tribes = list(all_tribes)

        target = tribe_name.lower().strip()
        best_match = None
        best_score = 0

        for rt in recognized_tribes:
            score = fuzz.ratio(target, rt.lower())
            if score > best_score:
                best_score = score
                best_match = rt

        # Match threshold of 80% handles minor phonetic spelling differences
        is_recognized = best_score >= 80

        return {
            "is_recognized_st": is_recognized,
            "confidence": best_score,
            "matched_tribe": best_match.capitalize() if best_match else None,
            "query_tribe": tribe_name,
            "state": state,
            "article_342_compliant": is_recognized,
            "message": f"Recognized as an official Scheduled Tribe ({best_match.capitalize()}) under Article 342 in {state.capitalize()}." if is_recognized else f"Tribe '{tribe_name}' not found in official Article 342 Scheduled Tribes schedule for {state.capitalize()}."
        }

# Global validator instance
st_validator = STGazetteValidator()
