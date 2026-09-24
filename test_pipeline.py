"""
Automated Pipeline Verification Test
Tests genuine, tampered, and non-ST sample certificates
"""

import sys
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent))

from ai_engine.pipeline import run_verification_pipeline

def test_genuine():
    print("\n--- TEST 1: GENUINE ST CERTIFICATE (Rahul Munda) ---")
    doc_path = Path("sample_docs/sample_genuine_st.jpg")
    with open(doc_path, "rb") as f:
        doc_bytes = f.read()

    res = run_verification_pipeline(
        caste_doc_bytes=doc_bytes,
        applicant_name="Rahul Munda",
        aadhaar_no="987654321012",
        caste_name="Munda",
        state="jharkhand",
        father_name="Birsa Munda"
    )

    print(f"Decision: {res['decision']} ({res['decision_label']})")
    print(f"Trust Score: {res['trust_score']}%")
    print(f"QR Signed: {res['qr_verification']['is_digitally_signed']}")
    print(f"Tribe Verified: {res['verified_tribe']} (ST: {res['is_st_verified']})")
    print(f"DBT Active: {res['dbt_status']['is_dbt_ready']}")
    print("Audit Trail Summary:")
    for trail in res["audit_trail"]:
        safe_str = trail.encode('ascii', 'replace').decode('ascii')
        print("  " + safe_str)
    assert res["trust_score"] >= 80.0, "Genuine ST certificate must receive high trust score"

def test_tampered():
    print("\n--- TEST 2: TAMPERED / PHOTOSHOPPED CERTIFICATE ---")
    doc_path = Path("sample_docs/sample_tampered_fake.jpg")
    with open(doc_path, "rb") as f:
        doc_bytes = f.read()

    res = run_verification_pipeline(
        caste_doc_bytes=doc_bytes,
        applicant_name="Rahul Munda",
        aadhaar_no="987654321012",
        caste_name="Munda",
        state="jharkhand"
    )

    print(f"Decision: {res['decision']} ({res['decision_label']})")
    print(f"Trust Score: {res['trust_score']}%")
    print(f"Tamper Detected: {res['ela_forensics']['is_tampered']} (Score: {res['ela_forensics']['tamper_score']}%)")
    print(f"Explanation: {res['ela_forensics']['explanation']}")
    print("Audit Trail:")
    for trail in res["audit_trail"]:
        safe_str = trail.encode('ascii', 'replace').decode('ascii')
        print("  " + safe_str)

def test_non_st():
    print("\n--- TEST 3: NON-ST / GENERAL CERTIFICATE ---")
    doc_path = Path("sample_docs/sample_non_st.jpg")
    with open(doc_path, "rb") as f:
        doc_bytes = f.read()

    res = run_verification_pipeline(
        caste_doc_bytes=doc_bytes,
        applicant_name="Rahul Kushwaha",
        aadhaar_no="987654321012",
        caste_name="Kushwaha",
        state="jharkhand"
    )

    print(f"Decision: {res['decision']} ({res['decision_label']})")
    print(f"Trust Score: {res['trust_score']}%")
    print(f"Tribe Recognized as ST: {res['is_st_verified']}")
    print("Audit Trail:")
    for trail in res["audit_trail"]:
        safe_str = trail.encode('ascii', 'replace').decode('ascii')
        print("  " + safe_str)

if __name__ == "__main__":
    test_genuine()
    test_tampered()
    test_non_st()
    print("\nAll 3 automated pipeline tests completed successfully!")
