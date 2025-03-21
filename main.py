from flask import Flask, jsonify, request
import json
import requests
import xml.etree.ElementTree as ET
import nltk
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from textblob import TextBlob

# Download necessary NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Analyze sentiment using TextBlob
def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.1:
        return "positive"
    elif polarity < -0.1:
        return "negative"
    else:
        return "neutral"

# Custom JSON Encoder for UTF-8 support
class CustomJSONEncoder(json.JSONEncoder):
    def __init__(self, *args, **kwargs):
        kwargs['ensure_ascii'] = False  
        super().__init__(*args, **kwargs)

# Initialize Flask app
app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False  
app.json_encoder = CustomJSONEncoder

# Initialize Flask-Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["10 per minute"]  # Set limit to 10 requests per minute per IP
)

# Define RSS feeds for various sources
def get_google_headlines(source="google"):
    feeds = {
        "google": "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
        "bbc": "http://feeds.bbci.co.uk/news/rss.xml",
        "cnn": "http://rss.cnn.com/rss/cnn_topstories.rss"
    }

    # Select the appropriate feed URL
    url = feeds.get(source.lower(), feeds["google"])

    # Set headers for HTTP request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/115.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        response = requests.get(url, headers=headers)
    except Exception as e:
        return [], f"Error making request: {str(e)}"

    if response.status_code != 200:
        error_msg = f"Error: Received status code {response.status_code}"
        return [], error_msg

    try:
        root = ET.fromstring(response.content)
    except Exception as e:
        return [], f"Error parsing XML: {str(e)}"

    headlines = []

    channel = root.find("channel")
    if channel is None:
        return [], "No channel element found in RSS feed."

    for item in channel.findall("item"):
        title_elem = item.find("title")
        if title_elem is not None and title_elem.text:
            title_text = title_elem.text.strip()
            sentiment = analyze_sentiment(title_text)
            headlines.append({"title": title_text, "sentiment": sentiment})

    return headlines[:10], None

# Route to fetch trending news with rate limit
@app.route("/trending-news", methods=["GET"])
@limiter.limit("10 per minute")  # Apply rate limit on this route
def trending_news():
    source = request.args.get("source", "google")
    headlines, error = get_google_headlines(source)
    if error:
        return jsonify({"status": "error", "message": error}), 400
    return jsonify({"status": "success", "headlines": headlines})

# Run the app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
