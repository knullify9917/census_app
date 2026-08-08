import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import os
import hashlib
import io

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & LOGO-MATCHED BLUE/GREEN COLORWAY
# ---------------------------------------------------------
st.set_page_config(
    page_title="PATIENT DATA RECORDING SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Clean Light Theme */
    .stApp { background-color: #fcfcfd !important; color: #1e293b !important; }
    
    /* Sidebar Background & Text Theme Styling */
    section[data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #cbd5e1; }
    section[data-testid="stSidebar"] * { color: #1e3a8a !important; }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] span, section[data-testid="stSidebar"] label { color: #0f766e !important; }
    
    /* Headers using Logo Blue (#1e3a8a) */
    h1, h2, h3, h4, h5, h6 { color: #1e3a8a !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    
    /* Subheaders & Paragraph/Label Typography Accent (Logo Green #0f766e) */
    .stMarkdown p, label, .stRadio label, .stCheckbox label, .stMultiSelect label { color: #0f766e !important; font-weight: 500 !important; }
    
    /* Action Buttons (Logo Blue with green accent hover) */
    .stButton > button, form button[type="submit"] {
        background-color: #1e3a8a !important; color: #ffffff !important; border-radius: 6px !important; border: none !important; font-weight: bold !important;
    }
    .stButton > button:hover, form button[type="submit"]:hover { background-color: #0f766e !important; color: #ffffff !important; }
    
    /* Sidebar Sign Out & Download Buttons Styled to Match stMetric Cards */
    section[data-testid="stSidebar"] div.stButton > button, section[data-testid="stSidebar"] .stDownloadButton > button {
        background-color: #ffffff !important;
        color: #1e3a8a !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 5px solid #0f766e !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        font-weight: 600 !important;
        width: 100% !important;
        text-align: left !important;
        padding: 10px 15px !important;
    }
    section[data-testid="stSidebar"] div.stButton > button:hover, section[data-testid="stSidebar"] .stDownloadButton > button:hover {
        background-color: #f0fdf4 !important;
        color: #0f766e !important;
        border-color: #0f766e !important;
        border-left: 5px solid #1e3a8a !important;
    }

    /* Form Inputs, Textareas, and Dropdown Controls */
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"], input[type="password"], textarea {
        background-color: #ffffff !important; color: #1e3a8a !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important;
    }
    div[data-baseweb="select"] span { color: #1e3a8a !important; }
    
    /* Professional Clean Borders for Time / Date input widget containers */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #0f766e !important;
        box-shadow: 0 0 0 1px #0f766e !important;
    }

    /* Dropdown Popover Lists & Menus */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #ffffff !important; color: #1e3a8a !important; border: 1px solid #cbd5e1 !important;
    }
    li[role="option"], div[data-baseweb="menu"] div, option { background-color: #ffffff !important; color: #1e3a8a !important; }
    li[role="option"]:hover, div[data-baseweb="menu"] div:hover { background-color: #f0fdf4 !important; color: #0f766e !important; }
    
    /* Dataframe Tables */
    [data-testid="stDataFrame"] { background-color: #ffffff !important; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px; }
    [data-testid="stDataFrame"] table { background-color: #ffffff !important; color: #1e293b !important; }
    [data-testid="stDataFrame"] thead tr th { background-color: #e2e8f0 !important; color: #1e3a8a !important; font-weight: bold !important; }
    
    /* Metric Cards with Logo Green Accent Border (#0f766e) */
    div.stMetric {
        background-color: #ffffff !important; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #cbd5e1; border-left: 5px solid #0f766e !important;
    }
    div.stMetric label { color: #0f766e !important; font-weight: 600 !important; }
    div.stMetric div[data-testid="stMetricValue"] { color: #1e3a8a !important; font-weight: bold !important; }
    
    div.stForm { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
</style>
""", unsafe_allow_html=True)

# Helper function to hash passwords securely
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# User Database with Administrator and Department Staff Accounts
USER_DATABASE = {
    "admin": {
        "password": hash_password("admin123"),
        "role": "Administrator",
        "name": "System Administrator",
        "modules": "All"
    },
    "ecc_staff": {
        "password": hash_password("ecc2026"),
        "role": "ECC Staff",
        "name": "Emergency Care Staff",
        "modules": ["Hospital Information System", "Emergency Care Complex (ECC)"]
    },
    "scc_staff": {
        "password": hash_password("scc2026"),
        "role": "SCC Staff",
        "name": "Surgical Care Staff",
        "modules": ["Hospital Information System", "Surgical Care Complex (OR Main)"]
    },
    "endo_staff": {
        "password": hash_password("endo2026"),
        "role": "ENDO Staff",
        "name": "Endoscopy Unit Staff",
        "modules": ["Hospital Information System", "Endoscopy Unit (ENDO)"]
    },
    "hdu_staff": {
        "password": hash_password("hdu2026"),
        "role": "HDU Staff",
        "name": "Hemodialysis Unit Staff",
        "modules": ["Hospital Information System", "Hemodialysis Unit (HDU)"]
    },
    "nsu_staff": {
        "password": hash_password("nsu2026"),
        "role": "Special Care Staff",
        "name": "Special Care Unit Staff",
        "modules": ["Hospital Information System", "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"]
    },
    "obgyne_staff": {
        "password": hash_password("obgyne2026"),
        "role": "OBGYNE Staff",
        "name": "OBGYNE Care Staff",
        "modules": ["Hospital Information System", "OBGYNE Care Complex (LRDR-OB Surgery)"]
    },
    "nsgcon_staff": {
        "password": hash_password("nsgcon2026"),
        "role": "Nursing Administration",
        "name": "Nursing Control Staff",
        "modules": "All"
    }
}

# Session State Initialization for Auth
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "name" not in st.session_state:
    st.session_state["name"] = ""

# ---------------------------------------------------------
# AUTHENTICATION SCREEN IF NOT LOGGED IN
# ---------------------------------------------------------
if not st.session_state["authenticated"]:
    col_l1, col_l2, col_l3 = st.columns([0.2, 2.6, 0.2])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="color: #1e3a8a; margin-bottom: 6px; font-size: 2.2rem; white-space: nowrap; font-weight: 800;">Mother Teresa of Calcutta Medical Center</h1>
                <p style="color: #0f766e; font-weight: 600; font-size: 1.2rem; margin-top: 0px; letter-spacing: 0.5px;">Patient Data System</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            username_input = st.text_input("Username")
            password_input = st.text_input("Password", type="password")
            submit_login = st.form_submit_button("Sign In")
            
            if submit_login:
                user_record = USER_DATABASE.get(username_input.strip().lower())
                if user_record and user_record["password"] == hash_password(password_input):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = username_input
                    st.session_state["role"] = user_record["role"]
                    st.session_state["name"] = user_record["name"]
                    st.success(f"Welcome back, {user_record['name']}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password. Please try again.")
    st.stop()

# Helper function to get current Philippine Time
def get_ph_time():
    return datetime.now(ZoneInfo("Asia/Manila"))

# Helper for a single cohesive civilian 12-hour time text entry with AM/PM default
def civilian_time_text_field(label, key_suffix=""):
    ph_now = get_ph_time()
    default_time_str = ph_now.strftime("%I:%M %p")
    val = st.text_input(label, value=default_time_str, key=f"time_txt_{key_suffix}", placeholder="e.g. 10:35 PM")
    return val

# ---------------------------------------------------------
# 2. SORTED HOSPITAL UNIT AREAS LIST
# ---------------------------------------------------------
HOSPITAL_UNIT_AREAS = [
    "None", "GNU 1C", "GNU 2A", "GNU 2B", "GNU 2C", "GNU 2D", "GNU 3A", "GNU 3B", "GNU 3C", "GNU 4A", "ICU", "NSU", "PCN", "PICU", "OUTBORN"
]

# ---------------------------------------------------------
# 3. EXACT SPECIALTIES
# ---------------------------------------------------------
SPECIALTIES_BY_FIELD = {
    "Anaesthesiology": ["GENERAL ANAESTHESIOLOGY", "NEURO - ANAESTHESIOLOGY", "PEDIA - ANAESTHESIOLOGY"],
    "Emergency & Family Medicine": ["EMERGNCY MEDICINE", "FAMILY MEDICINE"],
    "Internal Medicine & Subspecialties": ["CARDIOLOGY", "CLINICAL HAEMATOLOGY", "DERMATOLOGY", "ENDOCRINOLOGY", "GASTROENTEROLOGY", "HEPATOLOGY", "GERIATRIC MEDICINE", "INFECTIOUS DISEASES", "INTENSIVE CARE MEDICINE", "INTERNAL MEDICINE", "MEDICAL ONCOLOGY", "NEPHROLOGY", "NEUROLOGY", "PALLIATIVE MEDICINE", "RESPIRATORY MEDICINE", "RHEUMATOLOGY"],
    "Obstetrics & Gynaecology": ["GYNAE-ONCOLOGY", "MATERNAL FETAL MEDICINE", "OBSTETRICS & GYNAECOLOGY", "REPRODUCTIVE MEDICINE", "URO-GYNAECOLOGY"],
    "Oncology, Radiology & Physical Medicine": ["CLINICAL ONCOLOGY", "CLINICAL RADIOLOGY", "NUCLEAR MEDICINE", "ONCOLOGY", "RADIATION ONCOLOGY", "REHABILITATION MEDICINE", "SPORTS MEDICINE"],
    "Paediatrics & Subspecialties": ["ADOLESCENT MEDICINE", "CLINICAL GENETICS", "DEVELOPMENTAL PAEDIATRICS", "GENERAL PAEDIATRICS", "NEONATOLOGY", "PAEDIATRIC CARDIOLOGY", "PAEDIATRIC DERMATOLOGY", "PAEDIATRIC ENDOCRINOLOGY", "PAEDIATRIC GASTROENTEROLOGY", "PAEDIATRIC HAEMATOLOGY & ONCOLOGY", "PAEDIATRIC INFECTIOUS DISEASES", "PAEDIATRIC INTENSIVE CARE", "PAEDIATRIC NEPHROLOGY", "PAEDIATRIC NEUROLOGY", "PAEDIATRIC RESPIRATORY MEDICINE", "PAEDIATRIC RHEUMATOLOGY", "PAEDIATRICS AND CHILD HEALTH"],
    "Pathology": ["ANATOMICAL PATHOLOGY", "CHEMICAL PATHOLOGY", "CHEMICAL PATHOLOGY (METABOLIC MEDICINE)", "FORENSIC PATHOLOGY", "GENERAL PATHOLOGY", "GENETIC PATHOLOGY", "HAEMATOLOGY", "TRANSFUSION MEDICINE"],
    "Psychiatry": ["CHILD AND ADOLESCENT PSYCHIATRY", "FORENSIC PSYCHIATRY", "PSYCHIATRY"],
    "Public, Occupational & Military Health": ["COMMUNICABLE DISEASE EPIDEMIOLOGY", "MILITARY MEDICINE", "NON-COMMUNICABLE DISEASE EPIDEMIOLOGY", "OCCUPATIONAL HEALTH", "PUBLIC HEALTH MEDICINE"],
    "Surgical Specialties & Subspecialties": ["ADVANCED MUSCOSKELETAL TRAUMA", "ARTHOPLASTY", "ARTHROSCOPY & SPORT SURGERY", "BREAST / AND ENDOCRINE SURGERY", "COLORECTAL SURGERY", "GENERAL SURGERY", "HEPATOBILIARY SURGERY", "NEUROSURGERY", "OPHTHALMOLOGY", "ORTHOPAEDIC ONCOLOGY", "ORTHOPAEDIC SURGERY", "OTORHINOLARYNGOLOGY (ENT)", "PAEDIATRIC ORTHOPAEDICS", "PAEDIATRIC SURGERY", "PLASTIC SURGERY", "SPINE SURGERY", "THORACIC / CARDIOTHORACIC SURGERY", "UPPER GIT SURGERY", "UPPER LIMB & MICROSURGERY", "UROLOGY", "VASCULAR SURGERY"]
}

SPECIALTY_DROPDOWN_OPTIONS = ["None", "OTHERS"]
for field in sorted(SPECIALTIES_BY_FIELD.keys()):
    for spec in sorted(SPECIALTIES_BY_FIELD[field]):
        SPECIALTY_DROPDOWN_OPTIONS.append(spec)

def get_spec_index(default_name):
    if default_name in SPECIALTY_DROPDOWN_OPTIONS:
        return SPECIALTY_DROPDOWN_OPTIONS.index(default_name)
    return 0

# ---------------------------------------------------------
# 4. SHEET HEADERS
# ---------------------------------------------------------
SHEET_HEADERS = {
    "Emergency Care Complex (ECC)": ['MONTH', 'DATE', 'TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'DIAGNOSIS', 'DISEASE CATEGORY', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 'HOSPITALIZATION MODE', 'CASE TYPE', 'MODE OF PAYMENT', 'ADMITTED TO', 'PATIENT STATUS', 'CASE COUNT'],
    "Endoscopy Unit (ENDO)": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'PROCEDURE CATEGORY', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION', 'SURGEON / PROCEDURALIST', 'SURGEON SPECIALIZATION', 'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION', 'PROCEDURE NATURE', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT'],
    "Hemodialysis Unit (HDU)": ['MONTH', 'DATE', 'TRUE DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'DIAGNOSIS', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION', 'DIALYSIS SHIFT SLOT', 'HOSPITALIZATION MODE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT'],
    "OBGYNE Care Complex (LRDR-OB Surgery)": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'PRE-OP DIAGNOSIS', 'POST-OP DIAGNOSIS', 'PROCEDURE NAME', 'SURGICAL PROCEDURE', 'PROCEDURE CATEGORY', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION', 'SURGEON / OBGYNE', 'SURGEON SPECIALIZATION', 'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION', 'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT'],
    "Surgical Care Complex (OR Main)": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'PRE-OP DIAGNOSIS', 'POST-OP DIAGNOSIS', 'PROCEDURE', 'PROCEDURE CATEGORY', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION', 'PRIMARY SURGEON', 'SURGEON SPECIALIZATION', 'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION', 'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT'],
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)": ['MONTH', 'DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AOG', 'AGE', 'DIAGNOSIS', 'DIAGNOSIS CATEGORY', 'ADMITTED FROM', 'ADMITTED TO', 'TRANSFERRED TO', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION', 'HOSPITALIZATION MODE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT']
}

# ---------------------------------------------------------
# GOOGLE SHEETS HELPER FUNCTIONS
# ---------------------------------------------------------
@st.cache_resource
def init_google_sheets():
    from google.oauth2.service_account import Credentials
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" in st.secrets:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            pk = str(creds_dict["private_key"]).strip("'\" \n\r").replace("\\n", "\n")
            if "-----BEGIN PRIVATE KEY-----" in pk:
                start = pk.find("-----BEGIN PRIVATE KEY-----")
                end = pk.find("-----END PRIVATE KEY-----") + len("-----END PRIVATE KEY-----")
                pk = pk[start:end]
            creds_dict["private_key"] = pk
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    else:
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    return gspread.authorize(creds)

sh = init_google_sheets()

def ensure_google_sheets_exist():
    try:
        existing = [ws.title for ws in sh.worksheets()]
    except: existing = []
    if "Hospital Information System" not in existing:
        ws = sh.add_worksheet(title="Hospital Information System", rows=100, cols=4)
        ws.update('A4:D4', [['Department / Module', 'Total Census Records', 'Daily Patient Census', 'Monthly Patient Census']])
    for s_name, cols in SHEET_HEADERS.items():
        if s_name not in existing:
            ws = sh.add_worksheet(title=s_name, rows=1000, cols=len(cols))
            ws.update('A4', [cols])

def append_record_to_google_sheet(sheet_name, row_dict):
    ensure_google_sheets_exist()
    ws = sh.worksheet(sheet_name)
    headers = ws.row_values(4)
    row = [str(row_dict.get(h, "")) for h in headers]
    ws.append_row(row)
    return True

def read_google_sheet(sheet_name):
    ensure_google_sheets_exist()
    try:
        data = sh.worksheet(sheet_name).get_all_values()
        return pd.DataFrame(data[4:], columns=data[3]) if len(data) >= 4 else pd.DataFrame()
    except: return pd.DataFrame()

def check_existing_patient_ai(sheet_name, last_name, fn, curr_date_str):
    df = read_google_sheet(sheet_name)
    if df.empty: return None
    ln, first = str(last_name).strip().upper(), str(fn).strip().upper()
    matches = df[(df['LAST NAME'].astype(str).str.strip().str.upper() == ln) & (df['FIRST NAME'].astype(str).str.strip().str.upper() == first)]
    return matches[matches['DATE'].astype(str).str.strip() == curr_date_str].iloc[-1].to_dict() if not matches.empty else None

ensure_google_sheets_exist()

# ---------------------------------------------------------
# UI INTERFACE
# ---------------------------------------------------------
# (Omitted logo logic for brevity - keeping existing functionality)
# Sidebar Setup
st.sidebar.markdown(f"**Logged in as:** {st.session_state['name']}")
st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
st.sidebar.markdown("---")
# ... (Navigation and Export Sidebar UI)

# Registration Form Helper
def render_comanagement_ui(key_prefix, num_comanage):
    st.subheader("🤝 Co-Management Physician Settings")
    cm_entries = []
    for i in range(int(num_comanage)):
        c1, c2 = st.columns([2, 2])
        with c1:
            cm_name = st.text_input(f"CM Physician #{i+1} Name", value="", key=f"cm_name_{key_prefix}_{i}")
        with c2:
            cm_spec = st.selectbox(f"CM Physician #{i+1} Spec", SPECIALTY_DROPDOWN_OPTIONS, key=f"cm_spec_{key_prefix}_{i}")
        cm_entries.append((cm_name, cm_spec))
    return cm_entries

# Logic for rendering forms (abbreviated example for ECC)
if selected_sheet == "Emergency Care Complex (ECC)":
    # Patient Demographics
    with st.form("ecc_form"):
        st.subheader("👤 Patient Demographics")
        # ... fields
        
        col_m, col_c = st.columns([1, 1])
        with col_m:
            st.subheader("👨‍⚕️ Medical & Surgical Care Team")
            # ... fields
        with col_c:
            num_comanage = st.number_input("Count", min_value=0, max_value=5, value=0, step=1, key="num_cm_ecc")
            cm_entries = render_comanage_ui("ecc", num_comanage)
        
        # ... submit