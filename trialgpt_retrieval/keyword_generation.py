__author__ = "qiao"

"""
Generate the search keywords for each patient using Together AI.
"""

import json
import os
import sys
import re
from together import Together

# Initialize Together AI Client
client = Together(api_key=os.getenv("TOGETHER_API_KEY"))

def get_keyword_generation_messages(note):
    """Formats the input for Together AI keyword generation."""
    system = 'You are a helpful assistant. Your task is to extract medical keywords for clinical trial searches. First, summarize the patient’s main medical issues. Then generate up to 32 ranked key conditions as a JSON dict: Dict{"summary": Str(summary), "conditions": List[Str(condition)]}.'

    prompt = f"Here is the patient description: \n{note}\n\nJSON output:"

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": prompt}
    ]
    
    return messages

# Extract JSON from response
def extract_json_from_response(response_text):
    match = re.search(r'\{.*\}', response_text, re.DOTALL)  # Find JSON inside {}
    if match:
        json_str = match.group(0)  # Extract JSON
        try:
            return json.loads(json_str)  # Convert to dictionary
        except json.JSONDecodeError:
            print("Failed to parse JSON:", json_str)
            return {"summary": "", "conditions": []}  # Fallback
    else:
        print("No JSON found in response:", response_text)
        return {"summary": "", "conditions": []}  # Fallback

if __name__ == "__main__":
    # The corpus: trec_2021, trec_2022, or sigir
    corpus = sys.argv[1]

    outputs = {}

    with open(f"dataset/{corpus}/queries.jsonl", "r") as f:
        for line in f.readlines():
            entry = json.loads(line)
            messages = get_keyword_generation_messages(entry["text"])

            try:
                # Call Together AI
                response = client.chat.completions.create(
                    model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
                    messages=messages,
                    temperature=0,
                )

                # Extract valid JSON
                output = extract_json_from_response(response.choices[0].message.content)

            except Exception as e:
                print(f"Error generating keywords for {entry['_id']}: {e}")
                output = {"summary": "", "conditions": []}  # Fallback on failure

            outputs[entry["_id"]] = output

            # Save results
            with open(f"results/retrieval_keywords_{corpus}.json", "w") as f:
                json.dump(outputs, f, indent=4)
