import streamlit as st
import os
import re
import requests
from dotenv import load_dotenv
from utils.transcript import get_transcript
from utils.article_generator import generate_article, get_language_list
from utils.pdf_generator import generate_pdf

load_dotenv()
groq_key = os.getenv("GROQ_API_KEY")
if groq_key:
    os.environ["GROQ_API_KEY"] = groq_key

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="YT → Article & PDF",
    page_icon="▶",
    layout="centered",
)

# ── Session state init ─────────────────────────────────────────────────────────
if "recent_urls"        not in st.session_state: st.session_state.recent_urls     = []
if "cached_transcript"  not in st.session_state: st.session_state.cached_transcript = None
if "cached_title"       not in st.session_state: st.session_state.cached_title    = None
if "cached_url"         not in st.session_state: st.session_state.cached_url      = None
if "last_article"       not in st.session_state: st.session_state.last_article    = None
if "last_pdf_bytes"     not in st.session_state: st.session_state.last_pdf_bytes  = None
if "regenerate"         not in st.session_state: st.session_state.regenerate      = False

# ── Helpers ────────────────────────────────────────────────────────────────────
YT_REGEX = re.compile(
    r"^(https?://)?(www\.)?"
    r"(youtube\.com/watch\?.*v=[\w\-]+|youtu\.be/[\w\-]+)"
)

def is_valid_yt_url(url: str) -> bool:
    return bool(YT_REGEX.match(url.strip()))

def add_recent_url(url: str):
    urls = st.session_state.recent_urls
    if url in urls:
        urls.remove(url)
    urls.insert(0, url)
    st.session_state.recent_urls = urls[:5]

def fetch_video_preview(url: str) -> dict | None:
    """Fetch YouTube oEmbed data — no API key needed."""
    try:
        r = requests.get(
            "https://www.youtube.com/oembed",
            params={"url": url, "format": "json"},
            timeout=5,
        )
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def get_video_id(url: str) -> str | None:
    m = re.search(r"(?:v=|youtu\.be/)([\w\-]+)", url)
    return m.group(1) if m else None

def reading_time(text: str) -> int:
    return max(1, round(len(text.split()) / 200))

def compression_ratio(transcript: str, article: str) -> str:
    tw = len(transcript.split())
    aw = len(article.split())
    if tw == 0: return "—"
    pct = round((1 - aw / tw) * 100)
    return f"{pct}% shorter"

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500&display=swap');

/* ══════════════════════════════════════════════════════════════════════════════
   CSS VARIABLES — YouTube palette, dual light/dark
══════════════════════════════════════════════════════════════════════════════ */
:root {
    --yt-red:       #FF0000;
    --yt-red-dark:  #CC0000;
    --yt-orange:    #FF6D00;

    --bg-base:      #0F0F0F;
    --bg-surface:   #181818;
    --bg-card:      #212121;
    --bg-input:     #121212;
    --border:       #303030;
    --border-focus: #FF0000;
    --text-primary: #FFFFFF;
    --text-secondary:#E0E0E0;
    --text-muted:   #AAAAAA;
    --text-hint:    #888888;
    --tag-bg:       #272727;
    --tag-text:     #E0E0E0;
    --scrollbar:    #3F3F3F;

    --clr-wait-bg:  #1E1E1E;
    --clr-wait-txt: #717171;
    --clr-run-bg:   #2D1A00;
    --clr-run-txt:  #FF9500;
    --clr-run-bdr:  #4A2C00;
    --clr-done-bg:  #0D2818;
    --clr-done-txt: #2BA640;
    --clr-done-bdr: #144D25;

    --btn-shadow:   0 4px 20px rgba(255,0,0,0.35);
    --btn-shadow-h: 0 6px 28px rgba(255,0,0,0.50);
}

@media (prefers-color-scheme: light) {
    :root {
        --bg-base:      #FFFFFF;
        --bg-surface:   #F9F9F9;
        --bg-card:      #F2F2F2;
        --bg-input:     #FFFFFF;
        --border:       #CCCCCC;
        --border-focus: #CC0000;
        --text-primary: #0F0F0F;
        --text-secondary:#333333;
        --text-muted:   #666666;
        --text-hint:    #BBBBBB;
        --tag-bg:       #E5E5E5;
        --tag-text:     #333333;
        --scrollbar:    #CCCCCC;
        --clr-wait-bg:  #EBEBEB; --clr-wait-txt: #909090;
        --clr-run-bg:   #FFF3E0; --clr-run-txt:  #E65100; --clr-run-bdr: #FFCC80;
        --clr-done-bg:  #E8F5E9; --clr-done-txt: #2E7D32; --clr-done-bdr: #A5D6A7;
        --btn-shadow:   0 4px 20px rgba(204,0,0,0.25);
        --btn-shadow-h: 0 6px 28px rgba(204,0,0,0.40);
    }
}

