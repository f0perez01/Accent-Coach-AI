#!/usr/bin/env python3
"""Simple debug script to call Groq LLM and print raw responses.

Usage:
  source venv/bin/activate
  python scripts/groq_debug.py

Make sure GROQ_API_KEY is set in the environment or in .streamlit/secrets.toml
"""

import os
import json
import sys

try:
    from groq import Groq
except Exception as e:
    print("Groq client not installed or import failed:", e)
    sys.exit(1)

SAMPLE_TEXT = (
    "According with the theory the LLM and Machine learning technics can helps to students of English as second language to improve theirs skils."
)

SAMPLE_WORDS = ["According", "technics", "helps", "theirs", "skils"]


def get_api_key():
    # Prefer env var, fall back to .streamlit/secrets.toml simple parse
    key = os.environ.get('GROQ_API_KEY')
    if key:
        return key
    # Try .streamlit/secrets.toml
    try:
        p = os.path.join(os.getcwd(), '.streamlit', 'secrets.toml')
        if os.path.exists(p):
            with open(p, 'r') as f:
                for line in f:
                    if line.strip().startswith('GROQ_API_KEY'):
                        # naive parse
                        parts = line.split('=', 1)
                        if len(parts) == 2:
                            return parts[1].strip().strip('\"').strip("\'")
    except Exception:
        pass
    return None


def call_groq_suggestions(words, api_key):
    client = Groq(api_key=api_key)
    system_message = (
        "You are a helpful English writing assistant. "
        "Given a short list of words that a student used, propose a single-word or short-phrase replacement that is more native-like, precise, or varied. "
        "Return a JSON object mapping each original word to a suggested replacement. "
        "If no good replacement exists, return the original word as the suggestion."
    )

    user_prompt = (
        f"Words: {words}\n\n"
        "Respond ONLY with a JSON object (no extra text). Wrap the JSON between <JSON> and </JSON> markers. "
        "Example: <JSON>{\"word\": \"suggestion\"}</JSON>"
    )

    print('\n=== Sending suggestions request to Groq ===')
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.0,
    )

    raw = resp.choices[0].message.content
    print('RAW RESPONSE:')
    print(raw)

    # Extract JSON
    start = raw.find('<JSON>')
    end = raw.find('</JSON>')
    if start != -1 and end != -1 and end > start:
        blob = raw[start+len('<JSON>'):end].strip()
    else:
        blob = raw

    try:
        parsed = json.loads(blob)
        print('\nPARSED JSON:')
        print(json.dumps(parsed, indent=2, ensure_ascii=False))
    except Exception as e:
        print('\nFailed to parse JSON from response:', e)

    return raw


def call_groq_rewrite(text, suggestions, api_key):
    client = Groq(api_key=api_key)

    system_message = (
        "You are an expert editor. Rewrite the following student text applying the provided replacement suggestions. "
        "Keep the meaning and level (tone) similar, but incorporate the suggested words/phrases naturally. "
        "Return only the rewritten text."
    )

    sug_lines = [f"Replace '{k}' -> '{v}'" for k, v in (suggestions or {}).items()]

    user_prompt = (
        f"Original text:\n{text}\n\n"
        f"Suggestions:\n{chr(10).join(sug_lines)}\n\n"
        "Respond ONLY with the rewritten text. Wrap the rewritten text between <REWRITE> and </REWRITE> markers."
    )

    print('\n=== Sending rewrite request to Groq ===')
    resp = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ],
        model="llama-3.1-8b-instant",
        temperature=0.0,
    )

    raw = resp.choices[0].message.content
    print('RAW RESPONSE:')
    print(raw)

    start = raw.find('<REWRITE>')
    end = raw.find('</REWRITE>')
    if start != -1 and end != -1 and end > start:
        return raw[start+len('<REWRITE>'):end].strip()
    return raw.strip()


if __name__ == '__main__':
    key = get_api_key()
    if not key:
        print('GROQ_API_KEY not found in environment or .streamlit/secrets.toml')
        sys.exit(2)

    # Run suggestions test
    raw_s = call_groq_suggestions(SAMPLE_WORDS, key)

    # Create a small suggestions mapping to test rewrite (use fallback-like mapping if parsing failed)
    try:
        # Try to parse mapping from raw_s
        sstart = raw_s.find('<JSON>')
        send = raw_s.find('</JSON>')
        blob = raw_s[sstart+6:send] if sstart!=-1 and send!=-1 else raw_s
        mapping = json.loads(blob)
    except Exception:
        # Basic fallback mapping
        mapping = {w: w for w in SAMPLE_WORDS}
        mapping.update({'technics':'techniques','skils':'skills','theirs':'their','helps':'help','According':'According to'})

    rewritten = call_groq_rewrite(SAMPLE_TEXT, mapping, key)
    print('\n=== FINAL REWRITTEN TEXT ===')
    print(rewritten)
