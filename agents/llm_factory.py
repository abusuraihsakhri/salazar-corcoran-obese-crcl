"""Deterministic mock provider. Real external inference is not implemented."""
from .base import PHIGuard


class MockLLM:
    def __init__(self, system_name: str = "Salazar Corcoran Obese Crcl"):
        self.system_name = system_name

    def invoke(self, prompt: str) -> str:
        PHIGuard.assert_no_phi(prompt)
        return f"[{self.system_name} mock]: No model inference or clinical verification is performed."


class LLMFactory:
    """Only explicit mock mode is supported; never impersonate a provider."""

    @staticmethod
    def create(provider: str = "mock", system_name: str = "Salazar Corcoran Obese Crcl"):
        if str(provider).lower() in {"mock", "deterministic", "test"}:
            return MockLLM(system_name)
        raise ValueError(f"Model provider {provider!r} is not implemented; use mock mode")
