import chromadb
from chromadb.config import Settings
from rag.embedding.embeddings import generate_embedding

# Setup Chroma client
chroma_client = chromadb.Client(Settings(
    persist_directory="./chroma_data",
    chroma_db_impl="duckdb+parquet"
))

collection = chroma_client.get_or_create_collection(name="my_collection")

# Inserimento di un documento
def insert_to_chroma(doc_id: str, text: str, metadata: dict):
    embedding = generate_embedding(text)
    collection.add(
        documents=[text],
        embeddings=[embedding],
        metadatas=[metadata],
        ids=[doc_id]
    )

# ESEMPIO
insert_to_chroma("doc1", "To je slovensko besedilo.", {"lang": "sl"})
