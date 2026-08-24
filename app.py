import asyncio
import streamlit as st
from datetime import datetime
from google import genai
from tavily import TavilyClient
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# =========================================================
# 1. APPLICATION & SECRETS CONFIGURATION
# =========================================================
st.set_page_config(
    page_title="🍿 Movie Night Agent", 
    page_icon="🍿", 
    layout="centered"
)

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

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
# 2. USER CONTROL PANEL
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
    "Direct BookMyShow Showtime URL (Required for seat matrix check)",
    placeholder="https://in.bookmyshow.com/buytickets/..."
)

st.divider()

# =========================================================
# 3. AGENT ENGINES
# =========================================================

def get_web_showtimes(movie, city_name, date_val, g_key, t_key):
    """Phase 1: High-level showtime discovery using Tavily + Gemini."""
    try:
        formatted_date = date_val.strftime('%d %B %Y')
        search_query = f"{movie} movie showtimes {city_name} {formatted_date}"
        
        # 1. Fetch search data
        tavily = TavilyClient(api_key=t_key)
        search_results = tavily.search(query=search_query, max_results=5)
        
        raw_text = ""
        for item in search_results.get("results", []):
            raw_text += f"\nSource: {item.get('url')}\nContent: {item.get('content')}\n---"

        # 2. Process plain text with Gemini
        client = genai.Client(api_key=g_key)
        prompt = f"""
        Extract theater names and showtimes for '{movie}' in {city_name} on {formatted_date} from this raw search data:
        {raw_text}

        Format using Markdown bullet points grouped by Theater Name. 
        If no listings are found, state "No listings found."
        """
        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text
    except Exception as e:
        return f"Showtime Aggregation Error: {e}"


async def inspect_seats_stealth(url, seat_count):
    """Phase 2: Local Playwright engine to inspect dynamic DOM seat elements."""
    try:
        async with async_playwright() as p:
            # Launch local Chromium engine with automation flags disabled
            browser = await p.chromium.launch(
                headless=False,  # Runs visually to verify Cloudflare bypass
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth_async(page)

            # Route through residential connection
            await page.goto(url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(3000)
            
            # Dismiss interstitial modals
            try:
                accept_btn = page.locator("button:has-text('Accept'), div:has-text('Accept'), #btnAccept")
                if await accept_btn.count() > 0:
                    await accept_btn.first.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            try:
                select_seats_btn = page.locator("button:has-text('Select Seats'), div:has-text('Select Seats')")
                if await select_seats_btn.count() > 0:
                    await select_seats_btn.first.click()
                    await page.wait_for_timeout(1500)
            except Exception:
                pass

            # Target active available seat nodes within the rendered DOM / SVG tree
            seat_selector = "a._available, div._available, svg [class*='available'], g[class*='available'], .seat-available"
            
            try:
                await page.wait_for_selector(seat_selector, timeout=12000)
                available_elements = await page.locator(seat_selector).all()
                total_available = len(available_elements)
            except Exception:
                # Fallback selector for alternative layout structures
                all_seats = await page.locator("a[class*='seat'], div[class*='seat']").all()
                total_available = len(all_seats)

            await browser.close()
            
            return {
                "success": True,
                "total_available": total_available,
                "has_enough": total_available >= seat_count
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

# =========================================================
# 4. ORCHESTRATION & DISPLAY
# =========================================================
if st.button("🚀 EXECUTE AGENT SEARCH", type="primary"):
    if not GEMINI_API_KEY or not TAVILY_API_KEY:
        st.error("⚠️ Please configure GEMINI_API_KEY and TAVILY_API_KEY in secrets!")
    else:
        # Phase 1: Showtime Discovery
        with st.status("🌐 Phase 1: Aggregating theater listings via Tavily + Gemini...", expanded=True) as status:
            showtimes = get_web_showtimes(movie_name, city, selected_date, GEMINI_API_KEY, TAVILY_API_KEY)
            status.update(label="✅ Showtime Search Complete!", state="complete", expanded=False)
        
        st.subheader("📊 Theater Listings & Schedules")
        st.markdown(showtimes)

        # Phase 2: Stealth Seat Inspection
        if bms_url_input:
            st.divider()
            with st.status("🕵️ Phase 2: Spawning Local Stealth Browser (Home IP Bypass)...", expanded=True) as status:
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
        st.link_button("🎟️ Open Booking Page on BookMyShow ➔", direct_url)
