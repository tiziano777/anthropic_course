import json
from statistics import mean
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic
from chat_template.chat_functions import chat, add_assistant_message, add_user_message
from evaluation.model_grader import grade_by_model
from evaluation.syntax_grader import grade_syntax

from utils.dataset_creation import generate_dataset

def run_prompt(model, client, test_case):
    
    """Merges the prompt and test case input, then returns the result"""
    
    prompt = f"""
    Please solve the following task:
    {test_case["task"]}
    """
    
    messages = []
    add_user_message(messages, prompt)
    output = chat(model, client, messages)
    return output

def run_test_case(model, client, test_case):
    
    """Calls run_prompt, then grades the result"""
    
    output = run_prompt(model, client, test_case)
    
    ### Grading Strategy (Model, user, code)
    
    ## 1) model
    
    # Grade the output
    model_grade = grade_by_model(test_case, output)
    
    model_score = model_grade["score"]
    reasoning = model_grade["reasoning"]
    strengths = model_grade['strengths']
    weaknesses = model_grade['weaknesses']
    
    ## 2) code (syntax)
    
    syntax_score = grade_syntax(output, test_case)
    score = (model_score + syntax_score) / 2 
    
    ###
    
    return {
        "output": output,
        "test_case": test_case,
        "score": score,
        "reasoning": reasoning,
        "strengths": strengths,
        "weaknesses": weaknesses
    }

def run_eval(model, client, dataset):
    """Loads the dataset and calls (run_test_case) -> (run_prompt) for each case"""
    results = []
    
    for test_case in dataset:
        result = run_test_case(model, client, test_case)
        results.append(result)
    
    # Evaluate prompt results
    average_score = mean([result["score"] for result in results])
    print(f"Average score: {average_score}")
    
    return results


#### USAGE EXAMPLE ####

client = Anthropic()
model = "claude-sonnet-4-0"
messages = []

gen_dataset_prompt= """ generate a dataset for NER task in JSON structured output for a prompt evaluation.
The dataset will be used to evaluate prompts.
Generate an array of JSON objects, each representing task that requires Python, JSON, or a Regex to complete.

Example output:
```json
[
    {
        "task": "Description of task",
        "format": "json" or "python" or "regex",
        "kpi": "key criteria to evaluate the result"
    },
    ...additional
]
```

* Focus on tasks that can be solved by writing a single Python function, a single JSON object, or a regular expression.
* Focus on tasks that do not require writing much code

Please generate 3 objects.
"""

dataset = generate_dataset(client, model, gen_dataset_prompt)
with open("dataset.json", "w") as f:
    json.dump(dataset, f, indent=2)

# results have keys: (output, test_case, score)
results = run_eval(model, client, dataset)
print(json.dumps(results, indent=2))