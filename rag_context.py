from rag.chunking_strategies.basic_chunking import chunk_by_section
from rag.embedding.embeddings import generate_embedding
from rag.VectorDB.BM25Index import BM25Index
from rag.VectorDB.VectorIndex import VectorIndex
from rag.retriver.MultipleIndex import Retriever
from rag.retriver.MultipleIndex import reranker_fn

from rag.context.context import add_context

text= "Your long document text goes here..."
chunks = chunk_by_section(text)

# Create a vector index, a bm25 index, then use them to create a Retriever
vector_index = VectorIndex(embedding_fn=generate_embedding)
bm25_index = BM25Index()

# Join the two indexes in a retriever
retriever = Retriever(bm25_index, vector_index, reranker_fn= reranker_fn)


# Add context to each chunk, then add to the retriever
num_start_chunks = 2
num_prev_chunks = 2
contextualized_chunks = []

for i, chunk in enumerate(chunks):
    context_parts = []

    # Initial set of chunks from the start of the doc
    context_parts.extend(chunks[: min(num_start_chunks, len(chunks))])

    # Additional chunks ahead of the current chunk we're contextualizing
    start_idx = max(0, i - num_prev_chunks)
    context_parts.extend(chunks[start_idx:i])

    context = "\n".join(context_parts)

    contextualized_chunks.append(add_context(chunk, context))

retriever.add_documents([{"content": chunk} for chunk in contextualized_chunks])

results = retriever.search("user QUERY", 2)

for doc, score in results:
    print(score, "\n", doc["content"][0:200], "\n---\n")