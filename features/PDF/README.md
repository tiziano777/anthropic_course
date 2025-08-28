### What Claude Can Extract from PDFs
Claude's PDF processing capabilities go beyond simple text extraction. It can analyze and understand:

- Text content throughout the document
- Images and charts embedded in the PDF
- Tables and their data relationships
- Document structure and formatting

This makes Claude essentially a one-stop solution for extracting any type of information from PDF documents, whether you need summaries, data analysis, or specific content extraction.

### Enabling Citations
To enable citations, you need to modify your document message structure. Add two new fields to your document block:
```python
{
    "type": "document",
    "source": {
        "type": "base64",
        "media_type": "application/pdf",
        "data": file_bytes,
    },
    "title": "earth.pdf",
    "citations": { "enabled": True }
}
```
The title field gives your document a readable name, while citations: {"enabled": True} tells Claude to track where it finds information.

### Understanding Citation Structure
When citations are enabled, Claude's response becomes more complex. Instead of simple text, you get structured data that includes citation information for each claim.


Each citation contains several key pieces of information:

- cited_text - The exact text from your document that supports Claude's statement
- document_index - Which document Claude is referencing (useful when you provide multiple documents)
- document_title - The title you assigned to the document
- start_page_number - Where the cited text begins
- end_page_number - Where the cited text ends

### Building User Interfaces with Citations
The real power of citations comes from building user interfaces that make this information accessible. You can create interactive elements where users can hover over citation markers to see exactly where information came from.

This creates a transparent experience where users can:

See that Claude's answers are grounded in actual source material
Verify the information by checking the original document
Understand the context around each cited piece of information

### Citations with Plain Text
Citations aren't limited to PDF documents. You can also use them with plain text sources. When working with text, modify your document structure like this:

```python
{
    "type": "document", 
    "source": {
        "type": "text",
        "media_type": "text/plain",
        "data": article_text,
    },
    "title": "earth_article",
    "citations": { "enabled": True }
}
```
With plain text sources, instead of page numbers, you'll get character positions that pinpoint exactly where in the text Claude found each piece of information.

### When to Use Citations
Citations are particularly valuable when:

- Users need to verify information for accuracy
- You're working with authoritative documents that users should be able to reference
- Transparency about information sources is critical for your application
- Users might want to explore the broader context around specific facts

By implementing citations, you transform Claude from a "black box" that provides answers into a transparent research assistant that shows its work. This builds user trust and enables them to dive deeper into your source materials when needed.