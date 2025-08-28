### Prompt caching

Prompt caching offers several advantages:

1) Faster responses: Requests using cached content execute more quickly
2) Lower costs: You pay less for the cached portions of your requests
3) Automatic optimization: The initial request writes to the cache, follow-up requests read from it

However, there are important limitations to keep in mind:

- Cache duration: Cached content only lives for one hour
- Limited use cases: Only beneficial when you're repeatedly sending the same content
- High frequency requirement: Most effective when the same content appears extremely frequently in your requests
- Prompt caching works best for scenarios like document analysis workflows, where you're asking multiple questions about the same large document, or iterative editing tasks where the base content remains constant while you refine specific aspects.

### How Prompt Caching Works
When you enable prompt caching, the first request writes content to a cache that lives for one hour. Follow-up requests can then read from this cache instead of processing the same content again. This is particularly valuable when you're sending:

- Large system prompts (like a 6K token coding assistant prompt)
- Complex tool schemas (around 1.7K tokens for multiple tools)
- Repeated message content

The key insight is that caching only helps if you're repeatedly sending identical content - but in many applications, this happens extremely frequently.

### Setting Up Tool Schema Caching
To cache your tool schemas, you need to add a cache control field to the last tool in your list. Here's the proper way to do it without modifying your original tool definitions:
```python
if tools:
    tools_clone = tools.copy()
    last_tool = tools_clone[-1].copy()
    last_tool["cache_control"] = {"type": "ephemeral"}
    tools_clone[-1] = last_tool
    params["tools"] = tools_clone
```
This approach creates copies of both the tools list and the last tool schema before adding the cache control field. While you could directly modify tools[-1]["cache_control"], the copying approach prevents issues if you later reorder your tools.

### System Prompt Caching
For system prompts, you need to structure them as a text block with cache control:
```python
if system:
    params["system"] = [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"}
        }
    ]
```
This converts your system prompt from a simple string into a structured format that supports caching.

### Understanding Cache Behavior
When you run requests with caching enabled, you'll see different usage patterns in the response:

- First request: cache_creation_input_tokens=1772 - Claude writes to cache
- Follow-up requests: cache_read_input_tokens=1772 - Claude reads from cache
- Changed content: New cache creation tokens appear
- The cache is extremely sensitive - changing even a single character in your tools or system prompt - invalidates the entire cache for that component.

### Cache Ordering and Breakpoints
You can set multiple cache breakpoints in a single request. The order matters:

1) Tools (if provided)
2) System prompt (if provided)
3) Messages

If you change your system prompt but keep the same tools, you'll see a partial cache read (for tools) and a cache write (for the new system prompt). This granular caching means you only pay for processing the parts that actually changed.

### Practical Considerations
Prompt caching is most effective when you have:

- Consistent tool schemas across requests
- Stable system prompts
- Applications that make multiple requests with similar context

Remember that the cache only lasts for one hour, so it's designed for applications with relatively frequent API usage rather than long-term storage.