## Prompt Engineering vs Prompt Evaluation

Prompt engineering is your toolkit for crafting effective prompts. It includes techniques like:

- Multishot prompting
- Structuring with XML tags

### Many other best practices

These techniques help Claude understand exactly what you're asking for and how you want it to respond.
Prompt evaluation takes a different approach. Instead of focusing on how to write prompts, it's about measuring their effectiveness through automated testing. You can:

- Test against expected answers
- Compare different versions of the same prompt
- Review outputs for errors

### Three Paths After Writing a Prompt

Once you've drafted a prompt, you typically face three options for what to do next:

1. Test the prompt once and decide it's good enough. This carries a significant risk of breaking in production when users provide unexpected inputs.

2. Test the prompt a few times and tweak it to handle a corner case or two. While better than option 1, users will often provide very unexpected outputs that you haven't considered.

3. Run the prompt through an evaluation pipeline to score it, then iterate on the prompt based on objective metrics. This approach requires more work and cost, but gives you much more confidence in your prompt's reliability.

### Eval Workflow:

A typical prompt evaluation workflow follows five key steps that help you systematically improve your prompts through objective measurement. While there are many different ways to assemble these workflows and various open source and paid tools available, understanding the core process helps you start small and scale up as needed.

1. Draft a Prompt
Start by writing an initial prompt that you want to improve. For this example, we'll use a simple prompt:
```python
prompt = f""" Please answer the user's question: {question} """
```
This basic prompt will serve as our baseline for testing and improvement.

2. Create an Eval Dataset
Your evaluation dataset contains sample inputs that represent the types of questions or requests your prompt will handle in production. The dataset should include questions that will be interpolated into your prompt template.


For this example, our dataset includes three questions:
```bash
"What's 2+2?"
"How do I make oatmeal?"
"How far away is the Moon?"
```
In real-world evaluations, you might have tens, hundreds, or even thousands of records. You can assemble these datasets by hand or use Claude to generate them for you.

3. Feed Through Claude
Take each question from your dataset and merge it with your prompt template to create complete prompts. Then send each one to Claude to get responses.

For example, the first question becomes:

Please answer the user's question:
```bash
What's 2+2?
Claude might respond with "2 + 2 = 4" for the math question, provide oatmeal cooking instructions for the second question, and give the distance to the Moon for the third.
```
4. Feed Through a Grader
The grader evaluates the quality of Claude's responses by examining both the original question and Claude's answer. This step provides objective scoring, typically on a scale from 1 to 10, where 10 represents a perfect answer and lower scores indicate room for improvement.

In our example, the grader might assign:
```bash
Math question: 10 (perfect answer)
Oatmeal question: 4 (needs improvement)
Moon question: 9 (very good answer)
The average score across all questions gives you an objective measurement: (10 + 4 + 9) ÷ 3 = 7.66
```
5. Change Prompt and Repeat
Now that you have a baseline score, you can modify your prompt and run the entire process again to see if your changes improve performance.


For example, you might add more guidance to your prompt:
```python
prompt = f""" Please answer the user's question: {question} Answer the question with ample detail """
```
After running this improved prompt through the same evaluation process, you might get a higher average score of 8.7, indicating that the additional instruction helped Claude provide better responses.

### Prompt Scoring
The key benefit of this workflow is getting objective measurements of prompt performance. You can:

- Compare different prompt versions numerically
- Use the version with the best score
- Continue iterating to find even better approaches

This systematic approach removes guesswork from prompt engineering and gives you confidence that your changes are actually improvements rather than just different variations.

## Building the Core Functions

The evaluation pipeline consists of three main functions, each with a specific responsibility. Let's start with the simplest one - the function that handles individual prompts.

- The **run_prompt** Function
This function takes a test case and merges it with our prompt template:
```python
def run_prompt(test_case):
    """Merges the prompt and test case input, then returns the result"""
    prompt = f""" Please solve the following task: {test_case["task"]} """
    messages = []
    add_user_message(messages, prompt)
    output = chat(messages)
    return output
```
Right now, we're keeping the prompt extremely simple. We're not including any formatting instructions, so Claude will likely return more verbose output than we need. We'll refine this later as we iterate on our prompt design.

- The **run_test_case** Function

