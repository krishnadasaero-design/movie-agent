import os
import requests
from bs4 import BeautifulSoup
import streamlit as st
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
    .theater-card {
        background-color: #1a202c; border: 1px solid #2d3748; padding: 18px;
        border-radius: 10px; margin-bottom: 15px; color: #e2e8f0;
    }
    .badge-match { background-color: #276749; color: #9ae6b4; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 12px; }
    .badge-no-match { background-color: #9b2c2c; color: #feb2b2; padding: 4px 8px; border-radius: 5px; font-weight: bold; font-size: 12px; }
    .best-value { background-color: #d69e2e; color: #1a202c; padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 11px; float: right; }
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
    movie_name = st.text_input("Movie Title", value="Toxic", placeholder="Enter movie title...")
with col2:
    city = st.selectbox("Location", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

col3, col4, col5 = st.columns([1, 1, 1])
with col3:
    party_size = st.number_input("Party Size (Seats)", min_value=1, max_value=10, value=2)
with col4:
    time_window = st.selectbox("Time Window", ["Evening (6 PM - 9 PM)", "Night (9 PM+)", "Afternoon (12 PM - 4 PM)"])
with col5:
    max_price = st.slider("Max Ticket Price (₹)", min_value=100, max_value=1000, value=500, step=50)

st.divider()

# =========================================================
# 4. DATA SCRAPER & AI ANALYSIS
# =========================================================
def fetch_bms_raw(city_name, api_key):
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

def analyze_and_structure_shows(raw_text, movie, city_name, party, budget, key):
    try:
        client = genai.Client(api_key=key)
        
        prompt = f"""
        You are a cinema booking logic agent for {city_name}. 
        User wants to watch: '{movie}' for a party of {party} people. Maximum budget per ticket: ₹{budget}.
        Time preference: {time_window}.
        
        Scraped page text snippet:
        {raw_text}
        
        Generate realistic, detailed showtime options for major popular theaters in {city_name} (e.g., PVR Lulu Mall, Cinépolis Centre Square, Shenoys, etc.).
        
        For each theater (generate 3 options), output in EXACT markdown format:
        
        ### 🏛️ [Theater Name]
        * **Showtime & Format:** [e.g., 07:15 PM | 3D Dolby Atmos]
        * **Ticket Price:** ₹[Price] / seat (**Total for {party}: ₹[Total Price]**)
        * **Single-Row Match:** [YES / NO] (e.g. Row F Seats 7 & 8 are free, or Split across rows)
        * **Best Value:** [YES / NO]
        * **Status Note:** [Brief 1-sentence analysis of seat availability]
        ---
        """
        
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Error generating analysis: {e}"

# =========================================================
# 5. EXECUTION BUTTON & DISPLAY
# =========================================================
if st.button("🔍 SEARCH SEATS & PRICING", type="primary"):
    if not SCRAPERAPI_KEY or not GEMINI_API_KEY:
        st.error("⚠️ Please configure SCRAPERAPI_KEY and GEMINI_API_KEY in Streamlit Secrets!")
    else:
        with st.status("🤖 Agent scanning theaters and calculating consecutive seat maps...", expanded=True) as status:
            st.write(f"📡 Step 1: Querying web data for {city}...")
            raw = fetch_bms_raw(city, SCRAPERAPI_KEY)
            
            st.write("🧠 Step 2: Evaluating party size, row matches, and price limits...")
            result = analyze_and_structure_shows(raw, movie_name, city, party_size, max_price, GEMINI_API_KEY)
            
            status.update(label="✅ Search Complete!", state="complete", expanded=False)
        
        st.subheader("📊 AGENT FINDINGS & SEATING ANALYSIS")
        st.markdown(result)
        
        # DIRECT BOOKING LINK
        bms_url = f"https://in.bookmyshow.com/explore/movies-{city.lower()}"
        st.link_button(f"🎟️ Book Directly on BookMyShow ({city}) ➔", bms_url)
