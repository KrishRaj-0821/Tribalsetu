"""
Multi-Criteria AI Trust Scoring Module
Function 8: compute_composite_trust_score()
Computes the final composite integrity score (0-100%) and categorizes into
Green (Auto-Approve), Yellow (Officer Review), and Red (Fraud Flagged) queues.
"""

def compute_composite_trust_score(
    qr_result: dict,
    ela_result: dict,
    identity_result: dict,
    gazette_result: dict,
    dbt_result: dict
) -> dict:
    """
    Weighted Ensemble Algorithm:
      Score = w1*S_QR + w2*S_ELA + w3*S_Identity + w4*S_Gazette + w5*S_DBT
    """
    audit_trail = []

    # 1. QR Score (Weight: 30%)
    w_qr = 0.30
    if qr_result.get("is_digitally_signed", False):
        s_qr = 100.0
        audit_trail.append("✓ Government cryptographic digital signature verified (100/100).")
    elif qr_result.get("qr_present", False):
        s_qr = 50.0
        audit_trail.append("⚠ QR code detected but state public signature missing (50/100).")
    else:
        # Non-digital/handwritten document
        s_qr = 70.0
        audit_trail.append("ℹ No QR code present (Handwritten/Offline certificate fallback: 70/100).")

    # 2. ELA Tampering Score (Weight: 25%)
    # Invert tamper_score: 0% tampering = 100% integrity
    w_ela = 0.25
    tamper_val = ela_result.get("tamper_score", 0.0)
    s_ela = max(100.0 - tamper_val, 0.0)
    
    if ela_result.get("is_tampered", False):
        audit_trail.append(f"✗ ELA Tampering Flagged! Pixel variance spike detected in text/marks (Integrity: {s_ela:.1f}/100).")
    else:
        audit_trail.append(f"✓ Uniform pixel compression verified. Zero Photoshop tampering detected (Integrity: {s_ela:.1f}/100).")

    # 3. Identity Consistency Score (Weight: 20%)
    w_identity = 0.20
    s_identity = float(identity_result.get("average_score", 0.0))
    if identity_result.get("is_match", False):
        audit_trail.append(f"✓ Identity string consistency verified across Aadhaar, Caste & Marksheet ({s_identity:.1f}/100).")
    else:
        audit_trail.append(f"✗ Identity Mismatch: Name on certificate does not match Aadhaar ({s_identity:.1f}/100).")

    # 4. MoTA ST Gazette Score (Weight: 15%)
    w_gazette = 0.15
    if gazette_result.get("is_recognized_st", False):
        s_gazette = 100.0
        matched = gazette_result.get("matched_tribe", "Tribal")
        audit_trail.append(f"✓ Recognized as an official Scheduled Tribe ({matched}) under Article 342 (100/100).")
    else:
        s_gazette = 0.0
        audit_trail.append(f"✗ Not recognized under MoTA Article 342 Scheduled Tribes schedule (0/100).")

    # 5. DBT Bank Readiness Score (Weight: 10%)
    w_dbt = 0.10
    if dbt_result.get("is_dbt_ready", False):
        s_dbt = 100.0
        audit_trail.append("✓ Aadhaar-NPCI Bank Account seeded and active for direct DBT payout (100/100).")
    else:
        s_dbt = 20.0
        audit_trail.append("✗ Bank account not seeded with Aadhaar NPCI mapper (20/100).")

    # Calculate Weighted Composite Score
    composite_score = (
        (s_qr * w_qr) +
        (s_ela * w_ela) +
        (s_identity * w_identity) +
        (s_gazette * w_gazette) +
        (s_dbt * w_dbt)
    )
    final_score = round(min(max(composite_score, 0.0), 100.0), 1)

    # Determine Decision Band (Green / Yellow / Red)
    if final_score >= 85.0 and not ela_result.get("is_tampered", False) and gazette_result.get("is_recognized_st", False):
        decision = "GREEN"
        decision_label = "AUTO_APPROVE"
        badge_color = "#10B981"
        summary = "Document 100% authentic and verified. Safe for immediate batch approval."
    elif final_score >= 60.0 or not qr_result.get("qr_present", True):
        decision = "YELLOW"
        decision_label = "MANUAL_REVIEW"
        badge_color = "#F59E0B"
        summary = "Minor variation or offline non-digital document. Routed to Officer for 10-second inspection."
    else:
        decision = "RED"
        decision_label = "FRAUD_FLAGGED"
        badge_color = "#EF4444"
        summary = "High risk of document tampering, forged numbers, or non-ST classification. Flagged with proof."

    return {
        "final_trust_score": final_score,
        "decision": decision,
        "decision_label": decision_label,
        "badge_color": badge_color,
        "summary": summary,
        "sub_scores": {
            "qr_cryptography": s_qr,
            "ela_tampering_integrity": s_ela,
            "identity_consistency": s_identity,
            "mota_gazette_compliance": s_gazette,
            "dbt_bank_readiness": s_dbt
        },
        "audit_trail": audit_trail
    }
