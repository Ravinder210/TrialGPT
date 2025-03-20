__author__ = "qiao"

"""
TrialGPT-Ranking main functions.
"""

import json
from nltk.tokenize import sent_tokenize
import time
import os
import re  # Import regex for extracting JSON
from together import Together

client = Together(api_key=os.getenv("TOGETHER_API_KEY"))  # Use Together AI API

def convert_criteria_pred_to_string(
		prediction: dict,
		trial_info: dict,
) -> str:
	"""Given the TrialGPT prediction, output the linear string of the criteria."""
	output = ""

	for inc_exc in ["inclusion", "exclusion"]:
		# First get the idx2criterion dictionary
		idx2criterion = {}
		criteria = trial_info.get(inc_exc + "_criteria", "").split("\n\n")

		idx = 0
		for criterion in criteria:
			criterion = criterion.strip()

			if "inclusion criteria" in criterion.lower() or "exclusion criteria" in criterion.lower():
				continue

			if len(criterion) < 5:
				continue

			idx2criterion[str(idx)] = criterion
			idx += 1

		for idx, info in enumerate(prediction.get(inc_exc, {}).items()):
			criterion_idx, preds = info

			if criterion_idx not in idx2criterion:
				continue

			criterion = idx2criterion[criterion_idx]

			if len(preds) != 3:
				continue

			output += f"{inc_exc} criterion {idx}: {criterion}\n"
			output += f"\tPatient relevance: {preds[0]}\n"
			if len(preds[1]) > 0:
				output += f"\tEvident sentences: {preds[1]}\n"
			output += f"\tPatient eligibility: {preds[2]}\n"

	return output


def convert_pred_to_prompt(
		patient: str,
		pred: dict,
		trial_info: dict,
) -> str:
	"""Convert the prediction to a prompt string."""
	# Get the trial description
	trial = f"Title: {trial_info.get('brief_title', 'Unknown Title')}\n"
	trial += f"Target conditions: {', '.join(trial_info.get('diseases_list', []))}\n"
	trial += f"Summary: {trial_info.get('brief_summary', 'No summary available')}"

	# Get the prediction strings
	pred = convert_criteria_pred_to_string(pred, trial_info)

	# Construct the prompt
	prompt = (
		"You are a helpful assistant for clinical trial recruitment. You will be given a patient note, "
		"a clinical trial, and the patient eligibility predictions for each criterion.\n"
		"Your task is to output two scores, a relevance score (R) and an eligibility score (E), "
		"between the patient and the clinical trial.\n"
		"First explain the consideration for determining patient-trial relevance. Predict the relevance score R (0~100), "
		"which represents the overall relevance between the patient and the clinical trial. R=0 denotes the patient is totally "
		"irrelevant to the clinical trial, and R=100 denotes the patient is exactly relevant to the clinical trial.\n"
		"Then explain the consideration for determining patient-trial eligibility. Predict the eligibility score E (-R~R), "
		"which represents the patient's eligibility to the clinical trial. Note that -R <= E <= R "
		"(the absolute value of eligibility cannot be higher than the relevance), where E=-R denotes that the patient is ineligible "
		"(not included by any inclusion criteria, or excluded by all exclusion criteria), E=R denotes that the patient is eligible "
		"(included by all inclusion criteria, and not excluded by any exclusion criteria), E=0 denotes the patient is neutral "
		"(i.e., no relevant information for all inclusion and exclusion criteria).\n"
		"Please output a JSON dict formatted as Dict{'relevance_explanation': Str, 'relevance_score_R': Float, "
		"'eligibility_explanation': Str, 'eligibility_score_E': Float}."
	)

	user_prompt = f"Here is the patient note:\n{patient}\n\n"
	user_prompt += f"Here is the clinical trial description:\n{trial}\n\n"
	user_prompt += f"Here are the criterion-level eligibility predictions:\n{pred}\n\n"
	user_prompt += "Plain JSON output:"

	return prompt, user_prompt


def extract_json_from_output(raw_output):
	"""Extract only the JSON part from the model's response."""
	match = re.search(r"\{.*\}", raw_output, re.DOTALL)  # Find first JSON block
	if match:
		return match.group(0)  # Return only the JSON content
	return None  # Return None if no valid JSON found


def trialgpt_aggregation(patient: str, trial_results: dict, trial_info: dict, model: str):
	"""Call DeepSeek API to generate aggregation results."""
	system_prompt, user_prompt = convert_pred_to_prompt(patient, trial_results, trial_info)

	messages = [
		{"role": "system", "content": system_prompt},
		{"role": "user", "content": user_prompt}
	]

	print("\n--- Debugging GPT Call ---")
	print(f"Model: {model}")
	print(f"User Prompt (first 500 chars): {user_prompt[:500]}...")
	print("---------------------------")

	try:
		response = client.chat.completions.create(
			model="deepseek-ai/DeepSeek-R1-Distill-Llama-70B-free",
			messages=messages,
			temperature=0,
		)

		raw_output = response.choices[0].message.content.strip()
		print("\n--- Raw GPT Output ---")
		print(raw_output)
		print("----------------------")

		# Extract only the JSON part
		json_text = extract_json_from_output(raw_output)

		if json_text is None:
			print("🚨 No valid JSON found in GPT output! Returning empty response.")
			return {}

		# Parse the extracted JSON
		try:
			result = json.loads(json_text)
		except json.JSONDecodeError as e:
			print("🚨 JSON Parsing Error:", e)
			print("🚨 Extracted JSON Text:", json_text)  # Debugging output
			return {}

		print("\n--- Parsed JSON Output ---")
		print(result)
		print("--------------------------")

		return result

	except Exception as e:
		print("🚨 API Call Failed:", e)
		return {}
