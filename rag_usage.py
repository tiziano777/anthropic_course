
from rag.chunking_strategies.basic_chunking import chunk_by_section
from rag.embedding.embeddings import generate_embedding
from rag.VectorDB.BM25Index import BM25Index
from rag.VectorDB.VectorIndex import VectorIndex
from rag.retriver.MultipleIndex import Retriever
from rag.retriver.MultipleIndex import reranker_fn

text= "Your long document text goes here..."
chunks = chunk_by_section(text)

# Create a vector index, a bm25 index, then use them to create a Retriever
vector_index = VectorIndex(embedding_fn=generate_embedding)
bm25_index = BM25Index()

# Join the two indexes in a retriever
retriever = Retriever(bm25_index, vector_index, reranker_fn= reranker_fn)

# Use Hybrid retriver to add documents
retriever.add_documents([{"content": chunk} for chunk in chunks])