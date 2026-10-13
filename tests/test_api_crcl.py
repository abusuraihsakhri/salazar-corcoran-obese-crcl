"""FastAPI calculation contract and mock provider regression."""
import pytest
from fastapi import HTTPException
from agents.api import CrClRequest, api_crcl
from agents.llm_factory import LLMFactory

def test_crcl_endpoint_reference():
    payload = CrClRequest(sex="male", age_years=45, weight_kg=120,
                          height_m=1.75, serum_creatinine_mg_dl=1.2)
    assert api_crcl(payload)["creatinine_clearance_ml_min"] == 107.12

def test_crcl_endpoint_invalid_input():
    payload = CrClRequest(sex="male", age_years=45, weight_kg=120,
                          height_m=1.75, serum_creatinine_mg_dl=0)
    with pytest.raises(HTTPException) as exc:
        api_crcl(payload)
    assert exc.value.status_code == 422

def test_unsupported_provider_cannot_fake_inference():
    with pytest.raises(ValueError, match="not implemented"):
        LLMFactory.create("openai")
