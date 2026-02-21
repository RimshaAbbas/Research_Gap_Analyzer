import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import httpx
from dotenv import load_dotenv
from openai import OpenAI
from tavily import TavilyClient

# --- 1. CORE SETUP ---
load_dotenv()

OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_KEY = os.getenv("TAVILY_API_KEY")

if not all([OPENROUTER_KEY, TAVILY_KEY]):
    st.error("Missing API Keys! Ensure they are in your Streamlit Secrets.")
    st.stop()

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

# --- 2. RESPONSIVE THEME (Optimized for Mobile & Laptop) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&family=Lexend:wght@700&display=swap');

    /* Global Base */
    .main { background-color: #f8faff; font-family: 'Inter', sans-serif; }
    
    /* Laptop Padding */
    [data-testid="stMainBlockContainer"] { 
        padding: 2rem 5rem !important; 
        max-width: 1200px; 
        margin: auto;
    }

    /* Blue Sidebar Styling */
    [data-testid="stSidebar"] { border-right: 5px solid #0052cc !important; background-color: #ffffff; }
    
    /* Hero Section - Optimized for Fluidity */
    .hero-section {
        background: linear-gradient(135deg, #0052cc 0%, #003366 100%);
        padding: 40px 20px;
        border-radius: 25px;
        color: white;
        text-align: center;
        margin-bottom: 30px;
        box-shadow: 0 10px 30px rgba(0,82,204,0.2);
    }

    /* Fix for text breaking on mobile */
    .hero-section h1 { 
        font-family: 'Lexend', sans-serif; 
        font-size: clamp(1.8rem, 5vw, 3.5rem) !important; 
        color: white !important; 
        margin: 0;
        line-height: 1.2;
    }
    
    .hero-section p {
        font-size: clamp(0.9rem, 2vw, 1.2rem);
        opacity: 0.9;
        margin-top: 10px;
    }

    .report-card {
        background: white;
        border-radius: 20px;
        border-left: 15px solid #0052cc;
        padding: 25px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        color: #1e293b;
        line-height: 1.6;
    }

    /* High-Visibility Labels */
    label[data-testid="stWidgetLabel"] p {
        font-size: clamp(1.2rem, 3vw, 1.8rem) !important; 
        font-weight: 700 !important;
        color: #003366 !important;
    }

    /* --- MOBILE SPECIFIC OVERRIDES --- */
    @media (max-width: 768px) {
        [data-testid="stMainBlockContainer"] { padding: 1rem 0.8rem !important; }
        
        .hero-section { 
            padding: 30px 15px; 
            border-radius: 15px;
            margin-bottom: 20px;
        }
        
        /* Adjusting report card for narrow screens */
        .report-card { 
            padding: 15px; 
            border-left-width: 8px; 
            font-size: 0.9rem;
        }

        /* Tabs font size */
        button[data-baseweb="tab"] p { font-size: 0.9rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LOGIC ENGINES ---

def get_arxiv_links(query):
    clean_query = query[:70].replace(".pdf", "").replace("_", " ")
    url = f"http://export.arxiv.org/api/query?search_query=all:{clean_query}&max_results=3"
    try:
        response = requests.get(url, timeout=10)
        root = ET.fromstring(response.text)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        return [{"title": e.find('atom:title', ns).text.strip(), "link": e.find('atom:id', ns).text} for e in root.findall('atom:entry', ns)]
    except: return []

def scout_idea_with_tavily(idea_text):
    try:
        search_results = tavily.search(query=idea_text, search_depth="advanced", max_results=5)
        context = "\n".join([f"Source: {r['url']}\nContent: {r['content']}" for r in search_results['results']])
        
        response = ai_client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": "Analyze research gaps and novelty."},
                {"role": "user", "content": f"Idea: {idea_text}\n\nContext:\n{context}"}
            ]
        )
        return response.choices[0].message.content, search_results['results']
    except Exception as e:
        return f"⚠️ Error: {str(e)}", []

def process_document(doc_input, input_type="file"):
    try:
        name = doc_input if input_type == "url" else doc_input.name
        response = ai_client.chat.completions.create(
            model="google/gemini-2.0-flash-001",
            messages=[
                {"role": "system", "content": "Extract technical milestones and novelty."},
                {"role": "user", "content": f"Analyze: {name}"}
            ]
        )
        return response.choices[0].message.content, name
    except Exception as e: return f"⚠️ Error: {str(e)}", "Error"

# --- 4. DASHBOARD UI ---

with st.sidebar:
    st.markdown("## 🏢 RESEARCH ANALYZER")
    st.caption("Hackathon Project By RimshaAbbas Group")
    st.divider()
    if st.button("🔄 Reset Workspace"): st.rerun()

st.markdown("""
<div class="hero-section">
    <h1>Vanguard Research AI</h1>
    <p>Identifying research gaps today to architect the innovations of tomorrow.</p>
</div>
""", unsafe_allow_html=True)

tab_doc, tab_scout = st.tabs(["📄 Document Analysis", "📡 Enhance Idea"])

with tab_doc:
    mode = st.radio("Source", ["File Upload", "Remote URL"], horizontal=True)
    src = st.file_uploader("Upload PDF", type=["pdf"]) if mode == "File Upload" else st.text_input("Paper URL")
    
    if st.button("GENERATE REPORT"):
        if src:
            with st.spinner("Analyzing..."):
                rep, d_name = process_document(src, "url" if mode == "Remote URL" else "file")
                st.markdown(f'<div class="report-card">{rep}</div>', unsafe_allow_html=True)
                links = get_arxiv_links(d_name)
                if links:
                    st.markdown("### 🔗 Academic References")
                    for l in links: st.info(f"**{l['title']}**\n[View Paper]({l['link']})")
        else: st.error("Provide a document.")

with tab_scout:
    idea = st.text_area("Your Research Idea:", height=150)
    if st.button("SCOUT PRIOR WORK"):
        if idea:
            with st.spinner("Scouting..."):
                report, sources = scout_idea_with_tavily(idea)
                st.markdown(f'<div class="report-card">{report}</div>', unsafe_allow_html=True)
                
                st.markdown("### 🔗 Recommended Sources")
                for s in sources:
                    st.info(f"**Web: {s['title']}**\n[Link]({s['url']})")
                
                a_links = get_arxiv_links(idea)
                for al in a_links:
                    st.success(f"**Paper: {al['title']}**\n[Link]({al['link']})")
        else: st.error("Enter an idea.")

st.markdown("<div style='text-align: center; color: #94a3b8; margin-top: 50px;'>Vanguard AI @ RimshaAbbas</div>", unsafe_allow_html=True)
