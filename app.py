import os
import requests
import re
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
st.markdown("<p class='hero-sub'>Cinema Showtime & Price Intelligence Engine</p>", unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1000&auto=format&fit=crop", 
    caption="Real-Time Theater & Showtime Verification",
    use_container_width=True
)

st.divider()

# =========================================================
# 3. USER INPUT CONTROL PANEL
# =========================================================
st.subheader("🎬 Check Available Shows")

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
# 4. TARGETED SCRAPER ENGINE
# =========================================================
def fetch_movie_schedule_raw(movie_title, city_name, api_key):
    """Dynamically converts movie name to a direct BookMyShow slug URL."""
    # Convert 'Bethlehem Kudumba Unit' to 'bethlehem-kudumba-unit'
    movie_slug = re.sub(r'[^a-zA-Z0-9\s]', '', movie_title).lower().replace(' ', '-')
    
    # Direct targeted URL format for BookMyShow movie schedules
    target_url = f"https://in.bookmyshow.com/{city_name.lower()}/movies/{movie_slug}"
    proxy_url = f"http://api.scraperapi.com?api_key={api_key}&url={target_url}&render=true"
    
    try:
        res = requests.get(proxy_url, timeout=60)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            return soup.get_text(separator=' ', strip=True)[:10000], target_url
        return None, target_url
    except Exception:
        return None, target_url

# =========================================================
# 5. STRICT GEMINI EXTRACTOR ENGINE
# =========================================================
def analyze_and_structure_shows(raw_text, movie, city_name, party, target_date, window, key):
    """Extracts strictly verified showtimes from the raw page payload."""
    try:
        client = genai.Client(api_key=key)
        
        prompt = f"""
        You are an expert cinema schedule parser for {city_name}.
        Target Movie: '{movie}'
        Date Requested: {target_date.strftime('%d %b %Y')}
        Preferred Time Window: {window}
        Party Size: {party}
        
        RAW SCRAPED DATA FROM MOVIE SCHEDULE PAGE:
        {raw_text}
        
        INSTRUCTIONS:
        1. Parse the scraped text to extract real showtimes, formats (2D, 3D, LUXE, Atmos), and theater names (e.g., PVR Lulu, Cinépolis).
        2. Filter and present shows matching the preferred time window ({window}).
        3. If specific theater showtimes ARE FOUND in the text, present them in clean cards.
        4. If the page indicates NO SHOWS AVAILABLE or page did not load showtimes, state clearly that no active listings were returned for this title on {target_date.strftime('%d %b %Y')}.
        5. DO NOT invent fake times, prices, or rows. Use only verified facts from the text.
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
if st.button("🔍 SEARCH SHOWTIMES & THEATERS", type="primary"):
    if not SCRAPERAPI_KEY or not GEMINI_API_KEY:
        st.error("⚠️ Please configure SCRAPERAPI_KEY and GEMINI_API_KEY in Streamlit Secrets!")
    else:
        with st.status(f"🤖 Fetching direct movie schedule for '{movie_name}' in {city}...", expanded=True) as status:
            st.write(f"📡 Step 1: Querying targeted movie URL via ScraperAPI...")
            raw, target_url = fetch_movie_schedule_raw(movie_name, city, SCRAPERAPI_KEY)
            
            if raw:
                st.write(f"🧠 Step 2: Parsing verified showtimes for {selected_date.strftime('%d %b %Y')}...")
                result = analyze_and_structure_shows(raw, movie_name, city, party_size, selected_date, time_window, GEMINI_API_KEY)
                status.update(label="✅ Search Complete!", state="complete", expanded=False)
                
                st.subheader("📊 AGENT FINDINGS & VERIFIED SHOWTIMES")
                st.markdown(result)
            else:
                status.update(label="❌ Scraping Failed", state="error")
                st.error(f"Could not load direct page for '{movie_name}'. Please verify the spelling or check your ScraperAPI key.")
        
        st.link_button(f"🎟️ Open Direct Movie Page on BookMyShow ➔", target_url)
