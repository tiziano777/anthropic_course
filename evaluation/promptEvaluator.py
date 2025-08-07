import json
import concurrent.futures
import re
import logging

logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

from textwrap import dedent
from statistics import mean
from chat_template.chat_functions import chat, add_assistant_message, add_user_message

# PromptEvaluator Implementation
class PromptEvaluator:
    def __init__(self, model, client, max_concurrent_tasks=3):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.client=client
        self.model=model

    def render(self, template_string, variables):
        placeholders = re.findall(r"{([^{}]+)}", template_string)

        result = template_string
        for placeholder in placeholders:
            if placeholder in variables:
                result = result.replace(
                    "{" + placeholder + "}", str(variables[placeholder])
                )

        return result.replace("{{", "{").replace("}}", "}")

    # Report Builder
    def generate_prompt_evaluation_report(evaluation_results):
        total_tests = len(evaluation_results)
        scores = [result["score"] for result in evaluation_results]
        avg_score = mean(scores) if scores else 0
        max_possible_score = 10
        pass_rate = (
            100 * len([s for s in scores if s >= 7]) / total_tests
            if total_tests
            else 0
        )

        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Prompt Evaluation Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                }}
                .header {{
                    background-color: #f0f0f0;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .summary-stats {{
                    display: flex;
                    justify-content: space-between;
                    flex-wrap: wrap;
                    gap: 10px;
                }}
                .stat-box {{
                    background-color: #fff;
                    border-radius: 5px;
                    padding: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    flex-basis: 30%;
                    min-width: 200px;
                }}
                .stat-value {{
                    font-size: 24px;
                    font-weight: bold;
                    margin-top: 5px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 20px;
                }}
                th {{
                    background-color: #4a4a4a;
                    color: white;
                    text-align: left;
                    padding: 12px;
                }}
                td {{
                    padding: 10px;
                    border-bottom: 1px solid #ddd;
                    vertical-align: top;
                }}
                tr:nth-child(even) {{
                    background-color: #f9f9f9;
                }}
                .output-cell {{
                    white-space: pre-wrap;
                }}
                .score {{
                    font-weight: bold;
                    padding: 5px 10px;
                    border-radius: 3px;
                    display: inline-block;
                }}
                .score-high {{
                    background-color: #c8e6c9;
                    color: #2e7d32;
                }}
                .score-medium {{
                    background-color: #fff9c4;
                    color: #f57f17;
                }}
                .score-low {{
                    background-color: #ffcdd2;
                    color: #c62828;
                }}
                .output {{
                    overflow: auto;
                    white-space: pre-wrap;
                }}

                .output pre {{
                    background-color: #f5f5f5;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 0;
                    font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.4;
                    color: #333;
                    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
                    overflow-x: auto;
                    white-space: pre-wrap; 
                    word-wrap: break-word; 
                }}

                td {{
                    width: 20%;
                }}
                .score-col {{
                    width: 80px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Prompt Evaluation Report</h1>
                <div class="summary-stats">
                    <div class="stat-box">
                        <div>Total Test Cases</div>
                        <div class="stat-value">{total_tests}</div>
                    </div>
                    <div class="stat-box">
                        <div>Average Score</div>
                        <div class="stat-value">{avg_score:.1f} / {max_possible_score}</div>
                    </div>
                    <div class="stat-box">
                        <div>Pass Rate (≥7)</div>
                        <div class="stat-value">{pass_rate:.1f}%</div>
                    </div>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th>Scenario</th>
                        <th>Prompt Inputs</th>
                        <th>Solution Criteria</th>
                        <th>Output</th>
                        <th>Score</th>
                        <th>Reasoning</th>
                    </tr>
                </thead>
                <tbody>
        """

        for result in evaluation_results:
            prompt_inputs_html = "<br>".join(
                [
                    f"<strong>{key}:</strong> {value}"
                    for key, value in result["test_case"]["prompt_inputs"].items()
                ]
            )

            criteria_string = "<br>• ".join(
                result["test_case"]["solution_criteria"]
            )

            score = result["score"]
            if score >= 8:
                score_class = "score-high"
            elif score <= 5:
                score_class = "score-low"
            else:
                score_class = "score-medium"

            html += f"""
                <tr>
                    <td>{result["test_case"]["scenario"]}</td>
                    <td class="prompt-inputs">{prompt_inputs_html}</td>
                    <td class="criteria">• {criteria_string}</td>
                    <td class="output"><pre>{result["output"]}</pre></td>
                    <td class="score-col"><span class="score {score_class}">{score}</span></td>
                    <td class="reasoning">{result["reasoning"]}</td>
                </tr>
            """

        html += """
                </tbody>
            </table>
        </body>
        </html>
        """

        return html

    def generate_unique_ideas(
        self, task_description, prompt_inputs_spec, num_cases
    ):
        """Generate a list of unique ideas for test cases based on the task description"""

        prompt = """
        Generate {num_cases} unique, diverse ideas for testing a prompt that accomplishes this task:
        
        <task_description>
        {task_description}
        </task_description>

        The prompt will receive the following inputs
        <prompt_inputs>
        {prompt_inputs_spec}
        </prompt_inputs>
        
        Each idea should represent a distinct scenario or example that tests different aspects of the task.
        
        Output Format:
        Provide your response as a structured JSON array where each item is a brief description of the idea.
        
        Example:
        ```json
        [
            "Testing with technical computer science terminology",
            "Testing with medical research findings",
            "Testing with complex mathematical concepts",
            ...
        ]
        ```
        
        Ensure each idea is:
        - Clearly distinct from the others
        - Relevant to the task description
        - Specific enough to guide generation of a full test case
        - Quick to solve without requiring extensive computation or multi-step processing
        - Solvable with no more than 400 tokens of output

        Remember, only generate {num_cases} unique ideas
        """

        system_prompt = "You are a test scenario designer specialized in creating diverse, unique testing scenarios."

        example_prompt_inputs = ""
        for key, value in prompt_inputs_spec.items():
            val = value.replace("\n", "\\n")
            example_prompt_inputs += f'"{key}": str # {val},'

        rendered_prompt = self.render(
            dedent(prompt),
            {
                "task_description": task_description,
                "num_cases": num_cases,
                "prompt_inputs": example_prompt_inputs,
            },
        )

        messages = []
        add_user_message(messages, rendered_prompt)
        add_assistant_message(messages, "```json")
        text = chat(self.model, self.client, messages, stop_sequences=["```"], system=system_prompt, temperature=1.0)

        return json.loads(text)

    def generate_test_case(self, task_description, idea, prompt_inputs_spec={}):
        """Generate a single test case based on the task description and a specific idea"""

        example_prompt_inputs = ""
        for key, value in prompt_inputs_spec.items():
            val = value.replace("\n", "\\n")
            example_prompt_inputs += f'"{key}": "EXAMPLE_VALUE", // {val}\n'

        allowed_keys = ", ".join(
            [f'"{key}"' for key in prompt_inputs_spec.keys()]
        )

        prompt = """
        Generate a single detailed test case for a prompt evaluation based on:
        
        <task_description>
        {task_description}
        </task_description>
        
        <specific_idea>
        {idea}
        </specific_idea>
        
        <allowed_input_keys>
        {allowed_keys}
        </allowed_input_keys>
        
        Output Format:
        ```json
        {{
            "prompt_inputs": {{
            {example_prompt_inputs}
            }},
            "solution_criteria": ["criterion 1", "criterion 2", ...] // Concise list of criteria for evaluating the solution, 1 to 4 items
        }}
        ```
        
        IMPORTANT REQUIREMENTS:
        - You MUST ONLY use these exact input keys in your prompt_inputs: {allowed_keys}        
        - Do NOT add any additional keys to prompt_inputs
        - All keys listed in allowed_input_keys must be included in your response
        - Make the test case realistic and practically useful
        - Include measurable, concise solution criteria
        - The solution criteria should ONLY address the direct requirements of the task description and the generated prompt_inputs
        - Avoid over-specifying criteria with requirements that go beyond the core task
        - Keep solution criteria simple, focused, and directly tied to the fundamental task
        - The test case should be tailored to the specific idea provided
        - Quick to solve without requiring extensive computation or multi-step processing
        - Solvable with no more than 400 tokens of output
        - DO NOT include any fields beyond those specified in the output format

        Here's an example of a sample input with an ideal output:
        <sample_input>
        <sample_task_description>
        Extract topics out of a passage of text
        </sample_task_description>
        <sample_specific_idea>
        Testing with a text that contains multiple nested topics and subtopics (e.g., a passage about renewable energy that covers solar power economics, wind turbine technology, and policy implications simultaneously)
        </sample_specific_idea>

        <sample_allowed_input_keys>
        "content"
        </sample_allowed_input_keys>
        </sample_input>
        <ideal_output>
        ```json
        {
            "prompt_inputs": {
                "content": "The transition to renewable energy encompasses numerous interdependent dimensions. Solar photovoltaic technology has seen dramatic cost reductions, with panel efficiency improving 24% since 2010 while manufacturing costs declined by 89%, making it economically competitive with fossil fuels in many markets. Concurrently, wind energy has evolved through innovative turbine designs featuring carbon-fiber composite blades and advanced control systems that increase energy capture by 35% in low-wind conditions."
            },
            "solution_criteria": [
                "Includes all topics mentioned"   
            ]
        }
        ```
        </ideal_output>
        This is ideal output because the solution criteria is concise and doesn't ask for anything outside of the scope of the task description.
        """

        system_prompt = "You are a test case creator specializing in designing evaluation scenarios."

        rendered_prompt = self.render(
            dedent(prompt),
            {
                "allowed_keys": allowed_keys,
                "task_description": task_description,
                "idea": idea,
                "example_prompt_inputs": example_prompt_inputs,
            },
        )

        messages = []
        add_user_message(messages, rendered_prompt)
        add_assistant_message(messages, "```json")
        text = chat(self.model, self.client, messages, stop_sequences=["```"], system=system_prompt, temperature=0.7)

        test_case = json.loads(text)
        test_case["task_description"] = task_description
        test_case["scenario"] = idea

        return test_case

    def generate_dataset(
        self,
        task_description,
        prompt_inputs_spec={},
        num_cases=1,
        output_file="dataset.json",
    ):
        """Generate test dataset based on task description and save to file"""
        ideas = self.generate_unique_ideas(
            task_description, prompt_inputs_spec, num_cases
        )

        dataset = []
        completed = 0
        total = len(ideas)
        last_reported_percentage = 0

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_concurrent_tasks
        ) as executor:
            future_to_idea = {
                executor.submit(
                    self.generate_test_case,
                    task_description,
                    idea,
                    prompt_inputs_spec,
                ): idea
                for idea in ideas
            }

            for future in concurrent.futures.as_completed(future_to_idea):
                try:
                    result = future.result()
                    completed += 1
                    current_percentage = int((completed / total) * 100)
                    milestone_percentage = (current_percentage // 20) * 20

                    if milestone_percentage > last_reported_percentage:
                        print(f"Generated {completed}/{total} test cases")
                        last_reported_percentage = milestone_percentage

                    dataset.append(result)
                except Exception as e:
                    print(f"Error generating test case: {e}")

        with open(output_file, "w") as f:
            json.dump(dataset, f, indent=2)

        return dataset

    def grade_output(self, test_case, output, extra_criteria):
        """Grade the output of a test case using the model"""

        prompt_inputs = ""
        for key, value in test_case["prompt_inputs"].items():
            val = value.replace("\n", "\\n")
            prompt_inputs += f'"{key}":"{val}",\n'

        extra_criteria_section = ""
        if extra_criteria:
            extra_criteria_template = """
            Mandatory Requirements - ANY VIOLATION MEANS AUTOMATIC FAILURE (score of 3 or lower):
            <extra_important_criteria>
            {extra_criteria}
            </extra_important_criteria>
            """
            extra_criteria_section = self.render(
                dedent(extra_criteria_template),
                {"extra_criteria": extra_criteria},
            )

        eval_template = """
        Your task is to evaluate the following AI-generated solution with EXTREME RIGOR.

        Original task description:
        <task_description>
        {task_description}
        </task_description>

        Original task inputs:
        <task_inputs>
        {{ {prompt_inputs} }}
        </task_inputs>

        Solution to Evaluate:
        <solution>
        {output}
        </solution>

        Criteria you should use to evaluate the solution:
        <criteria>
        {solution_criteria}
        </criteria>

        {extra_criteria_section}

        Scoring Guidelines:
        * Score 1-3: Solution fails to meet one or more MANDATORY requirements
        * Score 4-6: Solution meets all mandatory requirements but has significant deficiencies in secondary criteria
        * Score 7-8: Solution meets all mandatory requirements and most secondary criteria, with minor issues
        * Score 9-10: Solution meets all mandatory and secondary criteria

        IMPORTANT SCORING INSTRUCTIONS:
        * Grade the output based ONLY on the listed criteria. Do not add your own extra requirements.
        * If a solution meets all of the mandatory and secondary criteria give it a 10
        * Don't complain that the solution "only" meets the mandatory and secondary criteria. Solutions shouldn't go above and beyond - they should meet the exact listed criteria.
        * ANY violation of a mandatory requirement MUST result in a score of 3 or lower
        * The full 1-10 scale should be utilized - don't hesitate to give low scores when warranted

        Output Format
        Provide your evaluation as a structured JSON object with the following fields, in this specific order:
        - "strengths": An array of 1-3 key strengths
        - "weaknesses": An array of 1-3 key areas for improvement
        - "reasoning": A concise explanation of your overall assessment
        - "score": A number between 1-10

        Respond with JSON. Keep your response concise and direct.
        Example response shape:
        {{
            "strengths": string[],
            "weaknesses": string[],
            "reasoning": string,
            "score": number
        }}
        """

        eval_prompt = self.render(
            dedent(eval_template),
            {
                "task_description": test_case["task_description"],
                "prompt_inputs": prompt_inputs,
                "output": output,
                "solution_criteria": "\n".join(test_case["solution_criteria"]),
                "extra_criteria_section": extra_criteria_section,
            },
        )

        messages = []
        add_user_message(messages, eval_prompt)
        add_assistant_message(messages, "```json")
        eval_text = chat(self.model, self.client, messages, stop_sequences=["```"], temperature=0.0)
        return json.loads(eval_text)

    def run_test_case(
        self, test_case, run_prompt_function, extra_criteria=None
    ):
        """Run a test case and grade the result"""
        output = run_prompt_function(test_case["prompt_inputs"])

        model_grade = self.grade_output(test_case, output, extra_criteria)
        model_score = model_grade["score"]
        reasoning = model_grade["reasoning"]

        return {
            "output": output,
            "test_case": test_case,
            "score": model_score,
            "reasoning": reasoning,
        }

    def run_evaluation(
        self,
        run_prompt_function,
        dataset_file,
        extra_criteria=None,
        json_output_file="output.json",
        html_output_file="output.html",
    ):
        """Run evaluation on all test cases in the dataset"""
        with open(dataset_file, "r") as f:
            dataset = json.load(f)

        results = []
        completed = 0
        total = len(dataset)
        last_reported_percentage = 0

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_concurrent_tasks
        ) as executor:
            future_to_test_case = {
                executor.submit(
                    self.run_test_case,
                    test_case,
                    run_prompt_function,
                    extra_criteria,
                ): test_case
                for test_case in dataset
            }

            for future in concurrent.futures.as_completed(future_to_test_case):
                result = future.result()
                completed += 1
                current_percentage = int((completed / total) * 100)
                milestone_percentage = (current_percentage // 20) * 20

                if milestone_percentage > last_reported_percentage:
                    print(f"Graded {completed}/{total} test cases")
                    last_reported_percentage = milestone_percentage
                results.append(result)

        average_score = mean([result["score"] for result in results])
        print(f"Average score: {average_score}")

        with open(json_output_file, "w") as f:
            json.dump(results, f, indent=2)

        html = self.generate_prompt_evaluation_report(results)
        with open(html_output_file, "w", encoding="utf-8") as f:
            f.write(html)

        return results




#########################################################

### USAGE EXAMPLE ###

import json
from dotenv import load_dotenv
load_dotenv()

from anthropic import Anthropic

client = Anthropic()
model = "claude-sonnet-4-0"
messages = []
evaluator = PromptEvaluator(model, client, max_concurrent_tasks=1)
dataset = evaluator.generate_dataset(
    # Describe the purpose or goal of the prompt you're trying to test
    task_description="",
    # Describe the different inputs that your prompt requires
    prompt_inputs_spec={},
    # Where to write the generated dataset
    output_file="dataset.json",
    # Number of test cases to generate (recommend keeping this low if you're getting rate limit errors)
    num_cases=3,
)

def run_prompt(prompt_inputs):
    prompt = f"""
        YOUR PROMPT TO SEST
    """

    messages = []
    add_user_message(messages, prompt)
    return chat(messages)

results = evaluator.run_evaluation(
    run_prompt_function=run_prompt, dataset_file="dataset.json"
)



