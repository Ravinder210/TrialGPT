
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TrialGPT backend is running successfully!"}

# Required for Render

