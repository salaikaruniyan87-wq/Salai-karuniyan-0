"""
Backend/main.py

FastAPI application entry point for LegalEase.
Run with:
    uvicorn main:app --reload --port 8000   (run from inside Backend/)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import router

app = FastAPI(
    title="LegalEase - AI Legal Document Generator",
    description="Generates customizable legal documents (contracts, NDAs, "
    "leases, and more) using Google's Gemini generative AI model.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def home():
    return {"message": "Welcome to LegalEase AI Legal Document Generator API"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)