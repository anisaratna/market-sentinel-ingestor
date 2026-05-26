import os
import requests
import psycopg2
from transformers import pipeline

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
TOPICS = ["Strait of Hormuz", 
    "AI Semiconductor", 
    "Global Inflation"]

def fetch_and_save():
    print("📦 Loading FinBERT AI Model...")
    nlp_engine = pipeline("sentiment-analysis", model="ProsusAI/finbert")
    
    try:
        conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        
        for topic in TOPICS:
            print(f"🔍 Fetching top 20 news for: {topic}")
            url = f'https://newsapi.org/v2/everything?q={topic}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=20'
            
            response = requests.get(url)
            articles = response.json().get('articles', [])
            
            added_count = 0
            for art in articles:
                # AI Analysis
                sentiment = nlp_engine(art['title'][:512])[0]
                
                # SQL dengan De-duplication (ON CONFLICT DO NOTHING)
                # Artinya: Jika judul & topik sudah ada di DB, jangan simpan lagi.
                query = """
                INSERT INTO sentiment_history (topic, source, title, sentiment, score)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (topic, title) DO NOTHING; 
                """
                cur.execute(query, (topic, art['source']['name'], art['title'], sentiment['label'], round(sentiment['score'], 4)))
                if cur.rowcount > 0:
                    added_count += 1
            
            print(f"✅ {topic}: Berhasil menambah {added_count} berita baru (mengabaikan duplikat).")

        conn.commit()
        cur.close()
        conn.close()
        print("🚀 PIPELINE SUCCESSFUL!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    fetch_and_save()
