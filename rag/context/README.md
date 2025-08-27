# Contetual Retrival

Contextual retrieval is a technique that improves RAG pipeline accuracy by solving a fundamental problem: when you split a document into chunks, each chunk loses its connection to the broader document context.

## The Problem with Standard Chunking
When you take a source document and break it into chunks for your vector database, each individual piece no longer knows where it came from or how it relates to the rest of the document. This can hurt retrieval accuracy because the chunks lack important contextual information.

## How Contextual Retrieval Works
Contextual retrieval adds a preprocessing step before inserting chunks into your retriever database.
Here's the process:
- Take each individual chunk and the original source document
- Send both to Claude with a specific prompt
- Ask Claude to write a short snippet that situates the chunk within the overall document
- Combine this context with the original chunk to create a "contextualized chunk"
Use the contextualized chunk in your vector and BM25 indexes

The prompt asks Claude to analyze the chunk and write context that explains what the chunk is about in relation to the larger document. For example, if you have a section about software engineering that mentions a 2023 incident, Claude might generate context explaining that this section is from a larger report and that the same incident is also mentioned in other sections.

## Handling Large Documents
A common problem is when your source document is too large to fit into a single prompt with Claude. In this case, you can provide a reduced set of context instead of the entire document.

### The strategy is to include:

- A few chunks from the start of the document (often containing summaries or abstracts)
- Chunks immediately before the chunk you're contextualizing
- Skip chunks in the middle that are less relevant to the current chunk

This approach gives Claude enough context to understand what the document is about and how the current chunk fits in, without overwhelming the prompt with unnecessary text.

### Implementation Example
Here's a basic function for adding context to a single chunk:

```python
def add_context(text_chunk, source_text):
    prompt = """
    Write a short and succinct snippet of text to situate this chunk within the
    overall source document for the purposes of improving search retrieval of the chunk.
    
    Here is the original source document:
    <document>
    {source_text}
    </document>
    
    Here is the chunk we want to situate within the whole document:
    <chunk>
    {text_chunk}
    </chunk>
    
    Answer only with the succinct context and nothing else.
    """
    
    messages = []
    add_user_message(messages, prompt)
    result = chat(messages)
    
    return result["text"] + "\n" + text_chunk
```

For processing multiple chunks with limited context, you can select specific chunks to include:

### Add context to each chunk, then add to the retriever
```python
num_start_chunks = 2
num_prev_chunks = 2

for i, chunk in enumerate(chunks):
    context_parts = []
    
    # Initial set of chunks from the start of the doc
    context_parts.extend(chunks[: min(num_start_chunks, len(chunks))])
    
    # Additional chunks ahead of the current chunk we're contextualizing
    start_idx = max(0, i - num_prev_chunks)
    context_parts.extend(chunks[start_idx:i])
    
    context = "\n".join(context_parts)
    
    contextualized_chunk = add_context(chunk, context)
    retriever.add_document({"content": contextualized_chunk})
```

## Expected Results
When you run a search query with contextual retrieval, you'll get results that include both the generated context and the original chunk content. The context helps the retrieval system better understand what each chunk is about and how it relates to the broader document.

For example, a contextualized chunk might start with: "This chunk is Section 2 of an Annual Interdisciplinary Research Review, detailing software engineering efforts to resolve stability issues in Project Phoenix..." followed by the original chunk text.

This technique is especially valuable for complex documents where individual sections have many interconnections and references to other parts of the document. The added context helps ensure that relevant chunks are retrieved even when the search query doesn't exactly match the chunk's original text.