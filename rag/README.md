# RAG Flow

## Benefits of RAG
- Claude can focus on only the most relevant content
- Scales up to very large documents
- Works with multiple documents
- Smaller prompts cost less and run faster

## Challenges with RAG
1. Requires a preprocessing step to chunk documents
2. Need a search mechanism to find "relevant" chunks
3. Included chunks might not contain all the context Claude needs
4. Many ways to chunk text - which approach is best?

For example, you could split documents into equal-sized portions, or you could create chunks based on document structure like headers and sections. Each approach has trade-offs you'll need to evaluate for your specific use case.

## Chunking Strategies

Text chunking is one of the most critical steps in building a RAG (Retrieval Augmented Generation) pipeline. How you break up your documents directly impacts the quality of your entire system. A poor chunking strategy can lead to irrelevant context being inserted into your prompts, causing your AI to give completely wrong answers.

### Size-Based Chunking

Size-based chunking is the simplest approach - you divide your text into strings of equal length. If you have a 325-character document, you might split it into three chunks of roughly 108 characters each.


This method is easy to implement and works with any type of document, but it has clear downsides:

Words get cut off mid-sentence
Chunks lose important context from surrounding text
Section headers might be separated from their content

To address these issues, you can add overlap between chunks. This means each chunk includes some characters from the neighboring chunks, providing better context and ensuring complete words and sentences.


Here's a basic implementation:
```python
def chunk_by_char(text, chunk_size=150, chunk_overlap=20):
    chunks = []
    start_idx = 0
    
    while start_idx < len(text):
        end_idx = min(start_idx + chunk_size, len(text))
        chunk_text = text[start_idx:end_idx]
        chunks.append(chunk_text)
        
        start_idx = (
            end_idx - chunk_overlap if end_idx < len(text) else len(text)
        )
    
    return chunks
```

### Structure-Based Chunking

Structure-based chunking divides text based on the document's natural structure - headers, paragraphs, and sections. This works great when you have well-formatted documents like Markdown files.


For a Markdown document, you can split on header markers:
```python
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)
```

This approach gives you the cleanest, most meaningful chunks because each one represents a complete section. However, it only works when you have guarantees about your document structure. Many real-world documents are plain text or PDFs without clear structural markers.

### Semantic-Based Chunking
Semantic-based chunking is the most sophisticated approach. You divide text into sentences, then use natural language processing to determine how related consecutive sentences are. You build chunks from groups of related sentences.

This method is computationally expensive but produces the most relevant chunks. It requires understanding the meaning of individual sentences and is more complex to implement than the other strategies.

Sentence-Based Chunking
A practical middle ground is chunking by sentences. You split the text into individual sentences using regular expressions, then group them into chunks with optional overlap:

```python
def chunk_by_sentence(text, max_sentences_per_chunk=5, overlap_sentences=1):
    sentences = re.split(r"(?<=[.!?])\s+", text)
    
    chunks = []
    start_idx = 0
    
    while start_idx < len(sentences):
        end_idx = min(start_idx + max_sentences_per_chunk, len(sentences))
        current_chunk = sentences[start_idx:end_idx]
        chunks.append(" ".join(current_chunk))
        
        start_idx += max_sentences_per_chunk - overlap_sentences
        
        if start_idx < 0:
            start_idx = 0
    
    return chunks
```

### Choosing Your Strategy
Your choice depends entirely on your use case and document guarantees:

***Structure-based**: Best results when you control document formatting (like internal company reports)
**Sentence-based**: Good middle ground for most text documents
**Size-based**: Most reliable fallback that works with any content type, including code

Size-based chunking with overlap is often the go-to choice in production because it's simple, reliable, and works with any document type. While it may not give perfect results, it consistently produces reasonable chunks that won't break your pipeline.

Remember: there's no single "best" chunking strategy. The right approach depends on your specific documents, use cases, and the trade-offs you're willing to make between implementation complexity and chunk quality.

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

## Retriver

The Retriever acts as a coordinator that forwards user queries to both indexes, collects their results, and merges them using a technique called reciprocal rank fusion.

### Description

The `Retriever` is a class that allows combining multiple search engines (indexes) into a single access point.
Each index must comply with the interface defined by the `SearchIndex` protocol, which specifies the core methods:

* `add_document(document: Dict[str, Any]) -> None`
* `add_documents(documents: List[Dict[str, Any]]) -> None`
* `search(query: Any, k: int = 1) -> List[Tuple[Dict[str, Any], float]]`

