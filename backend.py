
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "TrialGPT backend is running successfully!"}

# Required for Render
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
