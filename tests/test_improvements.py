"""
Tests for security, reliability, and validation improvements.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import os
import warnings
from salazar_corcoran import calculate_metrics, process_batch
from agents.base import AuditTrail, PHIGuard, SecurityException


class TestCalculateMetricsValidation:
    """The domain algorithm must return CrCl, not an arbitrary risk tier."""

    @pytest.mark.parametrize("bad", [
        {"weight_kg": float("nan")}, {"height_m": float("inf")},
        {"serum_creatinine_mg_dl": 0}, {"age_years": -1}, {"sex": "invalid"},
    ])
    def test_reject_invalid(self, bad):
        values = dict(sex="male", age_years=45, weight_kg=120,
                      height_m=1.75, serum_creatinine_mg_dl=1.2)
        values.update(bad)
        with pytest.raises(ValueError):
            calculate_metrics(**values)

    def test_reference_value(self):
        result = calculate_metrics(sex="male", age_years=45, weight_kg=120,
                                   height_m=1.75, serum_creatinine_mg_dl=1.2)
        assert result["creatinine_clearance_ml_min"] == 107.12


class TestProcessBatchErrorHandling:
    def test_missing_file(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "missing.csv"), str(tmp_path / "out.csv"))

    def test_empty_csv(self, tmp_path):
        source = tmp_path / "empty.csv"
        source.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty or has no headers"):
            process_batch(str(source), str(tmp_path / "out.csv"))

    def test_valid_csv(self, tmp_path):
        source, target = tmp_path / "in.csv", tmp_path / "out.csv"
        source.write_text("case_id,sex,age_years,weight_kg,height_m,serum_creatinine_mg_dl\n"
                          "PT-001,male,45,120,1.75,1.2\n", encoding="utf-8")
        assert process_batch(str(source), str(target)) == 1
        assert "107.12" in target.read_text(encoding="utf-8")


class TestAuditTrailSecurity:
    """Test security improvements in AuditTrail."""

    def test_no_hardcoded_default_key(self):
        """AuditTrail should not use a hardcoded default key."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            audit = AuditTrail()
            # Should warn about missing AUDIT_SECRET_KEY
            assert len(w) == 1
            assert "AUDIT_SECRET_KEY not set" in str(w[0].message)

    def test_ephemeral_key_generation(self):
        """Without AUDIT_SECRET_KEY, should generate ephemeral key."""
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            audit = AuditTrail()
            assert len(audit.secret_key) > 0

    def test_custom_key_works(self):
        """Custom key should work without warning."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            audit = AuditTrail(secret_key="test-key-123")
            assert len(w) == 0
            assert audit.secret_key == b"test-key-123"

    def test_audit_trail_integrity(self):
        """Audit trail should maintain integrity."""
        audit = AuditTrail(secret_key="test-key")
        audit.log("test", "tier", "event", {"data": "value"})
        audit.log("test", "tier", "event2", {"data": "value2"})
        assert audit.verify_integrity() is True

    def test_audit_trail_tamper_detection(self):
        """Tampered audit trail should fail integrity check."""
        audit = AuditTrail(secret_key="test-key")
        audit.log("test", "tier", "event", {"data": "value"})
        audit.log("test", "tier", "event2", {"data": "value2"})
        # Tamper with the prev_hash chain in the second entry
        audit.logs[1]["prev_hash"] = "tampered_hash_value"
        assert audit.verify_integrity() is False


class TestPHIGuard:
    """Test PHI guard functionality."""

    def test_blocks_mrn(self):
        """Should block MRN patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Patient MRN-12345678")

    def test_blocks_ssn(self):
        """Should block SSN patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("SSN: 123-45-6789")

    def test_blocks_phone(self):
        """Should block phone number patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Call 555-123-4567")

    def test_blocks_email(self):
        """Should block email patterns."""
        with pytest.raises(SecurityException):
            PHIGuard.assert_no_phi("Email: patient@example.com")

    def test_allows_clean_text(self):
        """Should allow clean text without PHI."""
        PHIGuard.assert_no_phi("Analytical assay specimen KEY-001 optimal")

    def test_allows_empty_string(self):
        """Should allow empty string."""
        PHIGuard.assert_no_phi("")

    def test_allows_none(self):
        """Should allow None."""
        PHIGuard.assert_no_phi(None)
