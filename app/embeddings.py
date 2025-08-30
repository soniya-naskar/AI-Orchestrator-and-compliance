# Placeholder embeddings wrapper. Replace with OpenAI or sentence-transformers in production.
import numpy as np

def embed_text(text: str):
    # deterministic lightweight embedding for demo (hash -> vector)
    h = abs(hash(text)) % (10**8)
    vec = [(h >> (i*8)) % 256 for i in range(32)]
    v = np.array(vec, dtype=float)
    v = v / (np.linalg.norm(v) + 1e-6)
    return v.tolist()
