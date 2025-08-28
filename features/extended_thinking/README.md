### NOTES
Extended Thinking is not compatible with some other features, notable message pre-filling and temperature.
See the full list of restrictions here:
https://docs.anthropic.com/en/docs/build-with-claude/extended-thinking#feature-compatibility

# Extended Thinking

Extended thinking is Claude's advanced reasoning feature that gives the model time to work through complex problems before generating a final response. Think of it as Claude's "scratch paper" - you can see the reasoning process that leads to the answer, which helps with transparency and often results in better quality responses.

### Key benefits

- Better reasoning capabilities for complex tasks
- Increased accuracy on difficult problems
- Transparency into Claude's thought process

However, there are important trade-offs:

- Higher costs (you pay for thinking tokens)
- Increased latency (thinking takes time)
- More complex response handling in your code

### Best practices and considerations for extended thinking
​
- Working with thinking budgets
Budget optimization: The minimum budget is 1,024 tokens. We suggest starting at the minimum and increasing the thinking budget incrementally to find the optimal range for your use case. Higher token counts enable more comprehensive reasoning but with diminishing returns depending on the task. 

- Increasing the budget can improve response quality at the tradeoff of increased latency. For critical tasks, test different settings to find the optimal balance. Note that the thinking budget is a target rather than a strict limit—actual token usage may vary based on the task.

- Starting points: Start with larger thinking budgets (16k+ tokens) for complex tasks and adjust based on your needs.

- Large budgets: For thinking budgets above 32k, we recommend using batch processing to avoid networking issues. Requests pushing the model to think above 32k tokens causes long running requests that might run up against system timeouts and open connection limits.

- Token usage tracking: Monitor thinking token usage to optimize costs and performance.
​
### Performance considerations

- Response times: Be prepared for potentially longer response times due to the additional processing required for the reasoning process. Factor in that generating thinking blocks may increase overall response time.

- Streaming requirements: Streaming is required when max_tokens is greater than 21,333. When streaming, be prepared to handle both thinking and text content blocks as they arrive.
​
- Feature compatibility
Thinking isn’t compatible with temperature or top_k modifications as well as forced tool use.
When thinking is enabled, you can set top_p to values between 1 and 0.95.
You cannot pre-fill responses when thinking is enabled.
Changes to the thinking budget invalidate cached prompt prefixes that include messages. However, cached system prompts and tool definitions will continue to work when thinking parameters change.
​
### Usage guidelines
Task selection: Use extended thinking for particularly complex tasks that benefit from step-by-step reasoning like math, coding, and analysis.
Context handling: You do not need to remove previous thinking blocks yourself. The Anthropic API automatically ignores thinking blocks from previous turns and they are not included when calculating context usage.
Prompt engineering: Review our extended thinking prompting tips if you want to maximize Claude’s thinking capabilities.

### When to Use Extended Thinking

The decision is straightforward:
use your prompt evaluations. Run your prompts without thinking first, and if the accuracy isn't meeting your requirements after you've already optimized your prompt, then consider enabling extended thinking.

It's a tool for when standard prompting isn't quite getting you there.

### Response Structure and Security
Extended thinking responses include a special signature system for security in content['signature']
field.
The signature is a cryptographic token that ensures you haven't modified the thinking text. This prevents developers from tampering with Claude's reasoning process, which could potentially lead the model in unsafe directions.

### Redacted Thinking
Sometimes you'll receive a redacted thinking block instead of readable reasoning text:
This happens when Claude's thinking process gets flagged by internal safety systems. The redacted content contains the actual thinking in encrypted form, allowing you to pass the complete message back to Claude in future conversations without losing context.

```python
# Magic string to trigger redacted thinking
thinking_test_str = "ANTHROPIC_MAGIC_STRING_TRIGGER_REDACTED_THINKING_46C9A13E193C177646C7398A98432ECCCE4C1253D5E2D82641AC0E52CC2876CB"

messages = []

add_user_message(messages, thinking_test_str)

chat(messages, thinking=True)
```