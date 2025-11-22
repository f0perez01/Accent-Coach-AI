import math
import re
from collections import Counter


def tokenize(text):
    tokens = re.findall(r"\b[\w']+\b", text.lower())
    return tokens


def ttr(tokens):
    types = set(tokens)
    return len(types) / max(1, len(tokens))


def mtld(tokens, threshold=0.72):
    # Simplified MTLD: forward pass only
    if not tokens:
        return 0.0
    factor_count = 0
    token_count = 0
    types = set()
    for tok in tokens:
        token_count += 1
        types.add(tok)
        cur_ttr = len(types) / token_count
        if cur_ttr <= threshold:
            factor_count += 1
            token_count = 0
            types = set()
    if token_count > 0:
        factor_count += (1 - (len(types) / max(1, token_count)))
    return len(tokens) / max(1, factor_count)


def med(tokens):
    # Measure of Textual Lexical Diversity (simple approximation)
    types = set(tokens)
    return len(types) / math.sqrt(2 * len(tokens) + 0.0001)


def load_basic_wordlists():
    # Minimal embedded 2000-word list subset and AWL flag for demo purposes
    common2000 = set(["the", "be", "and", "of", "a", "in", "to", "have", "it", "I"])
    awl = set(["analysis", "approach", "data", "academic"])
    return {"common2000": common2000, "awl": awl}


def lexical_sophistication(tokens, wordlists):
    common = wordlists.get("common2000", set())
    awl = wordlists.get("awl", set())
    outside = [t for t in tokens if t not in common]
    pct_outside = len(outside) / max(1, len(tokens))
    pct_awl = len([t for t in tokens if t in awl]) / max(1, len(tokens))
    return {"pct_outside_2000": round(pct_outside, 4), "pct_awl": round(pct_awl, 4)}


def compute_metrics_for_text(text, wordlists=None):
    tokens = tokenize(text)
    wordlists = wordlists or load_basic_wordlists()
    return {
        "tokens": len(tokens),
        "types": len(set(tokens)),
        "TTR": round(ttr(tokens), 4),
        "MTLD": round(mtld(tokens), 2),
        "MED": round(med(tokens), 4),
        **lexical_sophistication(tokens, wordlists),
    }
