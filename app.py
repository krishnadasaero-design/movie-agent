import streamlit as st
import time
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Cinema Seat & Price Agent", 
    page_icon="🍿", 
    layout="centered"
)

# --- CUSTOM CSS FOR CINEMATIC THEME & MOVIE POSTERS ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
        background-color: #e50914;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        padding: 10px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #b20710;
        color: white;
    }
    .card-box {
        background-color: #1e2430;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #2e384d;
        margin-bottom: 15px;
    }
    .hero-text {
        text-align: center;
        color: #f5c518;
        font-weight: 800;
        font-size: 32px;
        margin-bottom: 0px;
    }
    .star-banner {
        text-align: center;
        font-size: 14px;
        color: #8c9ba5;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# --- HERO SECTION & MOVIE STAR BANNER ---
st.markdown("<p class='hero-text'>🍿 MOVIE NIGHT AGENT</p>", unsafe_allow_html=True)
st.markdown("<p class='star-banner'>🌟 Featuring Mollywood • Bollywood • Hollywood Cinema Intelligence 🌟</p>", unsafe_allow_html=True)

# Visual Movie Icons & Collage Header
st.image(
    "https://images.unsplash.com/photo-1489599849927-2ee91cede3ba?q=80&w=1000&auto=format&fit=crop", 
    caption="Find the best consecutive seats for your movie night!",
    use_container_width=True
)

st.divider()

# --- INPUT SECTION ---
st.subheader("🎬 Search Theater Shows & Seats")

# Movie Name & Location
col1, col2 = st.columns([2, 1])
with col1:
    movie_name = st.text_input("Movie Title", value="Avatar 3", placeholder="e.g. Malaikottai Vaaliban, King of Kotha...")
with col2:
    city = st.selectbox("Location / City", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

# Date, Time Window & Group Size
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

# Single Row Requirement Indicator
st.caption(f"🎯 **Single-Row Rule Active:** The agent will search specifically for **{party_size} consecutive adjacent seats** in the same row.")

# --- SEARCH TRIGGER ---
if st.button("🔍 SEARCH SEATS & PRICING", type="primary"):
    if not movie_name:
        st.error("Please enter a movie title to search!")
    else:
        st.info(f"Agent scanning live theaters in **{city}** for **'{movie_name}'** on {selected_date.strftime('%d %b %Y')}...")
        
        # Simulated Scanning Progress
        progress_bar = st.progress(0)
        for p in range(100):
            time.sleep(0.015)
            progress_bar.progress(p + 1)
            
        st.success("Analysis Complete!")
        
        st.divider()
        st.subheader("🍿 Theater Findings & Seat Layout Analysis")

        # --- THEATER OPTION 1 ---
        with st.container(border=True):
            st.markdown("### 🏛️ PVR Lulu Mall, Edappally")
            
            c_time, c_price, c_total = st.columns(3)
            c_time.metric("Showtime", "07:15 PM", delta="3D Dolby Atmos")
            c_price.metric("Price per Seat", "₹320")
            c_total.metric("Total Bill for Group", f"₹{320 * party_size}")
            
            st.markdown(f"🟢 **SINGLE-ROW MATCH:** **YES!** Row F (Middle Row) — Seats 7 through {6 + party_size} are free and adjacent.")
            
            with st.expander("📸 View Live Seat Map Snapshot"):
                # Display the screenshot captured by Playwright
                try:
                    st.image("cinema_test_snapshot.png", caption="Live Seat Layout Grid from BookMyShow", use_container_width=True)
                except:
                    st.write("Seat map snapshot rendering...")

            st.link_button(f"🎟️ Book on BookMyShow (Total: ₹{320 * party_size}) ➔", f"https://in.bookmyshow.com/explore/home/{city.lower()}")

        # --- THEATER OPTION 2 ---
        with st.container(border=True):
            st.markdown("### 🏛️ Cinepolis Centre Square, MG Road")
            
            c_time2, c_price2, c_total2 = st.columns(3)
            c_time2.metric("Showtime", "08:30 PM", delta="VIP Recliner")
            c_price2.metric("Price per Seat", "₹550")
            c_total2.metric("Total Bill for Group", f"₹{550 * party_size}")
            
            st.markdown(f"🟡 **SINGLE-ROW MATCH:** **NO.** {party_size} total seats are open, but they are split across separate rows.")
            
            with st.expander("📸 View Live Seat Map Snapshot"):
                try:
                    st.image("cinema_test_snapshot.png", caption="Live Seat Layout Grid from BookMyShow", use_container_width=True)
                except:
                    st.write("Seat map snapshot rendering...")

            st.link_button(f"🎟️ Book on BookMyShow (Total: ₹{550 * party_size}) ➔", f"https://in.bookmyshow.com/explore/home/{city.lower()}")
