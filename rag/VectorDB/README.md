## RAG Vector Storage Flow

### First preprocessing steps:

1. Chunking the Text

First, we load our document and split it into manageable sections:
```python
with open("./report.md", "r") as f:
    text = f.read()

chunks = chunk_by_section(text)
chunks[2]  # Test to see the table of contents
```

We use the same chunk_by_section function from earlier to split our document into logical sections.

2. Generate Embeddings
Next, we create embeddings for all our chunks at once:
```python
embeddings = generate_embedding(chunks)
```
The embedding function has been updated to handle both single strings and lists of strings, making it more efficient for batch processing.

3. Store in Vector Database
Now we create our vector store and populate it with embeddings and their associated text:
```python
store = VectorIndex()

for embedding, chunk in zip(embeddings, chunks):
    store.add_vector(embedding, {"content": chunk})
```
Notice that we store both the embedding and the original text content. This is crucial because when we search later, we need to return the actual text, not just the numerical embedding values.

### Storage

When building RAG pipelines, you'll quickly discover that semantic search alone doesn't always return the best results.
Sometimes you need exact term matches that semantic search might miss.
The solution is to combine semantic search with lexical search using a technique called BM25.

- Semantic search finds conceptually related content using embeddings
- Lexical search finds exact term matches using classic text search
- Merged results combine both approaches for better accuracy

#### How Vector storage Works:

The vector database uses cosine similarity to determine which embeddings are most similar.
This measures the cosine of the angle between two vectors.

#### How BM25 Works:

1. Tokenize the query
Break the user's question into individual terms. 

2. Count term frequency
See how often each term appears across all your documents. Common words like "a" might appear 5 times, while specific terms like IDs might appear only once.

3. Weight terms by importance
Terms that appear less frequently get higher importance scores. The word "a" gets low importance because it's common, while IDs gets high importance because it's rare.

4. Find best matches
Return documents that contain more instances of the higher-weighted terms.