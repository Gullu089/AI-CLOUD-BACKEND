from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime

app = FastAPI(
    title="Personal XAUUSD AI Assistant",
    description="My Personal ICT Trading Analysis Assistant",
    version="2.0.0"
)


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float


class AnalysisRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str
    candles: List[Candle]


@app.get("/")
def home():
    return {
        "status": "online",
        "assistant": "XAUUSD AI Assistant",
        "message": "Your trading backend is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "time": datetime.utcnow().isoformat()
    }


@app.get("/market")
def market():
    return {
        "symbol": "XAUUSD",
        "status": "waiting_for_live_data",
        "message": "Live market data is not connected yet."
    }


@app.post("/analyze")
def analyze_market(request: AnalysisRequest):
    if not request.candles:
        return {
            "status": "error",
            "message": "No candle data received."
        }

    latest = request.candles[-1]

    return {
        "status": "data_received",
        "symbol": request.symbol,
        "timeframe": request.timeframe,
        "candles_received": len(request.candles),
        "latest_candle": latest.model_dump(),
        "analysis_status": "ICT_rules_not_configured_yet",
        "message": "Candle data received. ICT analysis engine is the next step."
    }
