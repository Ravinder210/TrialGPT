from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from trialgpt_ranking.run_aggregation import trialgpt_aggregation  # Importing your aggregation function

app = FastAPI()

class PatientSummary(BaseModel):
    summary: str

@app.post("/match-trials")
async def match_trials(data: PatientSummary):
    try:
        # Use your existing ML pipeline here
        patient_summary = data.summary
        
        # Load trial info (Ensure this path is correct)
        with open("dataset/trial_info.json") as f:
            trial_info = json.load(f)

        # Simulate ranking process (Replace with actual function)
        ranked_trials = trialgpt_aggregation(patient_summary, trial_results={}, trial_info=trial_info, model="deepseek-70b")

        return {"ranked_trials": ranked_trials}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
