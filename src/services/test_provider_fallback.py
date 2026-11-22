
from src.services import llm_manager


def simulate_gemini_failure(source_text):
    print("\nSimulating Gemini failure...")
    raise RuntimeError("Simulated Gemini API failure")


sample_text = """
TechNova AI is an artificial intelligence startup.

It develops SmartWriter, an AI writing assistant
that helps users create articles and business documents.

Website: https://example.com
"""

# Replace Gemini with a controlled failure.
# Keep the real Groq extraction function.
llm_manager.PROVIDERS = [
    {
        "name": "Gemini_TEST_FAILURE",
        "function": simulate_gemini_failure,
    },
    {
        "name": "Groq",
        "function": llm_manager.groq_extract_entities,
    },
]

print("\nAUTOMATIC PROVIDER FALLBACK TEST")
print("=" * 50)

result = llm_manager.extract_with_fallback(sample_text)

print("\nFINAL TEST RESULT")
print("=" * 50)
print("Success:", result["success"])
print("Selected provider:", result["provider"])
print("Recorded failures:", result["errors"])

if result["success"] and result["provider"] == "Groq":
    print("\nPASS: Automatic fallback to Groq worked.")
else:
    print("\nFAIL: Automatic fallback did not work.")
