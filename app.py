import os
import requests
from bs4 import BeautifulSoup
import streamlit as st
from datetime import datetime
from google import genai

# =========================================================
# 🔑 1. READ API KEYS SECURELY FROM STREAMLIT SECRETS
# =========================================================
SCRAPERAPI_KEY = st.secrets.get("SCRAPERAPI_KEY", "")
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# =========================================================
# 2. UI CONFIGURATION & CUSTOM STYLING
# =========================================================
st.set_page_config(
    page_title="🍿 Movie Night Agent", 
    page_icon="🍿", 
    layout="centered"
)

st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    .stButton>button {
        width: 100%; background-color: #e50914; color: white;
        font-weight: bold; border-radius: 8px; padding: 12px; border: none; font-size: 16px;
    }
    .stButton>button:hover { background-color: #b20710; color: white; }
    .hero-title { text-align: center; color: #f5c518; font-weight: 900; font-size: 32px; margin-bottom: 0px; }
    .hero-sub { text-align: center; font-size: 13px; color: #a0aec0; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

# HEADER BANNER
st.markdown("<p class='hero-title'>🍿 MOVIE NIGHT AGENT</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Cinema Seat & Price Intelligence Engine</p>", unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1000&auto=format&fit=crop", 
    caption="Real-Time Theater & Consecutive Seat Finder",
    use_container_width=True
)

st.divider()

# =========================================================
# 3. USER INPUT CONTROL PANEL
# =========================================================
st.subheader("🎬 Check Available Shows & Seats")

col1, col2 = st.columns([2, 1])
with col1:
    movie_name = st.text_input("Movie Title", value="Bethlehem Kudumba Unit", placeholder="Enter movie title...")
with col2:
    city = st.selectbox("Location", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

col3, col4, col5 = st.columns([1, 1, 1])
with col3:
    today = datetime.now().date()
    selected_date = st.date_input("Date", min_value=today, value=today)
with col4:
    party_size = st.number_input("Party Size (Seats)", min_value=1, max_value=10, value=2)
with col5:
    time_window = st.selectbox("Time Window", ["Evening (6 PM - 9 PM)", "Night (9 PM+)", "Afternoon (12 PM - 4 PM)", "Morning (10 AM - 12 PM)"])

st.divider()

# =========================================================
# 4. DATA SCRAPER ENGINE
# =========================================================
def fetch_bms_raw(city_name, api_key):
    """Fetches raw webpage text via ScraperAPI."""
    target_url = f"https://in.bookmyshow.com/explore/movies-{city_name.lower()}"
    proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={target_url}&render=true"
    try:
        res = requests.get(proxy_url, timeout=60)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            return soup.get_text(separator=' ', strip=True)[:8000]
        return None
    except Exception:
        return None

# =========================================================
# 5. STRICTLY GROUNDED GEMINI AI ENGINE
# =========================================================
def analyze_and_structure_shows(raw_text, movie, city_name, party, target_date, window, key):
    """Analyzes raw data while preventing hallucinated showtimes/pricing."""
    try:
        client = genai.Client(api_key=key)
        
        prompt = f"""
        You are a strict data extraction agent for cinema bookings in {city_name}.
        Target Movie: '{movie}'
        Date Requested: {target_date.strftime('%d %b %Y')}
        Preferred Time Window: {window}
        Party Size: {party}
        
        RAW SCRAPED DATA FROM BOOKMYSHOW:
        {raw_text}
        
        STRICT INSTRUCTIONS:
        1. DO NOT fabricate, invent, or guess showtimes, ticket prices, or seat availability.
        2. Verify if the movie '{movie}' is explicitly listed in the scraped text for {city_name}.
        3. If specific theater showtimes and ticket prices are present in the text, extract them cleanly.
        4. If the scraped text ONLY contains general city directory info (lacking deep theater schedules or seat maps), clearly state:
           - Movie presence status in {city_name}.
           - A clear note explaining that live showtimes/seats require opening the specific movie URL on BookMyShow.
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating analysis: {e}"

# =========================================================
# 6. EXECUTION BUTTON & DISPLAY
# =========================================================
if st.button("🔍 SEARCH SEATS & PRICING", type="primary"):
    if not SCRAPERAPI_KEY or not GEMINI_API_KEY:
        st.error("⚠️ Please configure SCRAPERAPI_KEY and GEMINI_API_KEY in Streamlit Secrets!")
    else:
        with st.status(f"🤖 Agent scanning theaters in {city} for {selected_date.strftime('%d %b %Y')}...", expanded=True) as status:
            st.write(f"📡 Step 1: Fetching live listings for {city}...")
            raw = fetch_bms_raw(city, SCRAPERAPI_KEY)
            
            if raw:
                st.write(f"🧠 Step 2: Extracting verified data for '{movie_name}' on {selected_date.strftime('%d %b %Y')}...")
                result = analyze_and_structure_shows(raw, movie_name, city, party_size, selected_date, time_window, GEMINI_API_KEY)
                status.update(label="✅ Search Complete!", state="complete", expanded=False)
                
                st.subheader("📊 AGENT FINDINGS & SEATING ANALYSIS")
                st.markdown(result)
            else:
                status.update(label="❌ Scraping Failed", state="error")
                st.error("Failed to fetch data from BookMyShow. Please check your ScraperAPI credentials.")
        
        bms_url = f"https://in.bookmyshow.com/explore/movies-{city.lower()}"
        st.link_button(f"🎟️ Open BookMyShow ({city}) ➔", bms_url)
