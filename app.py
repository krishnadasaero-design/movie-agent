import streamlit as st
from datetime import datetime
from google import genai
from tavily import TavilyClient

# =========================================================
# 1. API CONFIGURATION & SECRETS
# =========================================================
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
TAVILY_API_KEY = st.secrets.get("TAVILY_API_KEY", "")

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
st.markdown("<p class='hero-sub'>Real-Time Verified Showtime Finder (Powered by Tavily + Gemini)</p>", unsafe_allow_html=True)

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
# 3. SEARCH & EXTRACTION ENGINE (TAVILY + GEMINI)
# =========================================================
def get_verified_showtimes(movie, city_name, date_val, window, g_key, t_key):
    """Fetches web results via Tavily for free, then extracts showtimes using Gemini Flash Lite."""
    try:
        formatted_date = date_val.strftime('%d %B %Y')
        search_query = f"{movie} movie showtimes {city_name} {formatted_date}"
        
        # Step 1: Free Tavily Search Call
        tavily_client = TavilyClient(api_key=t_key)
        search_response = tavily_client.search(query=search_query, max_results=5)
        
        # Step 2: Format Tavily Context for LLM
        raw_results = ""
        for result in search_response.get("results", []):
            raw_results += f"\nSource: {result.get('url')}\nContent: {result.get('content')}\n---"
            
        if not raw_results:
            return "No web search data returned for this query."

        # Step 3: Pass Search Data to Gemini Flash Lite (No Grounding Tool = Completely Free API Quota)
        client = genai.Client(api_key=g_key)
        prompt = f"""
        You are an assistant summarizing movie showtime data.
        Analyze the raw web search data provided below to extract exact showtimes for '{movie}' in {city_name} on {formatted_date}.

        RAW WEB SEARCH DATA:
        {raw_results}

        INSTRUCTIONS:
        1. Extract theater names, showtimes, and format tags (e.g., 2D, 3D, LUXE, Dolby Atmos, 4DX) from the data.
        2. Format output clearly using Markdown bullet points grouped by Theater Name.
        3. Filter or highlight shows matching the user's preferred time window: {window}.
        4. IF the web data does not contain clear showtimes for this date, explicitly state: "No active shows found in current web listings."
        5. DO NOT invent seat numbers or imaginary theater schedules.
        """

        response = client.models.generate_content(
            model='gemini-3.5-flash-lite',
            contents=prompt
        )
        return response.text

    except Exception as e:
        return f"Error executing showtime search: {e}"

# =========================================================
# 4. EXECUTION BUTTON & DISPLAY
# =========================================================
if st.button("🔍 SEARCH VERIFIED SHOWTIMES", type="primary"):
    if not GEMINI_API_KEY:
        st.error("⚠️ Missing GEMINI_API_KEY in Streamlit Secrets!")
    elif not TAVILY_API_KEY:
        st.error("⚠️ Missing TAVILY_API_KEY in Streamlit Secrets!")
    else:
        with st.status(f"🤖 Fetching live schedules for '{movie_name}' in {city}...", expanded=True) as status:
            st.write("🌐 Step 1: Searching web via Tavily API...")
            st.write("🧠 Step 2: Extracting schedule details via Gemini 3.5 Flash Lite...")
            results = get_verified_showtimes(movie_name, city, selected_date, time_window, GEMINI_API_KEY, TAVILY_API_KEY)
            status.update(label="✅ Search Complete!", state="complete", expanded=False)
        
        st.subheader("📊 AGENT FINDINGS & SHOWTIMES")
        st.markdown(results)
        
        # Direct link generation
        st.divider()
        bms_slug = movie_name.lower().replace(' ', '-')
        direct_url = f"https://in.bookmyshow.com/{city.lower()}/movies/{bms_slug}"
        st.link_button(f"🎟️ Open Checkout Page on BookMyShow ➔", direct_url)