The `Retriever` delegates document insertion to all registered indexes and uses a ranking fusion algorithm (**Reciprocal Rank Fusion**) to aggregate search results.

---

### Reciprocal Rank Fusion (RRF)

Given a set of indexes $I = \{1, \dots, m\}$, each produces a ranked list of documents for a query $q$.
For each document $d$, its rank $r_{i,d}$ within index $i$ is considered.
The aggregated score is defined as:

$$
\text{score}(d) = \sum_{i=1}^m \frac{1}{k_{\text{rrf}} + r_{i,d}}
$$

where:

* $r_{i,d}$ is the rank (≥1) of document $d$ in index $i$,
* $k_{\text{rrf}}$ is a parameter that reduces the impact of very low-ranked documents.

The final result is the set of documents ordered by `score(d)` in descending order.

---

## Reranking Function

re-ranking is a technique that adds another post-processing step to improve retrieval accuracy.

### How Re-ranking Works

Re-ranking is conceptually simple. After running your vector index and BM25 index and merging the results, you add one more step: a re-ranker that uses Claude to intelligently reorder your search results.

The re-ranker function gets called automatically by your retriever after the initial hybrid search completes. Here's the basic structure:

```python
def reranker_fn(docs, query_text, k):
    # Format documents with IDs
    joined_docs = "\n".join([
        f"""
        <document>
        <document_id>{doc["id"]}</document_id>
        <document_content>{doc["content"]}</document_content>
        </document>
        """
        for doc in docs
    ])
    
    # Create prompt and get Claude's response
    prompt = f"""..."""
    messages = []
    add_user_message(messages, prompt)
    add_assistant_message(messages, """```json""")
    
    result = chat(messages, stop_sequences=["""```"""])
    
    return json.loads(result["text"])["document_ids"]
```
### Trade-offs
Re-ranking comes with clear trade-offs:

- Increased latency: You now have to wait for an additional API call to Claude
- Increased accuracy: Claude can understand context and relevance in ways that pure vector similarity cannot

---

### Code Structure

#### Index Protocol

```python
class SearchIndex(Protocol):
    def add_document(self, document: Dict[str, Any]) -> None: ...
    def add_documents(self, documents: List[Dict[str, Any]]) -> None: ...
    def search(
        self, query: Any, k: int = 1
    ) -> List[Tuple[Dict[str, Any], float]]: ...
```

#### Retriever Class

```python
text= "Your long document text goes here..."
chunks = chunk_by_section(text)

# Create indexes, vector index and bm25 index, then use them to create a Retriever
vector_index = VectorIndex(embedding_fn=generate_embedding)
bm25_index = BM25Index()

# Join multple indexes in a retriever
retriever = Retriever(bm25_index, vector_index, ....)

# Use Hybrid retriver to add documents
retriever.add_documents([{"content": chunk} for chunk in chunks])
```

---

### Main Parameters

* `k`: maximum number of documents returned (default = 1).
* `k_rrf`: attenuation constant for Reciprocal Rank Fusion (default = 60).
* `indexes`: one or more indexes conforming to the `SearchIndex` protocol.

---

### Minimal General Example

#### Simple Index Implementation

```python
class SimpleIndex:
    def __init__(self):
        self.docs = []

    def add_document(self, document: Dict[str, Any]) -> None:
        self.docs.append(document)

    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        self.docs.extend(documents)

    def search(self, query: str, k: int = 1):
        # Returns documents containing the query in their text
        results = [
            (doc, 1.0) for doc in self.docs if query.lower() in doc["text"].lower()
        ]
        return results[:k]
```

#### Usage with Retriever

```python
# Create indexes
index_a = SimpleIndex()
index_b = SimpleIndex()

# Create retriever
retriever = Retriever(index_a, index_b)

# Add documents
retriever.add_documents([
    {"id": 1, "text": "The cat sat on the mat"},
    {"id": 2, "text": "Deep learning for search engines"},
])

# Search
results = retriever.search("cat", k=5)
for doc, score in results:
    print(doc, score)
```

---

### Advantages

* **Flexibility**: supports any search engine implementing the `SearchIndex` interface.
* **Robustness**: aggregates results from multiple indexes using a principled ranking fusion method.
* **Ease of use**: provides the same interface as a single search engine, but with ensemble capabilities.
