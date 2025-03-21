from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import sys
import os

# Ensure the correct module path is included
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trialgpt_ranking.run_aggregation import trialgpt_aggregation  # Importing your aggregation function

app = FastAPI()

class PatientSummary(BaseModel):
    summary: str

@app.post("/match-trials")
async def match_trials(data: PatientSummary):
    try:
        patient_summary = data.summary
        
        # Load trial info (Ensure this path is correct)
        trial_info_path = "dataset/trial_info.json"
        if not os.path.exists(trial_info_path):
            raise HTTPException(status_code=500, detail="Trial info file not found!")

        with open(trial_info_path) as f:
            trial_info = json.load(f)

        # Simulate ranking process (Replace with actual function)
        ranked_trials = trialgpt_aggregation(patient_summary, trial_results={}, trial_info=trial_info, model="deepseek-70b")

        return {"ranked_trials": ranked_trials}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
