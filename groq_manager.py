from typing import List, Dict, Optional
import streamlit as st

try:
    from groq import Groq
    _HAS_GROQ_LIB = True
except Exception:
    Groq = None
    _HAS_GROQ_LIB = False


class GroqManager:
    """Wrapper around Groq LLM client and prompt management.

    Responsibilities:
    - Hold API key and connection checks
    - Provide a single `get_feedback` method that returns the model response
    - Store prompt templates in one place so they're easy to modify
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "llama-3.1-8b-instant", temperature: float = 0.0):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self._client = None

    def set_api_key(self, api_key: Optional[str]):
        self.api_key = api_key
        self._client = None

    def is_available(self) -> bool:
        return _HAS_GROQ_LIB and bool(self.api_key)

    def _ensure_client(self):
        if not _HAS_GROQ_LIB:
            raise RuntimeError("Groq SDK not installed")
        if not self.api_key:
            raise RuntimeError("Groq API key not set")
        if self._client is None:
            self._client = Groq(api_key=self.api_key)
        return self._client

    def _build_system_prompt(self) -> str:
        return (
            "You are an expert dialect/accent coach for American spoken English.\n"
            "Provide feedback to improve the speaker's American accent.\n"
            "Use Google pronunciation respelling when giving corrections.\n"
            "Provide the following sections:\n"
            "- Overall Impression\n"
            "- Specific Feedback\n"
            "- Google Pronunciation Respelling Suggestions\n"
            "- Additional Tips"
        )

    def _build_user_prompt(self, reference_text: str, per_word_comparison: List[Dict]) -> str:
        diff = "\n".join(
            f"{item['word']}: expected={item['ref_phonemes']}, produced={item['rec_phonemes']}"
            for item in per_word_comparison
        )
        return f"Reference Text: {reference_text}\n\n(word, reference_phoneme, recorded_phoneme)\n{diff}"

    def get_feedback(self, reference_text: str, per_word_comparison: List[Dict], model: Optional[str] = None) -> Optional[str]:
        """Return LLM feedback string or None on error."""
        # If Groq SDK not installed or no API key, return None
        if not _HAS_GROQ_LIB:
            st.warning("Groq SDK not installed. LLM feedback disabled.")
            return None
        if not self.api_key:
            st.warning("Groq API key not configured. LLM feedback disabled.")
            return None

        try:
            client = self._ensure_client()
            sys = self._build_system_prompt()
            user = self._build_user_prompt(reference_text, per_word_comparison)

            used_model = model or self.model

            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": sys},
                    {"role": "user", "content": user},
                ],
                model=used_model,
                temperature=self.temperature
            )

            return chat_completion.choices[0].message.content
        except Exception as e:
            st.error(f"LLM feedback failed: {e}")
            return None
