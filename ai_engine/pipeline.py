"""
Master AI Pipeline Controller
Orchestrates Functions 1 through 8 in an end-to-end automated sequence.
"""

import cv2
import numpy as np
from ai_engine.preprocessor import preprocess_and_deskew
from ai_engine.ela_tamper import detect_tampering_ela
from ai_engine.qr_engine import scan_and_verify_qr
from ai_engine.ocr_engine import extract_document_fields
from ai_engine.st_gazette import st_validator
from ai_engine.identity_matcher import cross_match_identity
from ai_engine.dbt_checker import check_dbt_seeding_status
from ai_engine.trust_scorer import compute_composite_trust_score

def run_verification_pipeline(
    caste_doc_bytes: bytes,
    applicant_name: str,
    aadhaar_no: str,
    caste_name: str = "",
    state: str = "jharkhand",
    father_name: str = "",
    marksheet_name: str = ""
) -> dict:
    """
    Runs the full 8-function AI auditing pipeline on an uploaded certificate.
    """
    # 1. Preprocess and Deskew
    enhanced_cv2, compressed_bytes = preprocess_and_deskew(caste_doc_bytes)

    # 2. ELA Tampering Forensics
    ela_result = detect_tampering_ela(caste_doc_bytes)

    # 3. QR Code Digital Signature Verification
    qr_result = scan_and_verify_qr(enhanced_cv2)

    # 4. OCR & Structured Fields Extraction
    # If QR has official text, use as high-confidence context
    qr_data = qr_result.get("official_data") or {}
    context_text = f"Name: {qr_data.get('name', '')} Caste: {qr_data.get('caste', '')} Certificate No: {qr_data.get('cert_no', '')}"
    ocr_result = extract_document_fields(enhanced_cv2, fallback_text=context_text)

    # Prioritize extracted/verified values
    doc_applicant = qr_data.get("name") or ocr_result.get("applicant_name") or applicant_name
    doc_caste = qr_data.get("caste") or ocr_result.get("tribe_name") or caste_name
    doc_father = qr_data.get("father_name") or ocr_result.get("father_name") or father_name

    # 5. MoTA Article 342 ST Gazette Validation
    gazette_result = st_validator.validate_tribe(doc_caste, state=state)

    # 6. Identity Cross-Matching
    identity_result = cross_match_identity(
        aadhaar_name=applicant_name,
        caste_doc_name=doc_applicant,
        marksheet_name=marksheet_name or applicant_name,
        aadhaar_father=father_name,
        caste_father=doc_father
    )

    # 7. DBT Seeding Status Verification
    dbt_result = check_dbt_seeding_status(aadhaar_no)

    # 8. Composite AI Trust Score
    trust_score_result = compute_composite_trust_score(
        qr_result=qr_result,
        ela_result=ela_result,
        identity_result=identity_result,
        gazette_result=gazette_result,
        dbt_result=dbt_result
    )

    return {
        "applicant_name": applicant_name,
        "verified_tribe": doc_caste,
        "state": state,
        "is_st_verified": gazette_result.get("is_recognized_st", False),
        "trust_score": trust_score_result["final_trust_score"],
        "decision": trust_score_result["decision"],
        "decision_label": trust_score_result["decision_label"],
        "badge_color": trust_score_result["badge_color"],
        "summary": trust_score_result["summary"],
        "sub_scores": trust_score_result["sub_scores"],
        "audit_trail": trust_score_result["audit_trail"],
        "ela_forensics": {
            "is_tampered": ela_result["is_tampered"],
            "tamper_score": ela_result["tamper_score"],
            "explanation": ela_result["explanation"],
            "heatmap_base64": ela_result["heatmap_base64"]
        },
        "qr_verification": qr_result,
        "identity_verification": identity_result,
        "dbt_status": dbt_result,
        "extracted_fields": ocr_result
    }
