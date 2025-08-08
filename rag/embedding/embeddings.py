from sentence_transformers import SentenceTransformer

# Load the model once
model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

# Embedding function
def generate_embedding(text: str) -> list[float]:
    '''
    Compatibilità con vectorDB
    Restituisce un oggetto List[float] o np.ndarray, quindi compatibile con:
    FAISS: index.add(np.array([embedding]))
    Qdrant: vectors=[embedding]
    ChromaDB: documents=[text], embeddings=[embedding]
    '''
    return model.encode(text, normalize_embeddings=True).tolist() # compatibile con FAISS, Qdrant, ecc.