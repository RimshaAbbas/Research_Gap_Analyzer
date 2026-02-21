import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import httpx
from dotenv import load_dotenv
from openai import OpenAI  # OpenRouter uses OpenAI's format
from tavily import TavilyClient
import base64

# --- 1. CORE SETUP ---
load_dotenv()

# API Key Retrieval
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

# Initialization Checks
if not all([OPENROUTER_KEY, TAVILY_KEY]):
    st.error("Missing API Keys! Ensure OPENROUTER_API_KEY and TAVILY_API_KEY are in your .env file.")
    st.stop()

# Initialize Clients
# OpenRouter handles all LLM tasks (including Gemini models)
ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_KEY,
    default_headers={
        "HTTP-Referer": "http://localhost:8501", 
        "X-Title": "Vanguard AI Research Suite"
    }
)
tavily = TavilyClient(api_key=TAVILY_KEY)

st.set_page_config(page_title="Vanguard Research AI", page_icon="🔬", layout="wide")

# --- 2. PREMIUM THEME ---
st.markdown("""

    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Lexend:wght@700&display=swap');

    /* Global Desktop Padding */
    [data-testid="stMainBlockContainer"] { padding: 2rem 5rem !important; }
    .main { background-color: #f8faff; font-family: 'Inter', sans-serif; }

    /* Blue Sidebar */
    [data-testid="stSidebar"] { border-right: 5px solid #0052cc !important; background-color: #ffffff; }
    
    hr { border: none !important; height: 4px !important; background-color: #0052cc !important; opacity: 1 !important; margin: 2rem 0 !important; }

    /* Hero Section - Desktop Default */
    .hero-section {
        background: linear-gradient(135deg, #0052cc 0%, #003366 100%);
        padding: 50px 30px;
        border-radius: 30px;
        color: white;
        text-align: center;
        margin-bottom: 40px;
    }
    .hero-section h1 { font-family: 'Lexend', sans-serif; font-size: 3.2rem !important; color: white !important; margin: 0; }

    .stButton>button {
        background: #0052cc;
        color: white;
        border-radius: 12px;
        font-weight: 600;
        padding: 0.7rem 2.5rem;
        width: 100%;
        font-size: 1.2rem !important;
    }

    .report-card {
        background: white;
        border-radius: 36px;
        border-left: 25px solid #0052cc;
        padding: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        color: black;
    }

    /* Large Labels for Desktop */
    label[data-testid="stWidgetLabel"] p {
        font-size: 2.2rem !important; 
        font-weight: 700 !important;
        color: #003366 !important;
        margin-bottom: 10px !important;
    }

    /* --- MOBILE RESPONSIVENESS (Media Queries) --- */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] { padding: 1rem 1rem !important; }
        
        .hero-section { padding: 30px 15px; border-radius: 15px; }
        .hero-section h1 { font-size: 1.8rem !important; }
        .hero-section p { font-size: 0.9rem !important; }
        
        label[data-testid="stWidgetLabel"] p { font-size: 1.4rem !important; }
        
        .report-card { 
            padding: 15px; 
            border-left-width: 10px; 
            border-radius: 15px;
            font-size: 0.95rem;
        }
        
        button[data-baseweb="tab"] p { font-size: 1rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC ENGINES ---

def get_arxiv_links(query):
    """Retrieves references from ArXiv."""
    clean_query = query[:70].replace(".pdf", "").replace("_", " ")
    url = f"http://export.arxiv.org/api/query?search_query=all:{clean_query}&max_results=3"
    try:
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        return [{"title": e.find('atom:title', ns).text.strip(), "link": e.find('atom:id', ns).text} for e in root.findall('atom:entry', ns)]
    except: return []

def scout_idea_with_tavily(idea_text):
    """Uses Tavily for search and OpenRouter for analysis."""
    try:
        # 1. Search
        search_results = tavily.search(query=idea_text, search_depth="advanced", max_results=5)
        context = "\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in search_results['results']])

        # 2. Analyze via OpenRouter
        response = ai_client.chat.completions.create(
            model="google/gemini-2.0-flash-001", # Requesting Gemini via OpenRouter
            messages=[
                {"role": "system", "content": "You are a Senior Research Scout. Analyze context for research gaps."},
                {"role": "user", "content": f"Idea: {idea_text}\n\nContext:\n{context}"}
            ]
        )
        return response.choices[0].message.content, search_results['results']
    except Exception as e:
        return f"⚠️ Scouting Error: {str(e)}", []

def process_document(doc_input, input_type="file"):
    """Document analysis using OpenRouter."""
    try:
        if input_type == "url":
            content = f"Analyze the research implications of this paper found at: {doc_input}"
        else:
            content = f"Analyze the research implications of the uploaded document: {doc_input.name}"
        
        response = ai_client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": "You are a Research Strategist. Extract novelty and technical milestones."},
                {"role": "user", "content": content}
            ]
        )
        return response.choices[0].message.content
    except Exception as e: return f"⚠️ Analysis Error: {str(e)}"

# --- 4. DASHBOARD ---

with st.sidebar:
    st.markdown("## 🏢 RESEARCH GAP ANALYZER USING AI")
    st.caption("Hackathon Project By RimshaAbbas Group")
    st.divider()
    st.info("Strategic Intelligence via OpenRouter & Tavily")
    if st.button("🔄 Reset Workspace"): st.rerun()

st.markdown("""<div class="hero-section"><h1>Vanguard Research AI</h1><p>Identifying research gaps today to architect the innovations of tomorrow.</p></div>""", unsafe_allow_html=True)

tab_doc, tab_scout = st.tabs(["📄 Document Analysis", "📡 Enhance Your Idea"])

with tab_doc:
    c1, c2 = st.columns([1, 1])
    with c1: mode = st.radio("Source", ["File Upload", "Remote URL"])
    with c2:
        src = st.file_uploader("Upload PDF", type=["pdf"]) if mode == "File Upload" else st.text_input("Paper URL")
    
    if st.button("GENERATE STRATEGIC REPORT"):
        if src:
            with st.spinner("🧠 Analyzing via OpenRouter..."):
                rep = process_document(src, "url" if mode == "Remote URL" else "file")
                name_ref = src if isinstance(src, str) else src.name
                links = get_arxiv_links(name_ref)
                
                st.divider()
                st.markdown(f'<div class="report-card">{rep}</div>', unsafe_allow_html=True)
                
                if links:
                    st.markdown("### 🔗 Recommended References")
                    for l in links:
                        st.info(f"**{l['title']}** [View Paper]({l['link']})")
        else: st.error("Please Provide a Document.")

with tab_scout:
    idea = st.text_area("Describe Your Research Idea:", height=150)
    if st.button("SCOUT PRIOR WORK & GAPS"):
        if idea:
            with st.spinner("🌍 Scouting Global Data via Tavily..."):
                report, sources = scout_idea_with_tavily(idea)
                st.divider()
                col_left, col_right = st.columns([2, 1])
                with col_left:
                    st.markdown(f'<div class="report-card">{report}</div>', unsafe_allow_html=True)
                with col_right:
                    st.markdown("### 🔗 Recommended Sources")
                    for s in sources:
                        st.info(f"**{s['title']}**\n[View Source]({s['url']})")
        else: st.error("Please enter an idea.")


st.markdown("<div style='text-align: center; color: #94a3b8; margin-top: 60px; font-size: 0.9rem;'>Vanguard AI@RimshaAbbas</div>", unsafe_allow_html=True)
