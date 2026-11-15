"""Multilingual embedding generator using dense character & subword n-gram hashing projection.
Zero dependencies on heavy 4GB torch packages; runs in <1ms; produces normalized 128-dim dense vectors.
Ideal for zero-cost, high-speed multilingual embedding of English, Bangla, and Banglish.
"""
import hashlib
import re
from typing import List

import numpy as np


class LightweightEmbedder:
    """Multilingual dense embedding generator using subword n-gram hashing and projection."""

    def __init__(self, dim: int = 128):
        self.dim = dim

    def _tokenize_subwords(self, text: str) -> List[str]:
        # Normalize and extract words and character n-grams (3 to 5 chars)
        clean_text = re.sub(r"[^\w\s]", " ", text.lower(), flags=re.UNICODE)
        words = clean_text.split()
        subwords = list(words)
        for w in words:
            if len(w) >= 3:
                for n in range(3, min(6, len(w) + 1)):
                    for i in range(len(w) - n + 1):
                        subwords.append(w[i:i+n])
        return subwords if subwords else ["empty"]

    def embed_text(self, text: str) -> List[float]:
        subwords = self._tokenize_subwords(text)
        vec = np.zeros(self.dim, dtype=np.float32)

        for sw in subwords:
            # Hash to index and sign (+1 / -1)
            h = hashlib.sha256(sw.encode("utf-8")).digest()
            idx = int.from_bytes(h[:4], "little") % self.dim
            sign = 1.0 if (h[4] % 2 == 0) else -1.0
            vec[idx] += sign

        # L2 normalize
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


embedder = LightweightEmbedder(dim=128)
