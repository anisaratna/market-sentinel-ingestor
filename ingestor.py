import os
import requests
import psycopg2
from transformers import pipeline

# Load API Keys dari GitHub Secrets
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
TOPIC = "Strait of Hormuz"

def fetch_and_save():
    # 1. Setup AI Engine
    print("Loading AI Model...")
    nlp_engine = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    
    # 2. Extract: Ambil data dari NewsAPI
    print(f"Fetching news for: {TOPIC}")
    url = f'https://newsapi.org/v2/everything?q={TOPIC}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=5'
    response = requests.get(url)
    articles = response.json().get('articles', [])
    
    if not articles:
        print("No articles found.")
        return

    # 3. Load: Simpan ke PostgreSQL
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for art in articles:
            sentiment = nlp_engine(art['title'][:512])[0]
            
            query = """
            INSERT INTO sentiment_history (topic, source, title, sentiment, score)
            VALUES (%s, %s, %s, %s, %s)
            """
            cur.execute(query, (TOPIC, art['source']['name'], art['title'], sentiment['label'], round(sentiment['score'], 4)))
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"✅ Success! {len(articles)} articles analyzed and saved.")
        
    except Exception as e:
        print(f"❌ Database Error: {e}")

if __name__ == "__main__":
    fetch_and_save()