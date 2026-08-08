import streamlit as st
import gspread
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & LIGHT MODE UI
# ---------------------------------------------------------
st.set_page_config(
    page_title="PATIENT DATA RECORDING SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme components explicitly
st.markdown("""
<style>
    /* Ensure the app body is white */
    .stApp {
        background-color: #ffffff !important;
        color: #1e293b !important;
    }
    /* Dropdown and Input Fields - White Background */
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"], textarea {
        background-color: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
    }
    /* Tables */
    div[data-testid="stDataFrame"] {
        background-color: #ffffff !important;
    }
    /* Dropdown popover menu background */
    div[data-baseweb="popover"] {
        background-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

# ... [Keep the rest of your existing code below this block] ...