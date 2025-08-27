# Retriever – Ensemble Search with Reciprocal Rank Fusion (RRF)

## Description

The `Retriever` is a class that allows combining multiple search engines (indexes) into a single access point.
Each index must comply with the interface defined by the `SearchIndex` protocol, which specifies the core methods:

* `add_document(document: Dict[str, Any]) -> None`
* `add_documents(documents: List[Dict[str, Any]]) -> None`
* `search(query: Any, k: int = 1) -> List[Tuple[Dict[str, Any], float]]`

The `Retriever` delegates document insertion to all registered indexes and uses a ranking fusion algorithm (**Reciprocal Rank Fusion**) to aggregate search results.

---

## Reciprocal Rank Fusion (RRF)

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

## Code Structure

### Index Protocol

```python
class SearchIndex(Protocol):
    def add_document(self, document: Dict[str, Any]) -> None: ...
    def add_documents(self, documents: List[Dict[str, Any]]) -> None: ...
    def search(
        self, query: Any, k: int = 1
    ) -> List[Tuple[Dict[str, Any], float]]: ...
```

### Retriever Class

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

## Main Parameters

* `k`: maximum number of documents returned (default = 1).
* `k_rrf`: attenuation constant for Reciprocal Rank Fusion (default = 60).
* `indexes`: one or more indexes conforming to the `SearchIndex` protocol.

---

## Minimal General Example

### Simple Index Implementation

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

### Usage with Retriever

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

## Advantages

* **Flexibility**: supports any search engine implementing the `SearchIndex` interface.
* **Robustness**: aggregates results from multiple indexes using a principled ranking fusion method.
* **Ease of use**: provides the same interface as a single search engine, but with ensemble capabilities.
