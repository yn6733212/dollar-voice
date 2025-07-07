import yfinance as yf
import asyncio
from edge_tts import Communicate
import os
from datetime import datetime
import pytz
import subprocess

VOICE = "he-IL-AvriNeural"
OUTPUT_FILENAME = "dollar.wav"

def split_price(value):
    shekels = int(value)
    agorot = int(round((value - shekels) * 100))
    return shekels, agorot

async def main():
    ticker = yf.Ticker("USDILS=X")
    data = ticker.history(period="1d", interval="1m")
    
    if data.empty:
        print("❌ לא נמצאו נתונים.")
        return

    last_price = round(data["
