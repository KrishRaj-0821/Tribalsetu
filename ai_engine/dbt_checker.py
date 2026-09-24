"""
NPCI Aadhaar Payment Bridge (APB) & DBT Validator
Function 7: check_dbt_seeding_status()
Simulates the National Payments Corporation of India (NPCI) gateway to verify
if the student's bank account is active and seeded with Aadhaar for Direct Benefit Transfer (DBT).
"""

import hashlib

def check_dbt_seeding_status(aadhaar_number: str) -> dict:
    """
    Queries NPCI Aadhaar-Bank Mapper to verify DBT readiness.
    Prevents post-approval payment rejections by warning students in advance.
    """
    clean_aadhaar = str(aadhaar_number).replace(" ", "").replace("-", "")
    
    if len(clean_aadhaar) < 12:
        return {
            "is_dbt_ready": False,
            "status": "INVALID_AADHAAR",
            "bank_name": None,
            "account_last4": None,
            "mandate_date": None,
            "alert_message": "Invalid Aadhaar number entered. Please enter a 12-digit Aadhaar number."
        }

    # Deterministic simulation based on hash of Aadhaar
    # In test scenarios, aadhaars ending in '00' simulate unseeded accounts
    h = int(hashlib.md5(clean_aadhaar.encode()).hexdigest(), 16)
    
    banks = [
        "State Bank of India",
        "Punjab National Bank",
        "Bank of India",
        "Canara Bank",
        "Jharkhand Rajya Gramin Bank",
        "Odisha Gramya Bank",
        "Central Bank of India"
    ]
    
    bank_idx = h % len(banks)
    assigned_bank = banks[bank_idx]
    account_suffix = str(1000 + (h % 9000))

    # Test edge-case: If user tests with Aadhaar ending in '0000', simulate unlinked DBT
    if clean_aadhaar.endswith("0000"):
        return {
            "is_dbt_ready": False,
            "status": "DBT_NOT_SEEDED",
            "bank_name": assigned_bank,
            "account_last4": account_suffix,
            "mandate_date": None,
            "alert_message": f"WARNING: Your bank account ({assigned_bank}) is NOT seeded with Aadhaar NPCI mapper. Scholarship funds will bounce! Please submit an Aadhaar seeding form at your bank branch before submitting."
        }

    return {
        "is_dbt_ready": True,
        "status": "ACTIVE_SEEDED",
        "bank_name": assigned_bank,
        "account_last4": account_suffix,
        "mandate_date": "14-Jan-2024",
        "alert_message": f"Verified: Bank account ({assigned_bank} ending in ****{account_suffix}) is ACTIVE and NPCI DBT-enabled. Direct funds will credit smoothly."
    }
