import os
import finnhub
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from textblob import TextBlob
from datetime import date, timedelta

# This line is for local development, but good practice to keep
load_dotenv()

app = Flask(__name__)

# Setup Finnhub client using the API key from Render's environment variables
finnhub_client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))

# --- Helper Function for AI ---
def get_sentiment(text):
    """Analyzes text and returns a sentiment polarity score."""
    analysis = TextBlob(text)
    # Polarity is between -1 (negative) and +1 (positive)
    return analysis.sentiment.polarity

# --- API Endpoints ---

@app.route('/')
def index():
    """A simple route to confirm the API is running."""
    return "Your AI Stock API is live and running!"

@app.route('/api/company-details')
def get_company_details():
    """Fetches fundamental company profile data."""
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "A 'symbol' query parameter is required."}), 400
    try:
        profile = finnhub_client.company_profile2(symbol=symbol)
        if not profile:
             return jsonify({"error": "No data found for this symbol."}), 404
        return jsonify(profile)
    except Exception as e:
        return jsonify({"error": f"An API error occurred: {str(e)}"}), 500

@app.route('/api/news-sentiment')
def get_news_sentiment():
    """Fetches recent news and calculates average sentiment."""
    symbol = request.args.get('symbol')
    if not symbol:
        return jsonify({"error": "A 'symbol' query parameter is required."}), 400
    try:
        # Fetch news from the last 15 days
        today = date.today()
        start_date = today - timedelta(days=15)
        news_list = finnhub_client.company_news(symbol, _from=start_date.strftime("%Y-%m-%d"), to=today.strftime("%Y-%m-%d"))

        if not news_list:
            return jsonify({"symbol": symbol, "average_sentiment": 0, "news_count": 0})

        total_sentiment = 0
        # Analyze the headlines of the most recent 20 articles
        for news in news_list[:20]:
            total_sentiment += get_sentiment(news['headline'])

        average_sentiment = total_sentiment / len(news_list[:20])

        return jsonify({
            "symbol": symbol,
            "average_sentiment": round(average_sentiment, 3),
            "news_count": len(news_list[:20])
        })
    except Exception as e:
        return jsonify({"error": f"An API error occurred: {str(e)}"}), 500
