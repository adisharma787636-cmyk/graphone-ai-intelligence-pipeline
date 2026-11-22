
from src.services.llm_manager import (
    call_provider_with_retry,
    split_text_semantically,
    extract_with_chunking,
)

from src.services.extraction_schema import (
    AIEntity,
    ExtractionResult,
)


class SimulatedAPIError(Exception):
    def __init__(self, status_code):
        super().__init__(f"Simulated HTTP {status_code}")
        self.status_code = status_code


def test_413_chunking():
    print("\nTEST 1: HTTP 413 semantic chunking")

    text = "Artificial intelligence processes data. " * 1000

    chunks = split_text_semantically(
        text,
        max_chars=500,
        overlap_chars=50,
    )

    assert len(chunks) > 1
    assert all(len(chunk) <= 500 for chunk in chunks)

    print("PASS: Text split into", len(chunks), "valid chunks.")


def test_429_retry():
    print("\nTEST 2: HTTP 429 retry")

    attempts = {"count": 0}

    def simulated_provider(text):
        attempts["count"] += 1

        if attempts["count"] < 3:
            raise SimulatedAPIError(429)

        return "SUCCESS"

    result = call_provider_with_retry(
        simulated_provider,
        "Test input",
    )

    assert result == "SUCCESS"
    assert attempts["count"] == 3

    print("PASS: Retry succeeded after", attempts["count"], "attempts.")


def test_413_end_to_end():
    print("\nTEST 3: HTTP 413 end-to-end extraction")

    provider_calls = {"count": 0}

    def simulated_provider(text):
        provider_calls["count"] += 1

        # Match the manager's actual default chunk size.
        if len(text) > 8000:
            raise SimulatedAPIError(413)

        return ExtractionResult(
            entities=[
                AIEntity(
                    entity_type="ai_product",
                    name="SmartWriter",
                    description="AI writing assistant",
                ),
                AIEntity(
                    entity_type="startup",
                    name="TechNova AI",
                ),
            ]
        )

    # Ensure the input is larger than 8000 characters.
    large_text = (
        "Artificial intelligence startup and product information. "
        * 1000
    )

    result = extract_with_chunking(
        simulated_provider,
        large_text,
    )

    names = [
        entity.name
        for entity in result.entities
    ]

    assert provider_calls["count"] > 1
    assert "SmartWriter" in names
    assert "TechNova AI" in names

    assert names.count("SmartWriter") == 1
    assert names.count("TechNova AI") == 1

    print("Provider calls:", provider_calls["count"])
    print("Merged entities:", names)
    print("PASS: Chunk extraction and duplicate merging worked.")


if __name__ == "__main__":
    test_413_chunking()
    test_429_retry()
    test_413_end_to_end()

    print("\nALL THREE RELIABILITY TESTS PASSED")