This function orchestrates running a single test case and grading the result:
```python
def run_test_case(test_case):
    """Calls run_prompt, then grades the result"""
    output = run_prompt(test_case)
    
    # TODO - Grading Logic
    
    return {
        "output": output,
        "test_case": test_case,
        "score": score
    }
```
The grading logic is where we'll spend significant time in upcoming sections.

- The **run_eval** Function

This function coordinates the entire evaluation process:
```python
def run_eval(dataset):
    """Loads the dataset and calls run_test_case with each case"""
    results = []
    
    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
    
    return results
```
This function processes every test case in our dataset and collects all the results into a single list.

- Running the Evaluation
To execute our evaluation pipeline, we load our dataset and run it through our functions:

```python
with open("dataset.json", "r") as f:
    dataset = json.load(f)

results = run_eval(dataset)
```

The first time you run this, expect it to take some time - even with Claude Haiku, it can take around 30 seconds to process a full dataset. We'll cover optimization techniques later.

Examining the Results
The evaluation returns a structured JSON array where each object represents one test case result:

```python
print(json.dumps(results, indent=2))
```
Each result contains three key pieces of information:

*output*: The complete response from Claude
*test_case*: The original test case that was processed
*score*: The evaluation score (currently hardcoded)

As you can see in the output, Claude generates quite verbose responses since we haven't provided specific formatting instructions yet. This is exactly the kind of issue we'll address as we refine our prompts.

## There are three main approaches to grading model outputs:

**Code graders** - Programmatically evaluate outputs using custom logic
**Model graders** - Use another AI model to assess the quality
**Human graders** - Have people manually review and score outputs

### Code Graders
Code graders let you implement any programmatic check you can imagine. Common uses include:

- Checking output length
- Verifying output does/doesn't have certain words
- Syntax validation for JSON, Python, or regex
- Readability scores

The only requirement is that your code returns some usable signal - usually a number between 1 and 10.

### Model Graders
Model graders feed your original output into another API call for evaluation. This approach offers tremendous flexibility for assessing:

- Response quality
- Quality of instruction following
- Completeness
- Helpfulness
- Safety

### Human Graders
Human graders provide the most flexibility but are time-consuming and tedious. They're useful for evaluating:

- General response quality
- Comprehensiveness
-Depth
- Conciseness
- Relevance

## Defining Evaluation Criteria

Before implementing any grader, you need clear evaluation criteria. For a code generation prompt, you might focus on:

- **Format** - Should return only Python, JSON, or Regex without explanation
- **Valid Syntax** - Produced code should have valid syntax
- **Task Following** - Response should directly address the user's task with accurate code

The first two criteria work well with code graders, while task following is better suited for model graders due to their flexibility.

### Implementing a Model Grader
Here's how to build a model grader function:
```python
def grade_by_model(test_case, output):
    # Create evaluation prompt
    eval_prompt = """
    You are an expert code reviewer. Evaluate this AI-generated solution.
    
    Task: {task}
    Solution: {solution}
    
    Provide your evaluation as a structured JSON object with:
    - "strengths": An array of 1-3 key strengths
    - "weaknesses": An array of 1-3 key areas for improvement  
    - "reasoning": A concise explanation of your assessment
    - "score": A number between 1-10
    """
    
    messages = []
    add_user_message(messages, eval_prompt)
    add_assistant_message(messages, "```json")
    
    eval_text = chat(messages, stop_sequences=["```"])
    return json.loads(eval_text)
```

The key insight is asking for strengths, weaknesses, and reasoning alongside the score. Without this context, models tend to default to middling scores around 6.

### Integrating Grading into Your Workflow
Update your test case runner to call the grader:
```python
def run_test_case(test_case):
    output = run_prompt(test_case)
    
    # Grade the output
    model_grade = grade_by_model(test_case, output)
    score = model_grade["score"]
    reasoning = model_grade["reasoning"]
    
    return {
        "output": output, 
        "test_case": test_case, 
        "score": score,
        "reasoning": reasoning
    }
```

Finally, calculate an average score across all test cases:
```python
from statistics import mean

def run_eval(dataset):
    results = []
    
    for test_case in dataset:
        result = run_test_case(test_case)
        results.append(result)
    
    average_score = mean([result["score"] for result in results])
    print(f"Average score: {average_score}")
    
    return results
```

This gives you an objective metric to track as you iterate on your prompt. While model graders can be somewhat capricious, they provide a consistent baseline for measuring improvements.