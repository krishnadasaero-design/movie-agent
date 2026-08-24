import streamlit as st
import time
from datetime import datetime
from google import genai
from google.genai import types
from google.genai.errors import APIError

# =========================================================
# 1. API CONFIGURATION
# =========================================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

st.set_page_config(
    page_title="🍿 Movie Night Agent", 
    page_icon="🍿", 
    layout="centered"
)

# Custom Styling
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

# Header
st.markdown("<p class='hero-title'>🍿 MOVIE NIGHT AGENT</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Real-Time Verified Showtime & Theater Finder</p>", unsafe_allow_html=True)

st.divider()

# =========================================================
# 2. USER INPUT CONTROL PANEL
# =========================================================
st.subheader("🎬 Find Shows Near You")

col1, col2 = st.columns([2, 1])
with col1:
    movie_name = st.text_input("Movie Title", value="Bethlehem Kudumba Unit", placeholder="Enter movie name...")
with col2:
    city = st.selectbox("Location", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

col3, col4 = st.columns([1, 1])
with col3:
    today = datetime.now().date()
    selected_date = st.date_input("Date", min_value=today, value=today)
with col4:
    time_window = st.selectbox("Preferred Time", ["Any Time", "Morning (10 AM - 12 PM)", "Afternoon (12 PM - 4 PM)", "Evening (5 PM - 9 PM)", "Night (9 PM+)"])

st.divider()

# =========================================================
# 3. REAL-TIME SEARCH ENGINE (WITH RETRY GUARD)
# =========================================================
def get_verified_showtimes(movie, city_name, date_val, window, api_key):
    """Fetches verified showtimes using Gemini 3.6 Flash with 429 Retry handling."""
    client = genai.Client(api_key=api_key)
    formatted_date = date_val.strftime('%d %B %Y')
    
    prompt = f"""
    Find real, active theater showtimes for the movie '{movie}' in {city_name} on {formatted_date}.
    Preferred Time Window: {window}
    
    INSTRUCTIONS:
    1. Search current theater listings (PVR, Cinépolis, local multiplexes) in {city_name} for '{movie}'.
    2. Format the response clearly using Markdown bullet points grouped by Theater Name.
    3. List exact showtimes and format tags (e.g., 2D, 3D, LUXE, Dolby Atmos, 4DX) if available.
    4. IF NO SHOWTIMES ARE FOUND for this date/movie combination, state clearly: "No active shows listed for this date."
    5. Present ONLY verified factual entries.
    """

    max_retries = 3
    delay = 10  # Wait 10 seconds if hit by a rate limit

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-3.6-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[{"google_search": {}}]
                )
            )
            return response.text
        except APIError as e:
            if "429" in str(e) and attempt < max_retries - 1:
                st.warning(f"⏳ Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                return f"⚠️ Rate Limit / API Error: {e}\n\nPlease wait 1-2 minutes before hitting search again."
        except Exception as e:
            return f"Error gathering showtime data: {e}"

# =========================================================
# 4. EXECUTION BUTTON & DISPLAY
# =========================================================
if st.button("🔍 SEARCH VERIFIED SHOWTIMES", type="primary"):
    if not GEMINI_API_KEY:
        st.error("⚠️ Please configure GEMINI_API_KEY in Streamlit Secrets!")
    else:
        with st.status(f"🤖 Searching active schedules for '{movie_name}' in {city}...", expanded=True) as status:
            st.write("🌐 Querying search engine for current multiplex listings...")
            results = get_verified_showtimes(movie_name, city, selected_date, time_window, GEMINI_API_KEY)
            status.update(label="✅ Search Complete!", state="complete", expanded=False)
        
        st.subheader("📊 AGENT FINDINGS & SHOWTIMES")
        st.markdown(results)
        
        # Direct booking link
        st.divider()
        bms_slug = movie_name.lower().replace(' ', '-')
        direct_url = f"https://in.bookmyshow.com/{city.lower()}/movies/{bms_slug}"
        st.link_button(f"🎟️ Open Checkout Page on BookMyShow ➔", direct_url)
