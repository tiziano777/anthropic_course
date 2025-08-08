# Web Search Tool

Modify the JSON conf files in "tools/web_search_tool" folder to configure schama domains and localizations, then call:

```python
web_search_tool = WebSearchTool()
response =  chat(model, client,messages,
                        tools=[get_text_edit_schema(model),

                               #HERE: to add web search to available tools
                               web_search_tool.get_web_search_schema(model=model, user_location="Italy"),

                               get_current_datetime_schema,
                               batch_tool_schema,
                               ]
                    )
```
## How the Response Works

When Claude uses the web search tool, the response contains several types of blocks:

**Text blocks** - Claude's explanation of what it's doing
**ServerToolUseBlock** - Shows the exact search query Claude used
**WebSearchToolResultBlock** - Contains all the search results
**WebSearchResultBlock** - Individual performed search results with titles and URLs
**Citation blocks** - Text that supports Claude's statements


## Rendering Search Results

The different block types in the response are designed for specific UI rendering:

1. Render text blocks as regular content
2. Display web search results as a list of sources at the top
3. Show citations inline with the text, including the source domain, page title, URL, and quoted text


## Practical Usage
The web search tool works best for:

- Current events and recent developments
- Specialized information not in Claude's training data
- Fact-checking and finding authoritative sources
- Research tasks requiring up-to-date information

Simply include the schema in your tools array when making API calls, and Claude will automatically decide when a web search would help answer the user's question.

### Important note: 
Your organization must enable the Web Search tool in the settings console before using it. You can find this setting here: https://console.anthropic.com/settings/privacy