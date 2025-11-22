from collections import Counter
import re
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    S2_AVAILABLE = True
except Exception:
    S2_AVAILABLE = False


def tokenize(text):
    return re.findall(r"\b[\w']+\b", text.lower())


class SuggestionEngine:
    def __init__(self, candidate_list=None):
        # candidate_list: iterable of words to consider (small demo list)
        if candidate_list is None:
            self.candidates = [
                "analysis",
                "approach",
                "theory",
                "methodology",
                "evidence",
                "subsequent",
                "synthesis",
                "contextual",
            ]
        else:
            self.candidates = list(candidate_list)

        if S2_AVAILABLE:
            try:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self._cand_emb = self.model.encode(self.candidates)
            except Exception:
                self.model = None
                self._cand_emb = None
        else:
            self.model = None
            self._cand_emb = None

    def suggest(self, text, top_k=10):
        tokens = tokenize(text)
        freq = Counter(tokens)
        # naive: rank candidates by inverse frequency (rarer = higher) and similarity if possible
        scores = []
        for w in self.candidates:
            rarity = 1.0 / (1 + freq.get(w, 0))
            reason = 'rare' if freq.get(w, 0) == 0 else 'seen'
            example = ''
            sim_score = 0.0
            if self.model and self._cand_emb is not None:
                try:
                    text_emb = self.model.encode([text])[0]
                    import numpy as np
                    sim = cosine_similarity([text_emb], [self._cand_emb[self.candidates.index(w)]])[0][0]
                    sim_score = float(sim)
                    reason = f"rare + sim={sim_score:.2f}"
                except Exception:
                    pass
            final_score = rarity + sim_score
            scores.append((final_score, w, reason, example))

        scores.sort(reverse=True)
        out = []
        for score, w, reason, example in scores[:top_k]:
            out.append({"word": w, "score": score, "reason": reason, "example": example})
        return out
