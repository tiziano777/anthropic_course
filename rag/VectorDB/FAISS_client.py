import faiss
import numpy as np
from rag.embedding.embeddings import generate_embedding

# Setup FAISS (Inner Product ≈ cosine sim se normalize_embeddings=True)
dim = 384
index = faiss.IndexFlatIP(dim)  # Inner product (cosine sim equiv. con normalizzazione)

# Storage ausiliario per ID / metadati
id_map = {}
next_id = 0

def insert_to_faiss(text: str, metadata: dict):
    global next_id
    embedding = generate_embedding(text)
    index.add(np.array([embedding]))
    id_map[next_id] = {"text": text, "metadata": metadata}
    next_id += 1

# ESEMPIO
insert_to_faiss("To je slovensko besedilo.", {"lang": "sl"})

# Ricerca
def search_faiss(query: str, top_k=5):
    emb = generate_embedding(query)
    D, I = index.search(np.array([emb]), top_k)
    results = []
    for idx in I[0]:
        results.append(id_map.get(idx, {}))
    return results