from rag.embedding.embeddings import generate_embedding
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import uuid

# Setup Qdrant client
client = QdrantClient(path="./qdrant_data")  # oppure url="http://localhost:6333"

collection_name = "my_collection"
vector_dim = 384

client.recreate_collection(
    collection_name=collection_name,
    vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE)
)

def insert_to_qdrant(text: str, metadata: dict):
    embedding = generate_embedding(text)
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload=metadata | {"text": text}
    )
    client.upsert(collection_name=collection_name, points=[point])

# ESEMPIO
insert_to_qdrant("To je slovensko besedilo.", {"lang": "sl"})

# Ricerca
def search_qdrant(query: str, top_k=5):
    vector = generate_embedding(query)
    hits = client.search(
        collection_name=collection_name,
        query_vector=vector,
        limit=top_k
    )
    return [{"score": h.score, "payload": h.payload} for h in hits]
