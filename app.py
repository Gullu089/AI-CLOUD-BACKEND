from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from collections import defaultdict

app = FastAPI(
    title="Personal XAUUSD ICT Assistant",
    description="Daily and Higher Timeframe Swing Volume Profile",
    version="3.0.0"
)


class Candle(BaseModel):
    time: str
    open: float
    high: float
    low: float
    close: float
    volume: float = 0


class AnalysisRequest(BaseModel):
    symbol: str = "XAUUSD"
    timeframe: str
    candles: List[Candle]


def calculate_profile(candles, bins=50, value_area=0.70):
    if not candles:
        return None

    lowest = min(c.low for c in candles)
    highest = max(c.high for c in candles)

    if highest <= lowest:
        return None

    step = (highest - lowest) / bins
    volumes = [0.0] * bins

    for candle in candles:
        typical_price = (
            candle.high + candle.low + candle.close
        ) / 3

        index = int((typical_price - lowest) / step)
        index = min(index, bins - 1)

        volumes[index] += candle.volume

    total_volume = sum(volumes)

    if total_volume <= 0:
        return {
            "status": "missing_volume",
            "message": "Valid volume data is required."
        }

    poc_index = volumes.index(max(volumes))
    target_volume = total_volume * value_area

    selected = {poc_index}
    accumulated = volumes[poc_index]
    left = poc_index - 1
    right = poc_index + 1

    while accumulated < target_volume:
        left_volume = volumes[left] if left >= 0 else -1
        right_volume = volumes[right] if right < bins else -1

        if left_volume < 0 and right_volume < 0:
            break

        if right_volume > left_volume:
            selected.add(right)
            accumulated += volumes[right]
            right += 1
        else:
            selected.add(left)
            accumulated += volumes[left]
            left -= 1

    vah_index = max(selected)
    val_index = min(selected)

    price_at = lambda index: lowest + (index + 0.5) * step

    return {
        "status": "calculated",
        "POC": round(price_at(poc_index), 2),
        "VAH": round(lowest + (vah_index + 1) * step, 2),
        "VAL": round(lowest + val_index * step, 2),
        "total_volume": total_volume,
        "price_bins": bins
    }


def daily_profiles(candles):
    days = defaultdict(list)

    for candle in candles:
        day = candle.time[:10]
        days[day].append(candle)

    return {
        day: calculate_profile(items)
        for day, items in days.items()
    }


def find_swings(candles, left=3, right=3):
    highs = []
    lows = []

    for i in range(left, len(candles) - right):
        current = candles[i]

        previous = candles[i-left:i]
        following = candles[i+1:i+right+1]

        if all(current.high > c.high for c in previous + following):
            highs.append({
                "index": i,
                "price": current.high,
                "time": current.time
            })

        if all(current.low < c.low for c in previous + following):
            lows.append({
                "index": i,
                "price": current.low,
                "time": current.time
            })

    return highs, lows


def swing_profile(candles, timeframe):
    highs, lows = find_swings(candles)

    swings = []

    for high in highs:
        for low in lows:
            if high["index"] < low["index"]:
                swings.append({
                    "start": high["index"],
                    "end": low["index"],
                    "type": "high_to_low",
                    "high": high["price"],
                    "low": low["price"]
                })

            elif low["index"] < high["index"]:
                swings.append({
                    "start": low["index"],
                    "end": high["index"],
                    "type": "low_to_high",
                    "high": high["price"],
                    "low": low["price"]
                })

    swings.sort(key=lambda x: x["end"])

    results = []

    for swing in swings[-5:]:
        section = candles[swing["start"]:swing["end"] + 1]

        results.append({
            "timeframe": timeframe,
            "swing": swing,
            "volume_profile": calculate_profile(section)
        })

    return {
        "swing_highs": highs,
        "swing_lows": lows,
        "profiles": results
    }


@app.get("/")
def home():
    return {
        "status": "online",
        "assistant": "XAUUSD ICT Assistant",
        "version": "3.0.0"
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
        "status": "waiting_for_live_data"
    }


@app.post("/analyze")
def analyze_market(request: AnalysisRequest):
    candles = request.candles

    if not candles:
        return {
            "status": "error",
            "message": "No candle data received."
        }

    if any(c.volume < 0 for c in candles):
        return {
            "status": "error",
            "message": "Volume cannot be negative."
        }

    timeframe = request.timeframe.upper()

    result = {
        "status": "data_received",
        "symbol": request.symbol,
        "timeframe": timeframe,
        "candles_received": len(candles),
        "daily_volume_profile": daily_profiles(candles)
    }

    if timeframe in ["1H", "H1", "60M", "60"]:
        result["swing_volume_profile"] = swing_profile(
            candles, "1H"
        )

    elif timeframe in ["4H", "H4", "240M", "240"]:
        result["swing_volume_profile"] = swing_profile(
            candles, "4H"
        )

    else:
        result["swing_volume_profile"] = {
            "status": "not_enabled_for_this_timeframe",
            "message": "Send 1H or 4H candles for swing profiles."
        }

    return result