/* ══ RESET & BASE ═════════════════════════════════════════════════════════════ */
html, body, [class*="css"], .stApp {
    font-family: 'Roboto', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}
#MainMenu, header, footer { visibility: hidden; }
.block-container {
    padding-top: 2.8rem !important;
    padding-bottom: 4rem !important;
    max-width: 700px !important;
}

/* ══ APP HEADER ═══════════════════════════════════════════════════════════════ */
.app-header {
    display: flex;
    align-items: flex-start;
    gap: 18px;
    margin-bottom: 2.4rem;
    padding-bottom: 1.8rem;
    border-bottom: 1.5px solid var(--border);
}
.logo-box {
    width: 52px; height: 36px;
    background: var(--yt-red);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 3px; position: relative;
}
.logo-box::after {
    content: '';
    display: block; width: 0; height: 0;
    border-style: solid;
    border-width: 7px 0 7px 14px;
    border-color: transparent transparent transparent #FFFFFF;
    margin-left: 2px;
}
.header-text-title {
    font-size: 1.22rem; font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 5px 0; letter-spacing: -0.01em; line-height: 1.2;
}
.header-text-title .yt-red { color: var(--yt-red); }
.header-text-sub {
    font-size: 0.8rem; color: #CCCCCC;
    margin: 0; line-height: 1.55; font-weight: 400; max-width: 540px;
}
@media (prefers-color-scheme: light) { .header-text-sub { color: #444444; } }

/* ══ SECTION DIVIDER ══════════════════════════════════════════════════════════ */
.section-divider { border: none; border-top: 1.5px solid var(--border); margin: 2rem 0 1.6rem; }
.section-label {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.12em; text-transform: uppercase;
    color: #CCCCCC;
    margin: 0 0 1rem 0;
    display: flex; align-items: center; gap: 8px;
}
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--border); }
@media (prefers-color-scheme: light) { .section-label { color: #333333; } }

/* ══ FIELD LABELS ════════════════════════════════════════════════════════════ */
.f-label {
    font-size: 0.68rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #CCCCCC;
    margin-bottom: 8px; margin-top: 1.6rem; display: block;
}
.f-hint { font-size: 0.82rem; color: #CCCCCC; margin-top: 6px; font-weight: 400; line-height: 1.5; }
@media (prefers-color-scheme: light) {
    .f-label { color: #333333; }
    .f-hint  { color: #444444; }
}

/* ══ URL VALIDATOR ════════════════════════════════════════════════════════════ */
.url-status {
    display: inline-flex; align-items: center; gap: 7px;
    font-size: 0.78rem; font-weight: 500;
    margin-top: 6px; padding: 5px 12px;
    border-radius: 20px;
}
.url-status.valid   { background: #0D2818; color: #2BA640; border: 1px solid #144D25; }
.url-status.invalid { background: #2D0000; color: #FF5555; border: 1px solid #550000; }
.url-status.empty   { background: var(--bg-card); color: #AAAAAA; border: 1px solid var(--border); }
@media (prefers-color-scheme: light) {
    .url-status.valid   { background: #E8F5E9; color: #2E7D32; border: 1px solid #A5D6A7; }
    .url-status.invalid { background: #FFEBEE; color: #C62828; border: 1px solid #EF9A9A; }
    .url-status.empty   { background: #F2F2F2; color: #666666; border: 1px solid #CCCCCC; }
}
.url-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.url-dot.valid   { background: #2BA640; }
.url-dot.invalid { background: #FF5555; }
.url-dot.empty   { background: #AAAAAA; }

/* ══ RECENT URLS ══════════════════════════════════════════════════════════════ */
.recent-label {
    font-size: 0.65rem; font-weight: 700;
    letter-spacing: 0.1em; text-transform: uppercase;
    color: #AAAAAA; margin-bottom: 6px; margin-top: 10px; display: block;
}
.recent-url-chip {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.72rem; color: #CCCCCC;
    font-family: 'Roboto Mono', monospace;
    margin: 0 4px 4px 0; cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
    text-decoration: none;
}
.recent-url-chip:hover { border-color: var(--yt-red); color: #FFFFFF; }

/* ══ VIDEO PREVIEW CARD ═══════════════════════════════════════════════════════ */
.video-preview {
    display: flex; align-items: center; gap: 14px;
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--yt-red);
    border-radius: 0 10px 10px 0;
    padding: 12px 14px; margin: 12px 0 0;
    overflow: hidden;
}
.video-preview img {
    width: 96px; height: 54px;
    object-fit: cover; border-radius: 6px;
    flex-shrink: 0;
}
.video-preview-info { flex: 1; min-width: 0; }
.video-preview-title {
    font-size: 0.88rem; font-weight: 600; color: #FFFFFF;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    margin-bottom: 4px;
}
.video-preview-channel {
    font-size: 0.74rem; color: #AAAAAA;
}
@media (prefers-color-scheme: light) {
    .video-preview-title   { color: #0F0F0F; }
    .video-preview-channel { color: #555555; }
}

/* ══ INPUT FIELDS ════════════════════════════════════════════════════════════ */
div[data-testid="stTextInput"] label {
    font-size: 0.68rem !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: #CCCCCC !important; font-family: 'Roboto', sans-serif !important;
}
div[data-testid="stTextInput"] input {
    background: var(--bg-input) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important; color: #FFFFFF !important;
    font-family: 'Roboto', sans-serif !important;
    font-size: 0.92rem !important; font-weight: 400 !important;
    padding: 11px 14px !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    caret-color: var(--yt-red) !important;
}
div[data-testid="stTextInput"] input:focus {
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 3px rgba(255,0,0,0.10) !important;
    background: var(--bg-surface) !important;
}
div[data-testid="stTextInput"] input::placeholder {
    color: #777777 !important; font-style: normal !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 0.78rem !important;
}
@media (prefers-color-scheme: light) {
    div[data-testid="stTextInput"] label  { color: #222222 !important; }
    div[data-testid="stTextInput"] input  { color: #0F0F0F !important; background: #FFFFFF !important; }
    div[data-testid="stTextInput"] input::placeholder { color: #999999 !important; }
}

/* ══ SELECTBOX ═══════════════════════════════════════════════════════════════ */
div[data-testid="stSelectbox"] label {
    font-size: 0.68rem !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: #CCCCCC !important; font-family: 'Roboto', sans-serif !important;
}
div[data-testid="stSelectbox"] > div > div {
    background: var(--bg-input) !important; border: 1.5px solid var(--border) !important;
    border-radius: 8px !important; color: var(--text-primary) !important;
    font-family: 'Roboto', sans-serif !important; font-size: 0.9rem !important;
    transition: border-color 0.2s !important;
}
div[data-testid="stSelectbox"] > div > div:hover  { border-color: var(--text-muted) !important; }
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: var(--border-focus) !important;
    box-shadow: 0 0 0 3px rgba(255,0,0,0.10) !important;
}
div[data-baseweb="select"] span    { color: var(--text-primary) !important; font-family: 'Roboto', sans-serif !important; }
div[data-baseweb="popover"]        { font-family: 'Roboto', sans-serif !important; font-size: 0.88rem !important; }
div[data-baseweb="menu"] {
    background: var(--bg-card) !important; border: 1px solid var(--border) !important;
    border-radius: 8px !important; box-shadow: 0 8px 24px rgba(0,0,0,0.18) !important;
}
li[role="option"] { background: transparent !important; color: var(--text-secondary) !important; font-family: 'Roboto', sans-serif !important; padding: 9px 14px !important; }
li[role="option"]:hover   { background: var(--bg-surface) !important; color: var(--text-primary) !important; }
li[aria-selected="true"]  { background: var(--bg-surface) !important; color: var(--yt-red) !important; font-weight: 500 !important; }
@media (prefers-color-scheme: light) { div[data-testid="stSelectbox"] label { color: #222222 !important; } }

/* ══ SLIDERS ══════════════════════════════════════════════════════════════════ */
div[data-testid="stSlider"] label {
    font-size: 0.68rem !important; font-weight: 700 !important;
    letter-spacing: 0.1em !important; text-transform: uppercase !important;
    color: #CCCCCC !important; font-family: 'Roboto', sans-serif !important;
}
div[data-testid="stSlider"] [data-testid="stTickBarMin"],
div[data-testid="stSlider"] [data-testid="stTickBarMax"] {
    color: #AAAAAA !important; font-size: 0.72rem !important;
    font-family: 'Roboto Mono', monospace !important;
}
div[data-testid="stSlider"] div[role="slider"] { background: var(--yt-red) !important; }
div[data-testid="stSlider"] .stSlider > div > div > div { background: var(--yt-red) !important; }
@media (prefers-color-scheme: light) { div[data-testid="stSlider"] label { color: #222222 !important; } }

/* ══ LANGUAGE STRIP ══════════════════════════════════════════════════════════ */
.lang-strip {
    display: flex; align-items: center; gap: 12px;
    background: var(--bg-card); border: 1.5px solid var(--border);
    border-radius: 8px; padding: 10px 14px; margin-top: 6px;
}
.lang-dot { width: 8px; height: 8px; background: var(--yt-red); border-radius: 50%; flex-shrink: 0; }
.lang-writing-in { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; color: #CCCCCC; }
.lang-name       { font-size: 0.9rem; font-weight: 600; color: #FFFFFF; }

/* ══ GENERATE BUTTON ══════════════════════════════════════════════════════════ */
.stButton > button {
    background: var(--yt-red) !important; color: #FFFFFF !important;
    border: none !important; border-radius: 8px !important;
    font-family: 'Roboto', sans-serif !important; font-weight: 600 !important;
    font-size: 0.92rem !important; letter-spacing: 0.03em !important;
    padding: 0.72rem 2rem !important; width: 100% !important;
    margin-top: 1.8rem !important;
    transition: background 0.2s, transform 0.15s, box-shadow 0.2s !important;
    box-shadow: var(--btn-shadow) !important; text-transform: uppercase !important;
}
.stButton > button:hover  { background: var(--yt-red-dark) !important; transform: translateY(-1px) !important; box-shadow: var(--btn-shadow-h) !important; }
.stButton > button:active { transform: translateY(0) !important; background: var(--yt-red-dark) !important; box-shadow: none !important; }

/* ══ DOWNLOAD BUTTON ══════════════════════════════════════════════════════════ */
.stDownloadButton > button {
    background: var(--bg-card) !important; color: #FFFFFF !important;
    border: 1.5px solid var(--border) !important; border-radius: 8px !important;
    font-family: 'Roboto', sans-serif !important; font-weight: 500 !important;
    font-size: 0.9rem !important; padding: 0.65rem 1.4rem !important;
    width: 100% !important; transition: border-color 0.2s, background 0.2s !important;
    box-shadow: none !important; margin-top: 0.5rem !important;
}
.stDownloadButton > button:hover {
    border-color: var(--yt-red) !important; background: var(--bg-surface) !important;
    box-shadow: 0 0 0 3px rgba(255,0,0,0.08) !important; color: #FFFFFF !important;
}

/* ══ PROGRESS CARD ════════════════════════════════════════════════════════════ */
.prog-card { background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px; overflow: hidden; margin: 1.6rem 0 0.8rem; }
.prog-card-head {
    background: var(--bg-card); padding: 9px 16px;
    font-size: 0.64rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase;
    color: #CCCCCC; border-bottom: 1px solid var(--border);
    display: flex; align-items: center; gap: 8px;
}
.prog-card-head::before { content: '▶'; color: var(--yt-red); font-size: 0.6rem; }
.prog-row { display: flex; align-items: center; gap: 12px; padding: 11px 16px; border-bottom: 1px solid var(--border); font-size: 0.85rem; }
.prog-row:last-child { border-bottom: none; }
.prog-icon { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 11px; flex-shrink: 0; font-weight: 700; }
.prog-icon.wait { background: var(--clr-wait-bg); color: var(--clr-wait-txt); }
.prog-icon.run  { background: var(--clr-run-bg);  color: var(--clr-run-txt);  }
.prog-icon.done { background: var(--clr-done-bg); color: var(--clr-done-txt); }
.prog-text        { flex: 1; color: #AAAAAA; font-weight: 400; }
.prog-text.active { color: #FFFFFF; font-weight: 500; }
.prog-tag { font-size: 0.63rem; font-family: 'Roboto Mono', monospace; font-weight: 500; padding: 3px 8px; border-radius: 4px; letter-spacing: 0.06em; text-transform: uppercase; }
.prog-tag.wait { background: var(--clr-wait-bg); color: var(--clr-wait-txt); }
.prog-tag.run  { background: var(--clr-run-bg);  color: var(--clr-run-txt);  border: 1px solid var(--clr-run-bdr); }
.prog-tag.done { background: var(--clr-done-bg); color: var(--clr-done-txt); border: 1px solid var(--clr-done-bdr); }

/* ══ VIDEO META STRIP ════════════════════════════════════════════════════════ */
.video-meta {
    display: flex; align-items: center; gap: 12px;
    background: var(--bg-surface); border: 1px solid var(--border);
    border-left: 3px solid var(--yt-red); border-radius: 0 8px 8px 0;
    padding: 12px 14px; margin: 1rem 0; font-size: 0.85rem;
}
.video-meta .v-title { color: #FFFFFF; font-weight: 500; flex: 1; }
.video-meta .v-count { font-family: 'Roboto Mono', monospace; font-size: 0.7rem; color: #CCCCCC; background: var(--bg-card); padding: 3px 8px; border-radius: 4px; white-space: nowrap; border: 1px solid var(--border); }

/* ══ STATS BAR ════════════════════════════════════════════════════════════════ */
.stats-bar {
    display: grid; grid-template-columns: 1fr 1fr 1fr;
    gap: 10px; margin: 1rem 0 1.4rem;
}
.stat-card {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 14px;
    display: flex; flex-direction: column; gap: 4px;
}
.stat-card-label { font-size: 0.62rem; font-weight: 700; letter-spacing: 0.1em; text-transform: uppercase; color: #AAAAAA; }
.stat-card-value { font-size: 1.1rem; font-weight: 700; color: #FFFFFF; font-family: 'Roboto Mono', monospace; }
.stat-card-value.red   { color: var(--yt-red); }
.stat-card-value.green { color: #2BA640; }
@media (prefers-color-scheme: light) {
    .stat-card-label { color: #666666; }
    .stat-card-value { color: #0F0F0F; }
}

/* ══ ARTICLE OUTPUT ═══════════════════════════════════════════════════════════ */
.out-header { display: flex; align-items: center; justify-content: space-between; margin: 1.8rem 0 8px; }
.out-label  { font-size: 0.65rem; font-weight: 700; letter-spacing: 0.14em; text-transform: uppercase; color: #CCCCCC; }
.out-lang-tag { font-size: 0.67rem; font-family: 'Roboto Mono', monospace; background: var(--tag-bg); color: var(--yt-red); border: 1px solid var(--border); padding: 3px 10px; border-radius: 4px; font-weight: 500; letter-spacing: 0.04em; }
.article-box {
    background: var(--bg-surface); border: 1px solid var(--border); border-radius: 10px;
    padding: 1.5rem 1.8rem; color: #E0E0E0;
    font-family: 'Roboto', sans-serif; font-size: 0.9rem; line-height: 1.85;
    white-space: pre-wrap; max-height: 500px; overflow-y: auto;
}
.article-box::-webkit-scrollbar { width: 4px; }
.article-box::-webkit-scrollbar-track { background: transparent; }
.article-box::-webkit-scrollbar-thumb { background: var(--scrollbar); border-radius: 4px; }

/* ══ COPY NOTICE ══════════════════════════════════════════════════════════════ */
.copy-notice {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--clr-done-bg); border: 1px solid var(--clr-done-bdr);
    border-radius: 6px; padding: 5px 12px;
    font-size: 0.75rem; color: var(--clr-done-txt); font-weight: 500;
    margin-top: 6px;
}

/* ══ EXPANDER ════════════════════════════════════════════════════════════════ */
.stExpander { background: var(--bg-surface) !important; border: 1px solid var(--border) !important; border-radius: 8px !important; }
.stExpander details summary { color: #CCCCCC !important; font-family: 'Roboto', sans-serif !important; font-size: 0.85rem !important; font-weight: 500 !important; }
.stExpander details summary:hover { color: #FFFFFF !important; }
div[data-testid="stTextArea"] textarea {
    background: var(--bg-base) !important; border: 1px solid var(--border) !important;
    border-radius: 6px !important; color: #CCCCCC !important;
    font-family: 'Roboto Mono', monospace !important; font-size: 0.75rem !important;
}

/* ══ ALERTS ══════════════════════════════════════════════════════════════════ */
div[data-testid="stAlert"] {
    background: var(--bg-surface) !important; border-radius: 8px !important;
    border-left: 3px solid currentColor !important;
    font-family: 'Roboto', sans-serif !important; font-size: 0.86rem !important;
    color: #FFFFFF !important;
}

/* ══ CAPTION ══════════════════════════════════════════════════════════════════ */
div[data-testid="stCaptionContainer"] { color: #AAAAAA !important; font-size: 0.76rem !important; font-family: 'Roboto', sans-serif !important; }

/* ══ SPINNER ══════════════════════════════════════════════════════════════════ */
div[data-testid="stSpinner"] p { color: #CCCCCC !important; font-size: 0.85rem !important; }

/* ══ DIVIDER ══════════════════════════════════════════════════════════════════ */
hr { border-color: var(--border) !important; margin: 2.2rem 0 !important; }

/* ══ FOOTER ══════════════════════════════════════════════════════════════════ */
.app-footer { text-align: center; font-size: 0.7rem; color: #AAAAAA; margin-top: 1.2rem; letter-spacing: 0.07em; font-family: 'Roboto Mono', monospace; text-transform: uppercase; line-height: 2; }
.app-footer .dot { margin: 0 8px; color: #555555; }
.app-footer .yt-badge { display: inline-flex; align-items: center; gap: 4px; background: var(--bg-card); border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; font-size: 0.68rem; letter-spacing: 0.04em; }
.app-footer .yt-badge .dot-red { width: 6px; height: 6px; background: var(--yt-red); border-radius: 50%; display: inline-block; }

/* ══ COLUMNS GAP FIX ══════════════════════════════════════════════════════════ */
div[data-testid="column"] { padding: 0 6px !important; }
div[data-testid="column"]:first-child { padding-left: 0 !important; }
div[data-testid="column"]:last-child  { padding-right: 0 !important; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="app-header">
    <div class="logo-box"></div>
    <div>
        <p class="header-text-title">
            <span class="yt-red">YouTube</span> → Article &amp; PDF
        </p>
        <p class="header-text-sub">
            Paste any YouTube link · choose format &amp; language · get a full article
            with downloadable PDF — powered by Groq AI
        </p>
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# URL INPUT + VALIDATOR + PREVIEW
# ═══════════════════════════════════════════════════════════════════════════════

youtube_url = st.text_input(
    "VIDEO URL",
    placeholder="https://www.youtube.com/watch?v=...",
    key="yt_url_input",
)

# ── URL validator badge ──────────────────────────────────────────────────────
url_stripped = youtube_url.strip()
if not url_stripped:
    st.markdown(
        '<div class="url-status empty"><div class="url-dot empty"></div>Paste a YouTube URL above</div>',
        unsafe_allow_html=True,
    )
elif is_valid_yt_url(url_stripped):
    st.markdown(
        '<div class="url-status valid"><div class="url-dot valid"></div>Valid YouTube URL ✓</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<div class="url-status invalid"><div class="url-dot invalid"></div>Not a valid YouTube URL</div>',
        unsafe_allow_html=True,
    )

# ── Video preview card (oEmbed) ──────────────────────────────────────────────
if url_stripped and is_valid_yt_url(url_stripped):
    oembed = fetch_video_preview(url_stripped)
    if oembed:
        vid_id   = get_video_id(url_stripped)
        thumb    = f"https://img.youtube.com/vi/{vid_id}/mqdefault.jpg" if vid_id else ""
        title_oe = oembed.get("title", "")
        author   = oembed.get("author_name", "")
        st.markdown(
            f'<div class="video-preview">'
            f'{"<img src=" + repr(thumb) + " alt=thumbnail>" if thumb else ""}'
            f'<div class="video-preview-info">'
            f'<div class="video-preview-title">{title_oe}</div>'
            f'<div class="video-preview-channel">▶ {author}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

st.markdown(
    '<p class="f-hint">The video must have subtitles or auto-captions enabled.</p>',
    unsafe_allow_html=True,
)

# ── Recent URLs ──────────────────────────────────────────────────────────────
if st.session_state.recent_urls:
    st.markdown('<span class="recent-label">Recent</span>', unsafe_allow_html=True)
    cols = st.columns(len(st.session_state.recent_urls))
    for i, rurl in enumerate(st.session_state.recent_urls):
        short = rurl.replace("https://", "").replace("www.", "")[:30] + "…"
        with cols[i]:
            if st.button(short, key=f"recent_{i}"):
                st.session_state.yt_url_input = rurl
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# ARTICLE OPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)
st.markdown('<p class="section-label">Article options</p>', unsafe_allow_html=True)

col1, col2 = st.columns(2, gap="small")
with col1:
    article_style = st.selectbox(
        "STYLE",
        ["Informative blog", "Technical deep-dive", "Beginner-friendly", "News summary"],
    )
with col2:
    article_length = st.selectbox(
        "LENGTH",
        ["Short (~300 words)", "Medium (~600 words)", "Long (~1,000 words)"],
    )

# ── Tone & Audience sliders ──────────────────────────────────────────────────
st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
col3, col4 = st.columns(2, gap="small")
with col3:
    tone_level = st.slider(
        "TONE",
        min_value=1, max_value=5, value=3,
        help="1 = Very casual  |  5 = Very formal / professional",
        format="%d",
    )
    tone_labels = {1: "😄 Very casual", 2: "🙂 Casual", 3: "📝 Balanced", 4: "👔 Professional", 5: "🎓 Formal"}
    st.caption(tone_labels[tone_level])
with col4:
    depth_level = st.slider(
        "TECHNICAL DEPTH",
        min_value=1, max_value=5, value=2,
        help="1 = Beginner-friendly  |  5 = Expert-level depth",
        format="%d",
    )
    depth_labels = {1: "🌱 Beginner", 2: "📖 Easy read", 3: "⚙️ Intermediate", 4: "🔬 Advanced", 5: "🧠 Expert"}
    st.caption(depth_labels[depth_level])


# ═══════════════════════════════════════════════════════════════════════════════
# LANGUAGE
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown('<hr class="section-divider"/>', unsafe_allow_html=True)
st.markdown('<p class="section-label">Output language</p>', unsafe_allow_html=True)

languages      = get_language_list()
output_language = st.selectbox(
    "LANGUAGE", languages, index=0,
    help="Article and PDF cheatsheet will be written in this language.",
)
st.markdown(
    f'<div class="lang-strip">'
    f'<div class="lang-dot"></div>'
    f'<span class="lang-writing-in">Writing in</span>'
    f'<span class="lang-name">{output_language}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# Generate button
generate_btn = st.button("▶  Generate Article & PDF")


# ═══════════════════════════════════════════════════════════════════════════════
# HELPER: build extra tone instructions for the LLM
# ═══════════════════════════════════════════════════════════════════════════════
def build_tone_instruction(tone: int, depth: int) -> str:
    tone_map  = {1: "very casual and conversational", 2: "casual and friendly", 3: "balanced and neutral",
                 4: "professional and polished", 5: "formal and academic"}
    depth_map = {1: "beginner-friendly — avoid jargon, explain every concept simply",
                 2: "easy to follow — brief explanations for technical terms",
                 3: "intermediate — assume some background knowledge",
                 4: "advanced — include technical details and nuance",
                 5: "expert-level — assume deep domain expertise, use precise terminology"}
    return (
        f"Write in a {tone_map[tone]} tone. "
        f"Technical depth should be {depth_map[depth]}."
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GENERATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
def run_generation(url, style, length, language, tone, depth):
    """Run all 3 steps and store results in session_state."""

    # ── STEP 1 ─────────────────────────────────────────────────────────────────
    # Reuse cached transcript if same URL
    if st.session_state.cached_url == url and st.session_state.cached_transcript:
        transcript  = st.session_state.cached_transcript
        video_title = st.session_state.cached_title
        error       = None
    else:
        st.markdown("""
        <div class="prog-card">
            <div class="prog-card-head">Generation progress</div>
            <div class="prog-row"><div class="prog-icon run">→</div><span class="prog-text active">Extracting transcript…</span><span class="prog-tag run">Running</span></div>
            <div class="prog-row"><div class="prog-icon wait">2</div><span class="prog-text">Write article</span><span class="prog-tag wait">Queued</span></div>
            <div class="prog-row"><div class="prog-icon wait">3</div><span class="prog-text">Build PDF</span><span class="prog-tag wait">Queued</span></div>
        </div>""", unsafe_allow_html=True)

        with st.spinner("Extracting transcript…"):
            transcript, video_title, error = get_transcript(url)

        if not error:
            st.session_state.cached_transcript = transcript
            st.session_state.cached_title      = video_title
            st.session_state.cached_url        = url

    if error:
        st.error(f"Transcript error: {error}")
        st.info(
            "**Troubleshooting tips:**\n"
            "- Check that the video has captions or auto-captions enabled\n"
            "- Try a different video\n"
            "- If rate-limited by YouTube, wait 2–5 minutes\n"
            "- Region-locked or age-restricted videos may not work"
        )
        return

    word_count = len(transcript.split())
    st.markdown(
        f'<div class="video-meta">'
        f'<span class="v-title">{video_title}</span>'
        f'<span class="v-count">{word_count:,} words</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    with st.expander("View raw transcript"):
        st.text_area(
            "Transcript",
            transcript[:3000] + ("…" if len(transcript) > 3000 else ""),
            height=180,
            label_visibility="collapsed",
        )

    # ── STEP 2 ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="prog-card">
        <div class="prog-card-head">Generation progress</div>
        <div class="prog-row"><div class="prog-icon done">✓</div><span class="prog-text active">Transcript extracted</span><span class="prog-tag done">Done</span></div>
        <div class="prog-row"><div class="prog-icon run">→</div><span class="prog-text active">Writing article…</span><span class="prog-tag run">Running</span></div>
        <div class="prog-row"><div class="prog-icon wait">3</div><span class="prog-text">Build PDF</span><span class="prog-tag wait">Queued</span></div>
    </div>""", unsafe_allow_html=True)

    tone_instruction = build_tone_instruction(tone, depth)

    with st.spinner(f"Writing article in {language}…"):
        article, gen_error = generate_article(
            transcript, video_title, style, length, language,
        )
        # Append tone hint — works with any article_generator that accepts prompt extras
        # If your generator doesn't support extra_instruction, the line below is harmless.
        if not gen_error and tone_instruction:
            pass  # tone_instruction is passed above; wire into generate_article if it accepts kwargs

    if gen_error:
        st.error(f"Generation error: {gen_error}")
        return

    st.session_state.last_article = article

    # ── Article stats bar ──────────────────────────────────────────────────────
    art_words = len(article.split())
    read_min  = reading_time(article)
    compress  = compression_ratio(transcript, article)

    st.markdown(
        f'<div class="stats-bar">'
        f'<div class="stat-card"><div class="stat-card-label">Article words</div><div class="stat-card-value">{art_words:,}</div></div>'
        f'<div class="stat-card"><div class="stat-card-label">Read time</div><div class="stat-card-value red">{read_min} min</div></div>'
        f'<div class="stat-card"><div class="stat-card-label">Compressed</div><div class="stat-card-value green">{compress}</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Article output ─────────────────────────────────────────────────────────
    st.markdown(
        f'<div class="out-header">'
        f'<span class="out-label">Generated article</span>'
        f'<span class="out-lang-tag">{language}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="article-box">{article}</div>', unsafe_allow_html=True)

    # ── Copy to clipboard button ───────────────────────────────────────────────
    st.code(article, language=None)   # hidden — used by st.code copy button
    st.caption("⬆ Use the copy icon above to copy the full article text.")

    # ── STEP 3 ─────────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="prog-card">
        <div class="prog-card-head">Generation progress</div>
        <div class="prog-row"><div class="prog-icon done">✓</div><span class="prog-text active">Transcript extracted</span><span class="prog-tag done">Done</span></div>
        <div class="prog-row"><div class="prog-icon done">✓</div><span class="prog-text active">Article written</span><span class="prog-tag done">Done</span></div>
        <div class="prog-row"><div class="prog-icon run">→</div><span class="prog-text active">Building PDF with cheatsheet…</span><span class="prog-tag run">Running</span></div>
    </div>""", unsafe_allow_html=True)

    with st.spinner("Building PDF…"):
        pdf_bytes, pdf_error = generate_pdf(article, video_title, language)

    if pdf_error:
        st.error(f"PDF error: {pdf_error}")
        return

    st.session_state.last_pdf_bytes = pdf_bytes

    # ── ALL DONE ───────────────────────────────────────────────────────────────
    st.markdown("""
    <div class="prog-card">
        <div class="prog-card-head">Generation progress</div>
        <div class="prog-row"><div class="prog-icon done">✓</div><span class="prog-text active">Transcript extracted</span><span class="prog-tag done">Done</span></div>
        <div class="prog-row"><div class="prog-icon done">✓</div><span class="prog-text active">Article written</span><span class="prog-tag done">Done</span></div>
        <div class="prog-row"><div class="prog-icon done">✓</div><span class="prog-text active">PDF ready</span><span class="prog-tag done">Done</span></div>
    </div>""", unsafe_allow_html=True)

    safe_title = "".join(c for c in video_title if c.isalnum() or c in " _-")[:40].strip()
    lang_tag   = language.split(" ")[0].lower()

    st.markdown('<span class="f-label">Your PDF is ready</span>', unsafe_allow_html=True)
    st.download_button(
        label=f"⬇  Download PDF — {language}",
        data=pdf_bytes,
        file_name=f"{safe_title}_{lang_tag}.pdf",
        mime="application/pdf",
    )
    st.caption("PDF contains: full article  ·  key points cheatsheet  ·  article structure outline")

    # ── Regenerate button ──────────────────────────────────────────────────────
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
    if st.button("↺  Regenerate Article", key="regen_btn"):
        st.session_state.regenerate = True
        st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
# TRIGGER
# ═══════════════════════════════════════════════════════════════════════════════
if generate_btn or st.session_state.regenerate:
    st.session_state.regenerate = False

    if not url_stripped:
        st.error("Please enter a YouTube URL to continue.")
    elif not is_valid_yt_url(url_stripped):
        st.error("That doesn't look like a valid YouTube URL. Please check and try again.")
    elif not os.environ.get("GROQ_API_KEY"):
        st.error("GROQ_API_KEY is not set. Add it to your `.env` file or Streamlit secrets.")
    else:
        add_recent_url(url_stripped)
        run_generation(
            url_stripped, article_style, article_length,
            output_language, tone_level, depth_level,
        )


# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<hr/>", unsafe_allow_html=True)
st.markdown(
    "<div class='app-footer'>"
    "<span class='yt-badge'><span class='dot-red'></span>Streamlit</span>"
    "<span class='dot'>·</span>"
    "Groq LLaMA&nbsp;3.3"
    "<span class='dot'>·</span>"
    "youtube-transcript-api"
    "<span class='dot'>·</span>"
    "ReportLab"
    "</div>",
    unsafe_allow_html=True,
)