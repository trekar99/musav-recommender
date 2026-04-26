import streamlit as st

# Minimal dark UI; extra top padding avoids Streamlit header clipping the custom nav row.
CSS = """
<style>
  .stApp {
    background: #090909 !important;
  }

  .stAppViewContainer > .main {
    padding-top: 0.25rem !important;
  }

  section.main > div.block-container {
    padding-top: 5.25rem !important;
    padding-bottom: 3rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: 920px !important;
  }

  [data-testid="stHeader"] {
    background: rgba(9, 9, 9, 0.92) !important;
    border-bottom: 1px solid #1a1a1a !important;
  }

  footer { visibility: hidden !important; height: 0 !important; }
  #MainMenu { visibility: hidden !important; }
  div[data-testid="stToolbar"] { display: none !important; }

  .stButton > button[kind="primary"] {
    background: #e5e5e5 !important;
    color: #0a0a0a !important;
    border: none !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    padding: 0.4rem 0.9rem !important;
    box-shadow: none !important;
  }
  .stButton > button[kind="primary"]:hover {
    background: #fafafa !important;
  }

  .stButton > button[kind="secondary"] {
    background: transparent !important;
    border: 1px solid #2a2a2a !important;
    color: #a3a3a3 !important;
    border-radius: 6px !important;
    font-weight: 450 !important;
    box-shadow: none !important;
  }
  .stButton > button[kind="secondary"]:hover {
    border-color: #404040 !important;
    color: #d4d4d4 !important;
    background: #141414 !important;
  }

  div.cp-brand {
    font-weight: 600;
    letter-spacing: -0.03em;
    font-size: 1.08rem;
    color: #fafafa;
    line-height: 1.25;
  }
  div.cp-tagline {
    margin: 0.2rem 0 0 0;
    font-size: 0.72rem;
    color: #737373;
    font-weight: 400;
    letter-spacing: 0.02em;
  }

  div.cp-hero {
    border-radius: 8px;
    padding: 1.25rem 1.35rem;
    margin: 0 0 1.5rem 0;
    background: #0f0f0f;
    border: 1px solid #1f1f1f;
  }
  div.cp-hero h1 {
    margin: 0 0 0.5rem 0;
    font-size: clamp(1.15rem, 2.2vw, 1.35rem);
    font-weight: 600;
    letter-spacing: -0.02em;
    color: #fafafa;
    line-height: 1.3;
  }
  div.cp-hero .lead {
    margin: 0;
    font-size: 0.9rem;
    line-height: 1.55;
    color: #a3a3a3;
    max-width: 40rem;
  }

  div.cp-muted {
    font-size: 0.75rem;
    color: #525252;
    margin: 0.5rem 0 0 0;
  }

  div[data-testid="stExpander"] details {
    border-radius: 8px !important;
    border: 1px solid #1f1f1f !important;
    background: #0f0f0f !important;
  }

  hr {
    border: none;
    border-top: 1px solid #1a1a1a;
    margin: 1.25rem 0;
  }

  [data-testid="stMetricValue"] { color: #e5e5e5 !important; }
  [data-testid="stMetricLabel"] { color: #737373 !important; }

  div[data-baseweb="select"] > div {
    border-radius: 6px !important;
  }

  /* Playlist row (descriptor / text results) */
  div.cp-track-shell {
    margin-bottom: 0.35rem;
  }
  div.cp-track-row {
    display: flex;
    align-items: center;
    gap: 0.65rem;
    padding: 0.55rem 0.75rem 0.45rem;
    background: linear-gradient(180deg, #121212 0%, #101010 100%);
    border: 1px solid #252525;
    border-radius: 8px;
  }
  div.cp-track-row:hover {
    border-color: #333333;
    background: #151515;
  }
  span.cp-track-idx {
    min-width: 1.35rem;
    text-align: right;
    color: #525252;
    font-size: 0.8rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }
  span.cp-track-play {
    color: #fafafa;
    font-size: 0.65rem;
    opacity: 0.85;
    width: 1rem;
    text-align: center;
  }
  div.cp-track-text {
    flex: 1;
    min-width: 0;
  }
  div.cp-track-title {
    color: #fafafa;
    font-weight: 500;
    font-size: 0.92rem;
    letter-spacing: -0.01em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  div.cp-track-meta {
    color: #737373;
    font-size: 0.74rem;
    margin-top: 0.12rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  div.cp-track-shell audio {
    margin-top: 0.35rem !important;
    height: 36px !important;
    border-radius: 6px !important;
  }

  /* Text encoder loader (indeterminate) */
  div.cp-load-panel {
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    background: #0f0f0f;
    border: 1px solid #252525;
    border-radius: 8px;
  }
  div.cp-load-panel p {
    margin: 0 0 0.65rem 0;
    font-size: 0.82rem;
    color: #a3a3a3;
  }
  div.cp-indeterminate {
    height: 3px;
    background: #1f1f1f;
    border-radius: 2px;
    overflow: hidden;
  }
  div.cp-indeterminate > div {
    height: 100%;
    width: 35%;
    background: #e5e5e5;
    border-radius: 2px;
    animation: cp-sweep 1.1s ease-in-out infinite;
  }
  @keyframes cp-sweep {
    0% { transform: translateX(-100%); }
    100% { transform: translateX(320%); }
  }
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
