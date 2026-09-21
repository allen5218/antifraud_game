from app.api.routes.certificate import generate_certificate_data


def test_generate_certificate_data_fields():
    cert = generate_certificate_data(
        user_id_str="user-12345",
        user_name="李大專",
        level=3,
        d_prime=2.94,
        criterion_c=0.04,
        brier_score=0.061,
    )
    assert cert.certificate_id.startswith("AGY-CERT-")
    assert cert.user_name == "李大專"
    assert len(cert.hash_signature) == 16
    assert cert.pr_rank >= 95.0
    assert cert.status == "verified_active"
    assert cert.far_transfer_multiplier == 1.38
    assert len(cert.pedagogy_endorsements) == 4
    assert any("McGuire" in e for e in cert.pedagogy_endorsements)
    assert any("Kahneman" in e for e in cert.pedagogy_endorsements)
    assert any("Lichtenstein" in e for e in cert.pedagogy_endorsements)


def test_certificate_hash_signature_deterministic():
    cert1 = generate_certificate_data("u-1", "Name", d_prime=2.5, brier_score=0.1)
    cert2 = generate_certificate_data("u-1", "Name", d_prime=2.5, brier_score=0.1)
    assert cert1.hash_signature == cert2.hash_signature
    assert cert1.certificate_id == cert2.certificate_id


def test_diagnostic_dossier_structure():
    from app.api.routes.certificate import get_diagnostic_dossier
    from unittest.mock import MagicMock
    mock_user = MagicMock()
    mock_user.id = "mock-uuid-999"
    mock_user.full_name = "特級搜查官"
    mock_user.email = "officer@collegiate.edu.tw"

    dossier = get_diagnostic_dossier(current_user=mock_user)
    assert dossier.dossier_id.startswith("AGY-DOSSIER-")
    assert dossier.student_name == "特級搜查官"
    assert len(dossier.longitudinal_metrics) == 4
    assert len(dossier.pedagogy_conclusions) == 4
    assert dossier.ebbinghaus_days_halflife > 20.0
    assert len(dossier.cryptographic_fingerprint) == 24

