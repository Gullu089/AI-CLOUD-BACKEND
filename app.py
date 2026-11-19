from fastapi import FastAPI

app = FastAPI(title="XAUUSD AI Assistant")

@app.get("/")
def home():
    return {
        "status": "online",
        "message": "XAUUSD AI Assistant is starting"
    }

@app.get("/health")
def health():
    return {"status": "healthy"}
