import streamlit as st

# Keep Streamlit HEADER visible (sidebar toggle lives there).
CSS = """
<style>
  .stApp {
    background:
      radial-gradient(1000px 520px at 8% -8%, rgba(99,102,241,0.20), transparent 52%),
      radial-gradient(800px 480px at 96% 4%, rgba(45,212,191,0.10), transparent 48%),
      linear-gradient(185deg, #06080d 0%, #0c1018 42%, #080b10 100%) !important;
  }

  .block-container {
    padding-top: 0.85rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1180px !important;
  }

  footer { visibility: hidden !important; height: 0 !important; }
  #MainMenu { visibility: hidden !important; }
  div[data-testid="stToolbar"] { display: none !important; }

  .stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1 0%, #4f46e5 55%, #4338ca 100%) !important;
    border: none !important;
    color: #f8fafc !important;
    font-weight: 600 !important;
    border-radius: 999px !important;
    padding: 0.42rem 0.95rem !important;
    box-shadow: 0 10px 28px rgba(67, 56, 202, 0.38);
  }
  .stButton > button[kind="secondary"] {
    background: rgba(15, 23, 42, 0.55) !important;
    border: 1px solid rgba(148, 163, 184, 0.22) !important;
    color: #e2e8f0 !important;
    border-radius: 999px !important;
    font-weight: 500 !important;
  }
  .stButton > button[kind="secondary"]:hover {
    border-color: rgba(165, 180, 252, 0.45) !important;
    background: rgba(30, 41, 59, 0.75) !important;
  }

  span.lab-brand {
    font-weight: 780;
    letter-spacing: -0.04em;
    font-size: 1.28rem;
    background: linear-gradient(92deg, #f1f5f9 0%, #a5b4fc 42%, #5eead4 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
    display: inline-block;
    line-height: 1.2;
    padding-bottom: 0.1rem;
  }
  p.lab-tagline {
    margin: 0.15rem 0 0 0;
    font-size: 0.82rem;
    color: #64748b;
    letter-spacing: 0.01em;
  }

  div.lab-hero {
    border-radius: 20px;
    padding: 1.75rem 1.85rem 1.5rem;
    margin: 0.5rem 0 1.35rem 0;
    background: linear-gradient(150deg, rgba(30,41,59,0.82) 0%, rgba(15,23,42,0.55) 100%);
    border: 1px solid rgba(148, 163, 184, 0.16);
    box-shadow: 0 20px 70px rgba(0,0,0,0.38);
  }
  div.lab-hero h1 {
    margin: 0 0 0.45rem 0;
    font-size: clamp(1.65rem, 2.8vw, 2.2rem);
    font-weight: 780;
    letter-spacing: -0.038em;
    color: #f8fafc;
    line-height: 1.18;
  }
  div.lab-hero .lead {
    margin: 0 0 0.85rem 0;
    font-size: 1.02rem;
    line-height: 1.62;
    color: #94a3b8;
    max-width: 52rem;
  }
  div.lab-pill-row { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.2rem; }
  span.lab-pill {
    font-size: 0.72rem;
    font-weight: 650;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #a5b4fc;
    border: 1px solid rgba(165, 180, 252, 0.32);
    border-radius: 999px;
    padding: 0.22rem 0.58rem;
    background: rgba(79, 70, 229, 0.12);
  }

  div[data-testid="stExpander"] details {
    border-radius: 14px !important;
    border: 1px solid rgba(148, 163, 184, 0.14) !important;
    background: rgba(15, 23, 42, 0.42) !important;
  }

  hr { border: none; border-top: 1px solid rgba(148, 163, 184, 0.11); margin: 1.35rem 0; }

  [data-testid="stMetricValue"] { color: #e2e8f0 !important; }

  /* Slightly calmer widget chrome */
  div[data-baseweb="select"] > div {
    border-radius: 10px !important;
  }
</style>
"""


def inject_theme() -> None:
    st.markdown(CSS, unsafe_allow_html=True)
