from datetime import datetime
import json
import os
import sys
import traceback
from google import genai
import requests
from twelvedata import TDClient

# ==========================================
# ENVIRONMENT VARIABLES (Set in Cloud Provider)
# ==========================================
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
    print("Fetching market data for XAU/USD...")
    try:
        ts_4h = td.time_series(
            symbol="XAU/USD", interval="4h", outputsize=15
        ).with_rsi(time_period=14)
        data_4h = ts_4h.as_json()

        ts_30m = (
            td.time_series(symbol="XAU/USD", interval="30min", outputsize=15)
            .with_rsi(time_period=14)
            .with_ema(time_period=20)
        )
        data_30m = ts_30m.as_json()

        ts_5m = td.time_series(
            symbol="XAU/USD", interval="5min", outputsize=15
        ).with_rsi(time_period=14)
        data_5m = ts_5m.as_json()

        return {
            "asset": "XAU/USD (Gold)",
            "timeframes": {"4H": data_4h, "30m": data_30m, "5m": data_5m},
        }
    except Exception as e:
        print(f"Error fetching TwelveData market data: {e}")
        return None


def analyze_market_with_gemini(payload):
    print("Analyzing market structure with Gemini...")

    prompt_content = f"""
    You are an institutional trading analysis engine specialized in Gold (XAU/USD).
    Evaluate this raw market data and return strictly valid JSON matching your system schema:
    
    {json.dumps(payload)}
    """

    try:
        interaction = client.interactions.create(
            model="gemini-3.8-flash",
            input=prompt_content,
        )
        return interaction.output_text
    except Exception as e:
        print(f"\n--- GEMINI API ERROR ---\nDetails: {e}")
        traceback.print_exc()
        return None


def main():
    print(f"--- Starting Scheduled Scan: {datetime.now()} ---")
    live_data = fetch_gold_data()

    if live_data:
        trade_analysis = analyze_market_with_gemini(live_data)
        if trade_analysis:
            alert_text = (
                f"🚨 *XAU/USD LIVE TRADE SETUP* 🚨\n\n```json\n{trade_analysis}\n```"
            )
            send_telegram_alert(alert_text)


if __name__ == "__main__":
    main()
