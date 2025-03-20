__author__ = "qiao"

"""
Running the TrialGPT matching for three cohorts (sigir, TREC 2021, TREC 2022).
"""

import json
from nltk.tokenize import sent_tokenize
import os
import sys
from TrialGPT import trialgpt_matching

if __name__ == "__main__":
    corpus = sys.argv[1]
    model = sys.argv[2]

    dataset = json.load(open(f"dataset/{corpus}/retrieved_trials.json"))

    output_path = f"results/matching_results_{corpus}_{model}.json"

    # Dict{Str(patient_id): Dict{Str(label): Dict{Str(trial_id): Str(output)}}}
    if os.path.exists(output_path):
        output = json.load(open(output_path))
    else:
        output = {}

    for instance in dataset:
        patient_id = instance["patient_id"]
        patient = instance["patient"]
        sents = sent_tokenize(patient)
        sents.append("The patient will provide informed consent and comply with the trial protocol.")
        sents = [f"{idx}. {sent}" for idx, sent in enumerate(sents)]
        patient = "\n".join(sents)

        if patient_id not in output:
            output[patient_id] = {"0": {}, "1": {}, "2": {}}

        for label in ["2", "1", "0"]:
            if label not in instance:
                continue

            for trial in instance[label]:
                trial_id = trial["NCTID"]

                if trial_id in output[patient_id][label]:  # Skip already processed trials
                    continue

                try:
                    results = trialgpt_matching(trial, patient, model)
                    output[patient_id][label][trial_id] = results

                    with open(output_path, "w") as f:
                        json.dump(output, f, indent=4)

                except Exception as e:
                    print(e)
                    continue
