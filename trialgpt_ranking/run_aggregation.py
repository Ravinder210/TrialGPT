__author__ = "qiao"

"""
Using GPT to aggregate the scores by itself.
"""

from beir.datasets.data_loader import GenericDataLoader
import json
from nltk.tokenize import sent_tokenize
import os
import sys
import time

from TrialGPT import trialgpt_aggregation

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python run_aggregation.py <corpus> <model> <matching_results_path>")
        sys.exit(1)

    corpus = sys.argv[1]
    model = sys.argv[2]
    matching_results_path = sys.argv[3]

    print(f"Loading matching results from: {matching_results_path}")

    try:
        results = json.load(open(matching_results_path))
    except Exception as e:
        print(f"Error loading matching results: {e}")
        sys.exit(1)

    trial_info_path = "dataset/trial_info.json"
    if not os.path.exists(trial_info_path):
        print(f"Error: Trial info file {trial_info_path} not found!")
        sys.exit(1)

    print(f"Loading trial info from: {trial_info_path}")
    
    try:
        trial2info = json.load(open(trial_info_path))
    except Exception as e:
        print(f"Error loading trial info: {e}")
        sys.exit(1)

    print(f"Loading patient queries from: dataset/{corpus}/")

    try:
        _, queries, _ = GenericDataLoader(data_folder=f"dataset/{corpus}/").load(split="test")
    except Exception as e:
        print(f"Error loading patient queries: {e}")
        sys.exit(1)

    output_path = f"results/aggregation_results_{corpus}_{model}.json"
    os.makedirs("results", exist_ok=True)  # Ensure output directory exists

    print(f"Output will be saved to: {output_path}")

    if os.path.exists(output_path):
        try:
            output = json.load(open(output_path))
        except Exception as e:
            print(f"Error loading existing output file: {e}")
            output = {}
    else:
        output = {}

    # Start aggregation
    for patient_id, info in results.items():
        if patient_id not in queries:
            print(f"Warning: Patient {patient_id} not found in queries. Skipping.")
            continue

        patient = queries[patient_id]
        sents = sent_tokenize(patient)
        sents.append("The patient will provide informed consent and comply with the trial protocol.")
        sents = [f"{idx}. {sent}" for idx, sent in enumerate(sents)]
        patient = "\n".join(sents)

        if patient_id not in output:
            output[patient_id] = {}

        for label, trials in info.items():
            for trial_id, trial_results in trials.items():
                if trial_id in output[patient_id]:  # Skip if already processed
                    continue

                if not isinstance(trial_results, dict):
                    print(f"Skipping {patient_id} - {trial_id}: Invalid format")
                    output[patient_id][trial_id] = "matching result error"
                    continue

                if trial_id not in trial2info:
                    print(f"Warning: Trial {trial_id} info not found. Skipping.")
                    continue

                trial_info = trial2info[trial_id]

                print(f"Processing Patient: {patient_id}, Trial: {trial_id}")

                try:
                    result = trialgpt_aggregation(patient, trial_results, trial_info, model)
                    output[patient_id][trial_id] = result

                    # Save results after every trial processing
                    with open(output_path, "w") as f:
                        json.dump(output, f, indent=4)

                    print(f"Saved result for Patient: {patient_id}, Trial: {trial_id}")

                except Exception as e:
                    print(f"Error processing Patient {patient_id}, Trial {trial_id}: {e}")
                    continue

    print(f"Aggregation complete! Results saved at {output_path}")
