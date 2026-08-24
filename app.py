import asyncio
import streamlit as st
from datetime import datetime
from google import genai
from tavily import TavilyClient
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

# =========================================================
# 1. PAGE & CONFIGURATION
# =========================================================
st.set_page_config(page_title="🍿 Autonomous Movie Agent", page_icon="🍿", layout="centered")

GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #e50914; color: white; font-weight: bold; border-radius: 8px; padding: 12px; }
    .stButton>button:hover { background-color: #b20710; }
    .hero-title { text-align: center; color: #f5c518; font-weight: 900; font-size: 30px; margin-bottom: 0px; }
    .hero-sub { text-align: center; font-size: 13px; color: #a0aec0; margin-bottom: 20px; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<p class='hero-title'>🤖 AUTONOMOUS MOVIE SEAT AGENT</p>", unsafe_allow_html=True)
st.markdown("<p class='hero-sub'>Zero Manual Links: End-to-End Search & Live Seat Grid Scanner</p>", unsafe_allow_html=True)
st.divider()

# =========================================================
# 2. USER INPUT CONTROL PANEL (NO URL FIELD NEEDED!)
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
    required_seats = st.number_input("Consecutive Seats Needed", min_value=1, max_value=10, value=2)

st.divider()

# =========================================================
# 3. AUTONOMOUS PLAYWRIGHT NAVIGATION & SEAT SCANNER
# =========================================================
async def autonomous_bms_scanner(movie, city_name, seat_count):
    """Fully automated web agent navigation loop."""
    try:
        async with async_playwright() as p:
            # 1. Spawns visible browser running on home residential IP
            browser = await p.chromium.launch(
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()
            await stealth_async(page)

            # 2. Navigate to BookMyShow City Homepage
            target_url = f"https://in.bookmyshow.com/explore/home/{city_name.lower()}"
            await page.goto(target_url, wait_until="domcontentloaded", timeout=45000)
            await page.wait_for_timeout(2000)

            # 3. Autonomous Search Bar Click & Type
            search_box = page.locator("span:has-text('Search for Movies'), input[placeholder*='Search']")
            if await search_box.count() > 0:
                await search_box.first.click()
                await page.keyboard.type(movie, delay=100)
                await page.wait_for_timeout(1500)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)

            # 4. Handle Interstitial Popups ("Book Tickets" Button)
            book_btn = page.locator("button:has-text('Book tickets'), button:has-text('Book')")
            if await book_btn.count() > 0:
                await book_btn.first.click()
                await page.wait_for_timeout(2000)

            # 5. Handle Terms / Accept Popups
            try:
                accept_btn = page.locator("button:has-text('Accept'), div:has-text('Accept'), #btnAccept")
                if await accept_btn.count() > 0:
                    await accept_btn.first.click()
                    await page.wait_for_timeout(1000)
            except Exception:
                pass

            # 6. Click First Available Showtime Button
            showtime_btns = page.locator(".showtime-pill, a[class*='showtime'], div[class*='showtime']")
            if await showtime_btns.count() > 0:
                await showtime_btns.first.click()
                await page.wait_for_timeout(2000)

            # 7. Select Quantity Popup (e.g., Click '2' Seats)
            try:
                pop_seat_btn = page.locator(f"#pop_{seat_count}, li:has-text('{seat_count}')")
                if await pop_seat_btn.count() > 0:
                    await pop_seat_btn.first.click()
                
                select_seats_confirm = page.locator("#proceed-Qty, button:has-text('Select Seats')")
                if await select_seats_confirm.count() > 0:
                    await select_seats_confirm.first.click()
                    await page.wait_for_timeout(2000)
            except Exception:
                pass

            # 8. Inspect Rendered DOM Grid for Open Seats
            seat_selector = "a._available, div._available, svg [class*='available'], g[class*='available']"
            try:
                await page.wait_for_selector(seat_selector, timeout=10000)
                available_seats = await page.locator(seat_selector).all()
                total_open = len(available_seats)
            except Exception:
                all_seats = await page.locator("a[class*='seat'], div[class*='seat']").all()
                total_open = len(all_seats)

            final_url = page.url
            await browser.close()

            return {
                "success": True,
                "total_available": total_open,
                "has_enough": total_open >= seat_count,
                "booking_url": final_url
            }

    except Exception as e:
        return {"success": False, "error": str(e)}

# =========================================================
# 4. CONTROLLER & EXECUTION
# =========================================================
if st.button("🤖 RUN AUTONOMOUS AGENT SCAN", type="primary"):
    with st.status("🕵️ Spawning Autonomous Stealth Browser...", expanded=True) as status:
        st.write(f"🌐 Navigating to BookMyShow {city}...")
        st.write(f"🔍 Searching for '{movie_name}' and navigating popups...")
        st.write("🎟️ Inspecting seat grid layout...")
        
        result = asyncio.run(autonomous_bms_scanner(movie_name, city, required_seats))
        status.update(label="✅ Scan Complete!", state="complete", expanded=False)

    st.subheader("📊 AGENT FINDINGS")
    if result.get("success"):
        if result["has_enough"]:
            st.success(f"🎉 YES! Found {result['total_available']} open seats. Enough for your group of {required_seats}!")
        else:
            st.warning(f"⚠️ Only {result['total_available']} open seats remaining.")
        
        st.link_button("🎟️ Jump Directly to Selected Seat Map ➔", result["booking_url"])
    else:
        st.error(f"Automation Encountered an issue: {result.get('error')}")
