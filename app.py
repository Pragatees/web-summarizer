import streamlit as st
import requests
from bs4 import BeautifulSoup
import re
from transformers import pipeline
from groq import Groq
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Web Scraper & Summarizer",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'scraped_content' not in st.session_state:
    st.session_state.scraped_content = ""
if 'summary' not in st.session_state:
    st.session_state.summary = ""
if 'url' not in st.session_state:
    st.session_state.url = ""
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'summary_title' not in st.session_state:
    st.session_state.summary_title = ""

# Initialize Summarization Pipeline
@st.cache_resource
def load_summarizer():
    return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")

summarizer = load_summarizer()

# Initialize Groq Client
api_key = "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"  # Replace with your actual Groq API key
groq_client = Groq(api_key=api_key)

# Enhanced Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap');
    
    .stApp {
        background: linear-gradient(135deg, #121212 0%, #1e1e1e 100%);
        font-family: 'Poppins', sans-serif;
        color: #e0e0e0;
    }
    .header {
        background: linear-gradient(90deg, #6B48FF 0%, #3B82F6 100%);
        padding: 2.5rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 20px rgba(0,0,0,0.4);
        animation: fadeIn 0.5s ease-in-out;
    }
    .header h1 {
        color: #ffffff;
        font-size: 2.8em;
        margin: 0;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }
    .header p {
        color: #d1d5db;
        font-size: 1.3em;
        margin: 0;
        font-weight: 300;
    }
    .content-card {
        background: linear-gradient(145deg, #1f1f1f 0%, #2a2a2a 100%);
        border-radius: 16px;
        padding: 25px;
        margin-bottom: 25px;
        box-shadow: 0 6px 15px rgba(0,0,0,0.3);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .content-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    }
    .content-card h3 {
        color: #ffffff;
        font-size: 1.8em;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .stTextInput input {
        background: #2d2d2d;
        border: 2px solid #6B48FF;
        border-radius: 8px;
        color: #ffffff;
        padding: 12px;
        font-size: 1em;
        transition: border-color 0.3s ease;
    }
    .stTextInput input:focus {
        border-color: #3B82F6;
        box-shadow: 0 0 8px rgba(59, 130, 246, 0.5);
    }
    .stButton>button {
        background: linear-gradient(90deg, #6B48FF 0%, #3B82F6 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 12px 24px;
        font-size: 1.1em;
        font-weight: 600;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .stButton>button:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.5);
    }
    .stTabs [data-baseweb="tab"] {
        background: #2d2d2d;
        color: #d1d5db;
        border-radius: 12px 12px 0 0;
        padding: 12px 24px;
        margin-right: 8px;
        font-weight: 600;
        transition: background 0.3s ease, color 0.3s ease;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #3a3a3a;
        color: #ffffff;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #6B48FF 0%, #3B82F6 100%) !important;
        color: #ffffff !important;
    }
    .sidebar .sidebar-content {
        background: #1a1a1a;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .sidebar .sidebar-content h2 {
        color: #ffffff;
        font-size: 1.6em;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .sidebar .sidebar-content p, .sidebar .sidebar-content li {
        color: #d1d5db;
        font-size: 0.95em;
        line-height: 1.6;
    }
    .chat-container {
        background: #252525;
        border-radius: 16px;
        padding: 15px;
        max-height: 450px;
        overflow-y: auto;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    .user-message {
        background: linear-gradient(135deg, #6B48FF 0%, #3B82F6 100%);
        border-radius: 20px 20px 5px 20px;
        padding: 15px;
        margin: 10px 20px 10px auto;
        max-width: 70%;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        position: relative;
        animation: slideIn 0.3s ease;
    }
    .assistant-message {
        background: linear-gradient(135deg, #4B5563 0%, #374151 100%);
        border-radius: 20px 20px 20px 5px;
        padding: 15px;
        margin: 10px auto 10px 20px;
        max-width: 70%;
        color: white;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        position: relative;
        animation: slideIn 0.3s ease;
    }
    .message-header {
        display: flex;
        align-items: center;
        margin-bottom: 8px;
    }
    .message-timestamp {
        font-size: 0.85em;
        color: #d1d5db;
        margin-left: 12px;
    }
    .copy-button {
        position: absolute;
        top: 12px;
        right: 12px;
        background: transparent;
        border: none;
        color: #ffffff;
        cursor: pointer;
        font-size: 0.9em;
        transition: color 0.3s ease;
    }
    .copy-button:hover {
        color: #60A5FA;
    }
    .chat-input-container {
        display: flex;
        align-items: center;
        background: #2d2d2d;
        border-radius: 25px;
        padding: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
        transition: box-shadow 0.3s ease;
    }
    .chat-input-container:hover {
        box-shadow: 0 6px 15px rgba(0,0,0,0.4);
    }
    .chat-input-container input {
        flex: 1;
        background: transparent;
        border: none;
        color: #ffffff;
        font-size: 1em;
        padding: 12px;
        outline: none;
    }
    .chat-input-container button {
        background: linear-gradient(90deg, #6B48FF 0%, #3B82F6 100%);
        color: white;
        border: none;
        border-radius: 15px;
        padding: 10px 20px;
        cursor: pointer;
        font-weight: 600;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .chat-input-container button:hover {
        transform: scale(1.05);
        box-shadow: 0 4px 10px rgba(59, 130, 246, 0.5);
    }
    .footer {
        text-align: center;
        color: #9ca3af;
        margin-top: 2.5rem;
        padding: 1.5rem;
        border-top: 1px solid #374151;
        font-size: 0.9em;
        font-weight: 300;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(-20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
</style>
""", unsafe_allow_html=True)

# App Title
st.markdown("""
<div class="header">
    <h1>🌐 Web Scraper & Summarizer</h1>
    <p>Extract, Summarize, and Query Web Content with AI</p>
</div>
""", unsafe_allow_html=True)

# URL Input and Summary Title
st.markdown('<div class="content-card">', unsafe_allow_html=True)
st.markdown("<h3>🔗 Input Webpage URL</h3>", unsafe_allow_html=True)
url_input = st.text_input("Enter a valid URL (e.g., https://www.bbc.com/news)", key="url_input", placeholder="https://example.com")
st.markdown("<h3>📝 Summary Title</h3>", unsafe_allow_html=True)
summary_title = st.text_input("Enter a title for the summary (optional)", key="summary_title_input", placeholder="e.g., News Article Summary")
if st.button("🚀 Scrape & Summarize", type="primary"):
    if url_input:
        st.session_state.url = url_input
        st.session_state.summary_title = summary_title if summary_title else "Untitled Summary"
        with st.spinner("📡 Scraping webpage..."):
            try:
                response = requests.get(url_input, timeout=10)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                content = ' '.join([p.text for p in soup.find_all('p')])
                content = re.sub(r'\s+', ' ', content).strip()
                if not content:
                    st.error("⚠️ No content found on the webpage.")
                    st.session_state.scraped_content = ""
                    st.session_state.summary = ""
                    st.session_state.summary_title = ""
                    st.session_state.chat_history = []
                else:
                    st.session_state.scraped_content = content
                    with st.spinner("📝 Generating summary..."):
                        max_input_length = 1000
                        summary = ""
                        if len(content) > 150:
                            chunks = [content[i:i + max_input_length] for i in range(0, len(content), max_input_length)]
                            summaries = []
                            for chunk in chunks:
                                try:
                                    max_summary_length = min(120, max(30, int(len(chunk) / 10)))
                                    summary_chunk = summarizer(chunk, max_length=max_summary_length, min_length=30, do_sample=False)
                                    summaries.append(summary_chunk[0]['summary_text'])
                                except Exception as e:
                                    summaries.append(f"Error summarizing chunk: {str(e)}")
                            summary = " ".join(summaries)
                        else:
                            summary = content
                        st.session_state.summary = summary
                    st.success("✅ Content scraped and summarized successfully!")
            except requests.RequestException as e:
                st.error(f"🌐 Error fetching URL: {e}")
                st.session_state.scraped_content = ""
                st.session_state.summary = ""
                st.session_state.summary_title = ""
                st.session_state.chat_history = []
    else:
        st.warning("⚠️ Please enter a valid URL.")
st.markdown('</div>', unsafe_allow_html=True)

# Tabs for Scraped Content, Summary, and Query Content
tab1, tab2, tab3 = st.tabs(["📄 Scraped Content", "📋 Summary", "💬 Query Content"])

# Tab 1: Scraped Content
with tab1:
    st.markdown("<h3>📄 Scraped Web Content</h3>", unsafe_allow_html=True)
    if st.session_state.scraped_content:
        st.text_area("Extracted Content", st.session_state.scraped_content, height=400, label_visibility="collapsed")
    else:
        st.info("ℹ️ No content scraped yet. Enter a URL and click 'Scrape & Summarize'.")

# Tab 2: Summary
with tab2:
    st.markdown("<h3>📋 Summarized Content</h3>", unsafe_allow_html=True)
    if st.session_state.summary and st.session_state.summary_title:
        st.markdown(f"**Title**: {st.session_state.summary_title}")
        st.markdown(f"**Summary**: {st.session_state.summary}")
    else:
        st.info("ℹ️ No summary available. Scrape a webpage first.")

# Tab 3: Query Content (Chatbot)
with tab3:
    st.markdown("<h3>💬 Query Scraped Content</h3>", unsafe_allow_html=True)
    if not st.session_state.scraped_content:
        st.info("ℹ️ Please scrape a webpage first to enable querying.")
    else:
        with st.container():
            st.markdown('<div class="chat-container">', unsafe_allow_html=True)
            for message in st.session_state.chat_history:
                timestamp = message.get("timestamp", datetime.now().strftime("%H:%M:%S"))
                if message["role"] == "user":
                    st.markdown(f"""
                    <div class="user-message">
                        <div class="message-header">
                            <span>🧑 User</span>
                            <span class="message-timestamp">{timestamp}</span>
                        </div>
                        <p>{message['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    escaped_content = message['content'].replace("'", "\\'")
                    st.markdown(f"""
                    <div class="assistant-message">
                        <div class="message-header">
                            <span>🤖 Assistant</span>
                            <span class="message-timestamp">{timestamp}</span>
                            <button class="copy-button" onclick="navigator.clipboard.writeText('{escaped_content}')">Copy</button>
                        </div>
                        <p>{message['content']}</p>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        with st.form(key="query_form", clear_on_submit=True):
            query = st.text_input("Ask about the scraped content", key="query_input", placeholder="e.g., What is the main topic?")
            submit = st.form_submit_button("🔍 Submit Query")
        
        if submit and query:
            with st.spinner("🔎 Processing query..."):
                prompt = f"""
You are an AI assistant with expertise in answering queries based on provided content. Your task is to answer the user's query using only the scraped webpage content, ensuring the response is concise, accurate, and formatted professionally.

CONTEXT:
- Scraped Content (first 2000 characters): {st.session_state.scraped_content[:2000]}...
- User Query: {query}

INSTRUCTIONS:
1. Provide a clear and concise answer (1-3 sentences) based solely on the scraped content.
2. If the query is unrelated to the content, respond with: "This query is not relevant to the scraped content. Please ask about the webpage content."
3. Maintain a professional tone and avoid speculation.
4. Format the response in markdown with a bolded header.

OUTPUT:
## Response
[Your answer here]
"""
                try:
                    completion = groq_client.chat.completions.create(
                        model="llama3-70b-8192",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=500
                    )
                    response = completion.choices[0].message.content
                except Exception as e:
                    response = f"## Response\nError generating response: {str(e)}"
                
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": query,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now().strftime("%H:%M:%S")
                })
                if len(st.session_state.chat_history) > 20:
                    st.session_state.chat_history = st.session_state.chat_history[-20:]
                st.rerun()

# Sidebar with Simplified Instructions
with st.sidebar:
    st.markdown("<h2>📚 Quick Guide</h2>", unsafe_allow_html=True)
    st.markdown("""
    **How to Use**:
    - 🔗 Enter a webpage URL (e.g., https://www.bbc.com).
    - 📝 Add an optional summary title.
    - 🚀 Click "Scrape & Summarize".
    - 📄 View content, summary, or query using tabs.

    **Tips**:
    - Use news or blog URLs for best results.
    - Ask specific questions in the query tab.
    - Ensure URL includes `http://` or `https://`.
    """)

# Footer
st.markdown("""
<div class="footer">
    Powered by Streamlit, BeautifulSoup, Transformers, and Groq AI<br>
    © 2025 Web Scraper & Summarizer
</div>
""", unsafe_allow_html=True)