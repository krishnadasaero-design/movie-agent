import os
import requests
from bs4 import BeautifulSoup
import streamlit as st
from datetime import datetime
from google import genai

# =========================================================
# 🔑 STEP 1: PASTE YOUR API KEYS HERE
# =========================================================
# Replace the text inside the quotes with your real keys
# =========================================================
# 🔑 STEP 1: READ KEYS SECURELY FROM STREAMLIT SECRETS
# =========================================================
SCRAPERAPI_KEY = st.secrets.get("SCRAPERAPI_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
# =========================================================
st.set_page_config(
    page_title="KD's AI Movie Night Agent", 
    page_icon="🍿", 
    layout="centered"
)

st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .stButton>button {
        width: 100%;
        background-color: #e50914;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 12px;
        border: none;
        font-size: 16px;
    }
    .stButton>button:hover { background-color: #b20710; color: white; }
    .hero-title { text-align: center; color: #f5c518; font-weight: 900; font-size: 36px; margin-bottom: 0px; }
    .hero-sub { text-align: center; font-size: 14px; color: #a0aec0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<p class='hero-title'>🍿 KD's AI Movie Agent</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Powered by ScraperAPI + Google Gemini 2.5 Flash</p>", unsafe_allow_html=True)
st.divider()

# =========================================================
# 3. USER INPUT CONTROL PANEL
# =========================================================
st.subheader("🎬 Query Movie Availability")

col1, col2 = st.columns([2, 1])
with col1:
    movie_name = st.text_input("Movie Title", placeholder="e.g. Toxic, Bethlehem Kudumba Unit...")
with col2:
    city = st.selectbox("City / Location", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

col3, col4 = st.columns([1, 1])
with col3:
    party_size = st.number_input("Party Size (Seats)", min_value=1, max_value=10, value=2)
with col4:
    time_window = st.selectbox("Preferred Time", ["Evening (6 PM - 9 PM)", "Night (9 PM+)", "Anytime"])

# =========================================================
# 4. SCRAPER ENGINE (BYPASSES CLOUDFLARE VIA SCRAPERAPI)
# =========================================================
def fetch_raw_bms_data(city_name, api_key):
    """Fetches clean HTML without getting blocked by Cloudflare."""
    target_url = f"https://in.bookmyshow.com/explore/movies-{city_name.lower()}"
    proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={target_url}&render=true"
    
    try:
        response = requests.get(proxy_url, timeout=60)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Extract readable text content from the DOM
            text_content = soup.get_text(separator=' ', strip=True)
            return text_content[:8000]  # Take relevant text slice for Gemini
        else:
            return None
    except Exception as e:
        st.error(f"Scraper error: {e}")
        return None

# =========================================================
# 5. GEMINI AI AGENT ENGINE (REASONING & EXTRACTION)
# =========================================================
def analyze_with_gemini(raw_text, target_movie, target_city, party, key):
    """Uses Google GenAI SDK to analyze raw data."""
    try:
        # Initialize Google GenAI client
        client = genai.Client(api_key=key)
        
        prompt = f"""
        You are an expert movie booking assistant. Analyze the following raw scraped text from BookMyShow for {target_city}.
        
        USER REQUEST:
        - Target Movie: {target_movie if target_movie else 'All Active Movies'}
        - Target City: {target_city}
        - Requested Seats: {party} consecutive seats
        
        RAW WEBPAGE DATA:
        {raw_text}
        
        INSTRUCTIONS:
        1. State clearly whether the movie '{target_movie}' is listed/playing in {target_city}.
        2. Extract a clean list of top active movie titles found in the scraped data.
        3. Provide helpful advice regarding theaters, availability, and consecutive seat booking for a party of {party}.
        4. Keep your answer clear, well-structured, and encouraging.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Gemini Processing Error: {e}"

# =========================================================
# 6. AGENT EXECUTION TRIGGER
# =========================================================
if st.button("🚀 RUN AI AGENT SEARCH", type="primary"):
    if SCRAPERAPI_KEY == "PASTE_YOUR_SCRAPERAPI_KEY_HERE" or GEMINI_API_KEY == "PASTE_YOUR_GEMINI_API_KEY_HERE":
        st.error("⚠️ Please replace the placeholder API keys at the top of your app.py script with your actual keys!")
    else:
        with st.status("🤖 Agent at work...", expanded=True) as status:
            st.write("📡 Step 1: Requesting web data via ScraperAPI (bypassing Cloudflare)...")
            raw_data = fetch_raw_bms_data(city, SCRAPERAPI_KEY)
            
            if raw_data:
                st.write("🧠 Step 2: Passing raw data to Gemini 2.5 Flash for reasoning...")
                ai_analysis = analyze_with_gemini(raw_data, movie_name, city, party_size, GEMINI_API_KEY)
                status.update(label="✅ Search Complete!", state="complete", expanded=False)
                
                st.subheader(f"📊 Agent Analysis for {city}")
                st.markdown(ai_analysis)
                
                bms_url = f"https://in.bookmyshow.com/explore/movies-{city.lower()}"
                st.link_button(f"🎟️ Open Direct Bookings on BookMyShow ({city}) ➔", bms_url)
            else:
                status.update(label="❌ Scraping Failed", state="error")
                st.error("Could not fetch data. Please check if your ScraperAPI key is valid.")
