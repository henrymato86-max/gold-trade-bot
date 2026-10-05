import os
import json
import traceback
from google import genai
import requests
from twelvedata import TDClient

# =====================================================================
# ENVIRONMENT VARIABLES (Set in Cloud Provider)
# =====================================================================
TWELVEDATA_KEY = os.getenv("TWELVEDATA_KEY")
GEMINI_KEY = os.getenv("GEMINI_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Initialize API Clients
td = TDClient(apikey=TWELVEDATA_KEY)
client = genai.Client(api_key=GEMINI_KEY)


def send_telegram_alert(message):
    """Sends formatted trade setup alerts directly to your Telegram app."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            print("[SUCCESS] Telegram alert delivered successfully.")
        else:
            print(f"[ERROR] Failed to send Telegram alert: {response.text}")
    except Exception as e:
        print(f"[ERROR] Exception sending Telegram alert: {e}")


def fetch_gold_data():
    print("Fetching macro market data for XAU/USD swing analysis...")
    try:
        # Daily Chart (Macro Trend & Major S/R)
        ts_1d = td.time_series(
            symbol="XAU/USD", interval="1day", outputsize=30
        ).with_rsi(time_period=14)
        data_1d = ts_1d.as_json()

        # 4-Hour Chart (Structural Swing Entries)
        ts_4h = (
            td.time_series(symbol="XAU/USD", interval="4h", outputsize=30)
            .with_rsi(time_period=14)
            .with_ema(time_period=50)
        )
        data_4h = ts_4h.as_json()

        # 1-Hour Chart (Execution & Refinement)
        ts_1h = td.time_series(
            symbol="XAU/USD", interval="1h", outputsize=30
        ).with_rsi(time_period=14)
        data_1h = ts_1h.as_json()

        return {
            "asset": "XAU/USD (Gold)",
            "timeframes": {"1D": data_1d, "4H": data_4h, "1H": data_1h},
        }
    except Exception as e:
        print(f"Error fetching TwelveData market data: {e}")
        return None


def analyze_market_with_gemini(payload):
    print("Analyzing market structure for swing trade opportunities...")

    prompt_content = f"""
You are an institutional macro swing trading analyst specializing in Gold (XAU/USD).
Your objective is to generate low-frequency, high-probability SWING TRADE setups meant to be held for several days to weeks.

Focus on:
1. Daily structural trend, key liquidity sweeps, and major supply/demand zones.
2. 4H and 1H market structure shifts for entry refinement.
3. Wide stop losses based on structural invalidation and targets with at least 1:3 Risk-to-Reward ratio.

Evaluate this market data and return strictly valid JSON matching your schema.

{json.dumps(payload)}
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt_content,
        )
        return response.text
    except Exception as e:
        print(f"\n--- GEMINI API ERROR ---\nDetails: {e}")
        traceback.print_exc()
        return None


def main():
    print(f"--- Starting Macro Swing Analysis Scan ---")
    live_data = fetch_gold_data()

    if live_data:
        trade_analysis = analyze_market_with_gemini(live_data)
        if trade_analysis:
            alert_text = (
                f"📊 *XAU/USD MACRO SWING SETUP* 📊\n\n{trade_analysis}\n"
            )
            send_telegram_alert(alert_text)


if __name__ == "__main__":
    main()
