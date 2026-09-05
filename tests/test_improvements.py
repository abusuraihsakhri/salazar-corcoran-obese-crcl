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
    """Test input validation in calculate_metrics."""

    def test_reject_nan_values(self):
        """NaN values should be rejected, not included in calculation."""
        res = calculate_metrics(v1=10.0, v2=float('nan'))
        assert res["score"] == 10.0
        assert res["inputs_evaluated"] == 1

    def test_reject_inf_values(self):
        """Infinity values should be rejected."""
        res = calculate_metrics(v1=10.0, v2=float('inf'))
        assert res["score"] == 10.0
        assert res["inputs_evaluated"] == 1

    def test_reject_negative_inf_values(self):
        """Negative infinity values should be rejected."""
        res = calculate_metrics(v1=10.0, v2=float('-inf'))
        assert res["score"] == 10.0
        assert res["inputs_evaluated"] == 1

    def test_normal_values_work(self):
        """Normal finite values should work correctly."""
        res = calculate_metrics(v1=10.0, v2=5.0)
        assert res["score"] == 12.5  # 10 + 5*(1/2)
        assert res["inputs_evaluated"] == 2

    def test_classification_low(self):
        """Score < 10 should be Low / Standard."""
        res = calculate_metrics(v1=5.0)
        assert res["classification"] == "Low / Standard"

    def test_classification_moderate(self):
        """Score 10-25 should be Moderate / Intermediate."""
        res = calculate_metrics(v1=15.0)
        assert res["classification"] == "Moderate / Intermediate"

    def test_classification_high(self):
        """Score >= 25 should be High / Severe."""
        res = calculate_metrics(v1=30.0)
        assert res["classification"] == "High / Severe"

    def test_string_values_ignored_for_numeric(self):
        """String values should not contribute to numeric score."""
        res = calculate_metrics(v1=10.0, name="test")
        assert res["score"] == 10.0
        assert res["inputs_evaluated"] == 2  # Both counted as inputs


class TestProcessBatchErrorHandling:
    """Test error handling in process_batch."""

    def test_file_not_found_raises_error(self, tmp_path):
        """Non-existent input file should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            process_batch(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))

    def test_empty_csv_raises_error(self, tmp_path):
        """Empty CSV file should raise ValueError."""
        csv_in = tmp_path / "empty.csv"
        csv_in.write_text("", encoding="utf-8")
        with pytest.raises(ValueError, match="empty or has no headers"):
            process_batch(str(csv_in), str(tmp_path / "out.csv"))

    def test_valid_batch_processing(self, tmp_path):
        """Valid batch should process correctly."""
        csv_in = tmp_path / "in.csv"
        csv_out = tmp_path / "out.csv"
        csv_in.write_text("Patient_ID,v1,v2\nPT-001,15.0,3.0\n", encoding="utf-8")
        process_batch(str(csv_in), str(csv_out))
        assert csv_out.exists()
        content = csv_out.read_text(encoding="utf-8")
        assert "PT-001" in content
        assert "score" in content


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
