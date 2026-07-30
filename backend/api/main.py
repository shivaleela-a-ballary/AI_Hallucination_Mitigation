from fastapi import FastAPI
from backend.api.routes.retrieval import router

app = FastAPI(title="AI Hallucination Mitigation")

app.include_router(router)

@app.get("/")
def root():
    return {"message": "API is running"}