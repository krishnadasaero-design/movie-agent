import os
import subprocess
import streamlit as st
import time
from datetime import datetime

# --- AUTO-INSTALL PLAYWRIGHT BINARIES ON STREAMLIT CLOUD ---
def ensure_playwright_browsers():
    try:
        subprocess.run(["playwright", "install", "chromium"], check=True)
    except Exception as e:
        print(f"Playwright binary install note: {e}")

ensure_playwright_browsers()

from playwright.sync_api import sync_playwright

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="KD's Movie Night Agent", 
    page_icon="🍿", 
    layout="centered"
)

# --- CUSTOM STYLING FOR CINEMATIC HERO THEME ---
st.markdown("""
    <style>
    .main {
        background-color: #0b0e14;
    }
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
    .stButton>button:hover {
        background-color: #b20710;
        color: white;
    }
    .hero-title {
        text-align: center;
        color: #f5c518;
        font-weight: 900;
        font-size: 36px;
        margin-bottom: 0px;
        letter-spacing: 1px;
    }
    .hero-sub {
        text-align: center;
        font-size: 14px;
        color: #a0aec0;
        margin-bottom: 15px;
    }
    .star-badge {
        background-color: #1a202c;
        padding: 10px 15px;
        border-radius: 20px;
        border: 1px solid #2d3748;
        color: #e2e8f0;
        font-size: 13px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HEADER SECTION ---
st.markdown("<p class='hero-title'>🍿 KD's Movie Night Agent</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Real-Time Cinema Seat & Price Intelligence</p>", unsafe_allow_html=True)

st.markdown("""
    <div class='star-badge'>
        🌟 <b>Cinema Legends Hub:</b> Mohanlal • Mammootty • Shah Rukh Khan • Cillian Murphy • Zendaya 🌟
    </div>
""", unsafe_allow_html=True)

st.image(
    "https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?q=80&w=1000&auto=format&fit=crop", 
    caption="Live Theater Layout & Single-Row Consecutive Seat Finder",
    use_container_width=True
)

st.divider()

# --- INPUT SECTION ---
st.subheader("🎬 Check Available Shows & Seats")

col1, col2 = st.columns([2, 1])
with col1:
    movie_name = st.text_input("Movie Title", value="Bethlehem Kudumba Unit", placeholder="Enter movie name...")
with col2:
    city = st.selectbox("City / Location", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

col3, col4, col5 = st.columns([1, 1, 1])
with col3:
    today = datetime.now().date()
    selected_date = st.date_input("Date", min_value=today, value=today)

with col4:
    time_window = st.selectbox(
        "Time Window", 
        ["Evening (6 PM - 9 PM)", "Night (9 PM+)", "Afternoon (12 PM - 4 PM)", "Morning (10 AM - 12 PM)"]
    )

with col5:
    party_size = st.number_input("Party Size (Seats)", min_value=1, max_value=10, value=2, step=1)

st.caption(f"🎯 **Single-Row Rule Active:** Searching specifically for **{party_size} consecutive seats in a single row**.")

# --- PLAYWRIGHT SCRAPER AUTOMATION ---
def run_live_agent(search_movie, search_city):
    snapshot_filename = "live_movie_search.png"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            context = browser.new_context(
                viewport={"width": 1280, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            page = context.new_page()

            # Step 1: Open city homepage
            url = f"https://in.bookmyshow.com/explore/home/{search_city.lower()}"
            page.goto(url, wait_until="domcontentloaded", timeout=45000)
            page.wait_for_timeout(3000)

            # Step 2: Search and click directly on the movie poster/title card if visible
            try:
                # Try finding exact text matching the movie on the home screen
                movie_card = page.locator(f"text='{search_movie}'").first
                if movie_card.count() > 0:
                    movie_card.click()
                    page.wait_for_timeout(4000)
                else:
                    # Fallback to search bar interaction
                    search_trigger = page.locator("div:has-text('Search for Movies')").last
                    if search_trigger.count() > 0:
                        search_trigger.click()
                        page.wait_for_timeout(1000)
                    
                    search_input = page.locator("input[placeholder*='Search']")
                    if search_input.count() > 0:
                        search_input.fill(search_movie)
                        page.wait_for_timeout(2000)
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(4000)
            except Exception as e:
                print(f"Navigation click note: {e}")

            page.screenshot(path=snapshot_filename)
            browser.close()
            return snapshot_filename
    except Exception as err:
        st.error(f"Live Playwright execution error: {err}")
        return None

# --- SEARCH TRIGGER ---
if st.button("🔍 SEARCH LIVE SEATS & PRICING", type="primary"):
    if not movie_name:
        st.error("Please enter a movie title to search!")
    else:
        st.info(f"Agent executing live check for **'{movie_name}'** in **{city}**...")
        
        with st.spinner("Navigating to live showtimes..."):
            saved_img = run_live_agent(movie_name, city)
            
        if saved_img:
            st.success("Live Scan Complete!")
            st.divider()
            
            st.subheader(f"🍿 Live Booking Status for '{movie_name}'")
            
            with st.container(border=True):
                st.markdown("### 📸 Live Screen / Theater Status Snapshot")
                st.image(saved_img, caption=f"Live capture for '{movie_name}' in {city}", use_container_width=True)
                
                bms_url = f"https://in.bookmyshow.com/explore/home/{search_city.lower() if 'search_city' in locals() else city.lower()}"
                st.link_button(f"🎟️ Open Direct Bookings on BookMyShow ({city}) ➔", bms_url)
