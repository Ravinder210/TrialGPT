__author__ = "qiao"

"""
TrialGPT-Matching main functions.
"""

import json
from nltk.tokenize import sent_tokenize
import time
import os

from together import Together

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))  # Use Together AI API

def parse_criteria(criteria):
    output = ""
    criteria = criteria.split("\n\n")

    idx = 0
    for criterion in criteria:
        criterion = criterion.strip()

        if "inclusion criteria" in criterion.lower() or "exclusion criteria" in criterion.lower():
            continue

        if len(criterion) < 5:
            continue

        output += f"{idx}. {criterion}\n"
        idx += 1

    return output


def print_trial(trial_info: dict, inc_exc: str) -> str:
    """Given a dict of trial information, returns a string of trial."""
    
    trial = f"Title: {trial_info['brief_title']}\n"
    trial += f"Target diseases: {', '.join(trial_info['diseases_list'])}\n"
    trial += f"Interventions: {', '.join(trial_info['drugs_list'])}\n"
    trial += f"Summary: {trial_info['brief_summary']}\n"
    
    if inc_exc == "inclusion":
        trial += "Inclusion criteria:\n %s\n" % parse_criteria(trial_info['inclusion_criteria'])
    elif inc_exc == "exclusion":
        trial += "Exclusion criteria:\n %s\n" % parse_criteria(trial_info['exclusion_criteria']) 

    return trial


def get_matching_prompt(trial_info: dict, inc_exc: str, patient: str) -> str:
    """Output the prompt."""
    prompt = f"You are a helpful assistant for clinical trial recruitment. Your task is to compare a given patient note and the {inc_exc} criteria of a clinical trial to determine the patient's eligibility at the criterion level.\n"

    if inc_exc == "inclusion":
        prompt += "The factors that allow someone to participate in a clinical study are called inclusion criteria...\n"
    elif inc_exc == "exclusion":
        prompt += "The factors that disqualify someone from participating are called exclusion criteria...\n"

    prompt += "You should output only a JSON dict exactly formatted as: dict{str(criterion_number): list[str(element_1_brief_reasoning), list[int(element_2_sentence_id)], str(element_3_eligibility_label)]}."
    
    user_prompt = f"Here is the patient note, each sentence is led by a sentence_id:\n{patient}\n\n" 
    user_prompt += f"Here is the clinical trial:\n{print_trial(trial_info, inc_exc)}\n\n"
    user_prompt += f"Plain JSON output:"

    return prompt, user_prompt


def trialgpt_matching(trial: dict, patient: str, model: str):
    results = {}

    for inc_exc in ["inclusion", "exclusion"]:
        system_prompt, user_prompt = get_matching_prompt(trial, inc_exc, patient)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response = client.chat.completions.create(
            model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
            messages=messages,
            temperature=0,
        )

        message = response.choices[0].message.content.strip()
        message = message.strip("`").strip("json")

        try:
            results[inc_exc] = json.loads(message)
        except:
            results[inc_exc] = message  # In case of invalid JSON response

    return results
