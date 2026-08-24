import asyncio
import streamlit as st
from datetime import datetime
from google import genai
from tavily import TavilyClient
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# =========================================================
# 1. PAGE & API CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="🍿 Movie Night Agent", 
    page_icon="🍿", 
    layout="centered"
)

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%; background-color: #e50914; color: white;
        font-weight: bold; border-radius: 8px; padding: 12px; border: none; font-size: 16px;
    }
    .stButton>button:hover { background-color: #b20710; color: white; }
    .hero-title { text-align: center; color: #f5c518; font-weight: 900; font-size: 30px; margin-bottom: 0px; }
    .hero-sub { text-align: center; font-size: 13px; color: #a0aec0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<p class='hero-title'>🍿 MOVIE NIGHT AGENT</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Real-Time Showtimes & Local Stealth Seat Inspector</p>", unsafe_allow_html=True)
st.divider()

# =========================================================
# 2. USER INPUTS
# =========================================================
col1, col2 = st.columns([2, 1])
with col1:
    movie_name = st.text_input("Movie Title", value="Bethlehem Kudumba Unit")
with col2:
    city = st.selectbox("Location", ["Kochi", "Bengaluru", "Mumbai", "Chennai"])

col3, col4 = st.columns([1, 1])
with col3:
    today = datetime.now().date()
    selected_date = st.date_input("Date", min_value=today, value=today)
with col4:
    required_seats = st.number_input("Consecutive Seats Needed", min_value=1, max_value=10, value=3)

bms_url_input = st.text_input(
    "Optional: Direct BookMyShow Showtime URL (for deep seat inspection)",
    placeholder="https://in.bookmyshow.com/buytickets/..."
)

st.divider()

# =========================================================
# 3. CORE ENGINES
# =========================================================

def get_web_showtimes(movie, city_name, date_val, g_key, t_key):
    """Phase 1: Fast & Free Showtime Aggregation via Tavily + Gemini."""
    try:
        formatted_date = date_val.strftime('%d %B %Y')
        search_query = f"{movie} movie showtimes {city_name} {formatted_date}"
        
        # 1. Web Search
        tavily = TavilyClient(api_key=t_key)
        search_results = tavily.search(query=search_query, max_results=5)
        
        raw_text = ""
        for item in search_results.get("results", []):
            raw_text += f"\nSource: {item.get('url')}\nContent: {item.get('content')}\n---"

        # 2. Extract with Gemini (No Grounding Tool = 100% Free Quota)
        client = genai.Client(api_key=g_key)
        prompt = f"""
        Extract theater names and showtimes for '{movie}' in {city_name} on {formatted_date} from this web data:
        {raw_text}

        Format using simple Markdown bullet points grouped by Theater Name. 
        If no schedules are found, reply with "No listings found."
        """
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Showtime Search Error: {e}"


async def inspect_seats_stealth(url, seat_count):
    """Phase 2: Local Stealth Browser Engine to check seat availability."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth_async(page)

            # Route through local home residential network
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for available seat elements to render
            await page.wait_for_timeout(3000)
            
            # Extract available seat markers from the DOM grid
            available_elements = await page.locator("a._available, div._available, .seat-available").all_inner_texts()
            
            await browser.close()
            
            total_available = len(available_elements)
            has_enough = total_available >= seat_count
            
            return {
                "success": True,
                "total_available": total_available,
                "has_enough": has_enough,
                "seats": available_elements[:15] # Display preview sample
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

# =========================================================
# 4. EXECUTION CONTROLLER
# =========================================================
if st.button("🚀 EXECUTE AGENT SEARCH", type="primary"):
    if not GEMINI_API_KEY or not TAVILY_API_KEY:
        st.error("⚠️ Please configure GEMINI_API_KEY and TAVILY_API_KEY in secrets!")
    else:
        # Step 1: Showtime Discovery
        with st.status("🌐 Step 1: Aggregating theater listings via Tavily + Gemini...", expanded=True) as status:
            showtimes = get_web_showtimes(movie_name, city, selected_date, GEMINI_API_KEY, TAVILY_API_KEY)
            status.update(label="✅ Showtime Search Complete!", state="complete", expanded=False)
        
        st.subheader("📊 Theater Listings & Schedules")
        st.markdown(showtimes)

        # Step 2: Stealth Seat Inspection (If URL provided)
        if bms_url_input:
            st.divider()
            with st.status("🕵️ Step 2: Spawning Local Stealth Browser (Home IP Bypass)...", expanded=True) as status:
                seat_data = asyncio.run(inspect_seats_stealth(bms_url_input, required_seats))
                status.update(label="✅ Seat Inspection Complete!", state="complete", expanded=False)
            
            st.subheader("🎟️ Seat Matrix Availability Result")
            if seat_data.get("success"):
                if seat_data["has_enough"]:
                    st.success(f"🎉 YES! Found {seat_data['total_available']} total open seats (Enough for your group of {required_seats}).")
                else:
                    st.warning(f"⚠️ Only {seat_data['total_available']} seats remaining. Might not fit {required_seats} consecutive seats.")
            else:
                st.error(f"Could not inspect seats: {seat_data.get('error')}")

        # Checkout Link
        st.divider()
        bms_slug = movie_name.lower().replace(' ', '-')
        direct_url = bms_url_input if bms_url_input else f"https://in.bookmyshow.com/{city.lower()}/movies/{bms_slug}"
        st.link_button("🎟️ Proceed to Booking Page ➔", direct_url)
