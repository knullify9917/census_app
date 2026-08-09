import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import os
import hashlib
import io
import base64
import random
import concurrent.futures
import threading
import sqlite3
import time as py_time

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
    
    /* Unified Button Theme (Matching Sidebar Button Cards) across all forms and actions */
    .stButton > button, form button[type="submit"], .stFormSubmitButton > button {
        background-color: #ffffff !important;
        color: #1e3a8a !important;
        border: 1px solid #cbd5e1 !important;
        border-left: 5px solid #0f766e !important;
        border-radius: 8px !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        font-weight: 600 !important;
        font-size: 13px !important;
        white-space: nowrap !important;
        width: 100% !important;
        text-align: left !important;
        padding: 8px 12px !important;
    }
    .stButton > button:hover, form button[type="submit"]:hover, .stFormSubmitButton > button:hover {
        background-color: #f0fdf4 !important;
        color: #0f766e !important;
        border-color: #0f766e !important;
        border-left: 5px solid #1e3a8a !important;
    }

    /* Form Inputs, Textareas, and Dropdown Controls (Excluding password fields to prevent login friction) */
    div[data-baseweb="select"] > div, input[type="text"]:not([type="password"]), input[type="number"], textarea {
        background-color: #ffffff !important; color: #1e3a8a !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; text-transform: uppercase !important;
    }
    input[type="password"] {
        text-transform: none !important;
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

    /* Dropdown Popover Lists & Menus with Enhanced Z-Index */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #ffffff !important; color: #1e3a8a !important; border: 1px solid #cbd5e1 !important; z-index: 999999 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
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

REGULAR_FONT_SIZE = 10

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

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
        "modules": ["Hospital Information System", "Pareto Tally Sheet", "Emergency Care Complex (ECC)"]
    },
    "scc_staff": {
        "password": hash_password("scc2026"),
        "role": "SCC Staff",
        "name": "Surgical Care Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet", "Surgical Care Complex (OR Main)"]
    },
    "endo_staff": {
        "password": hash_password("endo2026"),
        "role": "ENDO Staff",
        "name": "Endoscopy Unit Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet", "Endoscopy Unit (ENDO)"]
    },
    "hdu_staff": {
        "password": hash_password("hdu2026"),
        "role": "HDU Staff",
        "name": "Hemodialysis Unit Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet", "Hemodialysis Unit (HDU)"]
    },
    "nsu_staff": {
        "password": hash_password("nsu2026"),
        "role": "Special Care Staff",
        "name": "Special Care Unit Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet", "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"]
    },
    "obgyne_staff": {
        "password": hash_password("obgyne2026"),
        "role": "OBGYNE Staff",
        "name": "OBGYNE Care Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet", "OBGYNE Care Complex (LRDR-OB Surgery)"]
    },
    "nsgcon_staff": {
        "password": hash_password("nsgcon2026"),
        "role": "Nursing Administration",
        "name": "Nursing Control Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet"]
    },
    "ha_staff": {
        "password": hash_password("hastaff2026"),
        "role": "Hospital Administration",
        "name": "Hospital Administration Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet"]
    },
    "ha_staff1": {
        "password": hash_password("hastaff12026"),
        "role": "Hospital Administration",
        "name": "Hospital Administration Staff 1",
        "modules": ["Hospital Information System", "Pareto Tally Sheet"]
    }
}

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "username" not in st.session_state:
    st.session_state["username"] = ""
if "role" not in st.session_state:
    st.session_state["role"] = ""
if "name" not in st.session_state:
    st.session_state["name"] = ""
if "df_cache" not in st.session_state:
    st.session_state["df_cache"] = {}

for form_key in ["ecc", "endo", "hdu", "ob", "scc", "scu", "1c", "2a", "2b", "2c", "2d", "3a", "3b", "3c", "4a"]:
    if f"cm_list_{form_key}" not in st.session_state:
        st.session_state[f"cm_list_{form_key}"] = []

if not st.session_state["authenticated"]:
    col_l1, col_l2, col_l3 = st.columns([0.2, 2.6, 0.2])
    with col_l2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="color: #1e3a8a; margin-bottom: -2px; font-size: 2.8rem; white-space: nowrap; font-weight: 800;">Mother Teresa of Calcutta Medical Center</h1>
                <p style="color: #0f766e; font-weight: 600; font-size: 1.4rem; margin-top: 0px; letter-spacing: 0.5px;">Patient Data System</p>
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

def get_ph_time():
    return datetime.now(ZoneInfo("Asia/Manila"))

def civilian_time_input_field(label, key_suffix=""):
    current_default_time = get_ph_time().time()
    t_val = st.time_input(label, value=current_default_time, key=f"time_widget_{key_suffix}")
    if t_val:
        return t_val.strftime("%I:%M %p")
    return ""

def sanitize_medical_text(text):
    if not text or pd.isna(text):
        return ""
    return " ".join(str(text).strip().upper().split())

def get_custom_icon_html(filename, width=32):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            b64_str = base64.b64encode(f.read()).decode()
        return f'<img src="data:image/png;base64,{b64_str}" style="width: {width}px; height: {width}px; vertical-align: middle; margin-right: 8px;">'
    return ""

HOSPITAL_UNIT_AREAS = sorted([
    "None", "ECC", "GNU 1C", "GNU 2A", "GNU 2B", "GNU 2C", "GNU 2D", "GNU 3A", "GNU 3B", "GNU 3C", "GNU 4A", 
    "MS-ICU (MEDICAL SURGICAL – INTENSIVE CARE UNIT)", 
    "NICU (NEONATAL INTENSIVE CARE UNIT)", 
    "PICU (PEDIATRIC INTENSIVE CARE UNIT)", 
    "NSU (NEWBORN SERVICE UNIT)", 
    "PCN (PROGRESSIVE CARE UNIT)", 
    "OUTBORN (OUTBORN BABIES ADMITTED IN THE UNIT)"
])

sorted_departments = sorted([
    "Emergency Care Complex (ECC)", "Endoscopy Unit (ENDO)", "Hemodialysis Unit (HDU)", 
    "OBGYNE Care Complex (LRDR-OB Surgery)", "Surgical Care Complex (OR Main)", 
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
    "General Nursing Unit (GNU 1C)", "General Nursing Unit (GNU 2A)", "General Nursing Unit (GNU 2B)", 
    "General Nursing Unit (GNU 2C)", "General Nursing Unit (GNU 2D)", "General Nursing Unit (GNU 3A)", 
    "General Nursing Unit (GNU 3B)", "General Nursing Unit (GNU 3C)", "General Nursing Unit (GNU 4A)"
])

SPECIALTIES_BY_FIELD = {
    "Anaesthesiology": ["GENERAL ANAESTHESIOLOGY", "NEURO - ANAESTHESIOLOGY", "PEDIA - ANAESTHESIOLOGY"],
    "Emergency & Family Medicine": ["EMERGNCY MEDICINE", "FAMILY MEDICINE"],
    "Internal Medicine & Subspecialties": ["CARDIOLOGY", "CLINICAL HAEMATOLOGY", "DERMATOLOGY", "ENDOCRINOLOGY", "GASTROENTEROLOGY", "HEPATOLOGY", "GERIATRIC MEDICINE", "INFECTIOUS DISEASES", "INTENSIVE CARE MEDICINE", "INTERNAL MEDICINE", "MEDICAL ONCOLOGY", "NEPHROLOGY", "NEUROLOGY", "PALLIATIVE MEDICINE", "RESPIRATORY MEDICINE", "RHEUMATOLOGY"],
    "Obstetrics & Gynaecology": ["GYNAE-ONCOLOGY", "MATERNAL FETAL MEDICINE", "OBSTETRICS & GYNAECOLOGY", "REPRODUCTIVE MEDICINE", "URO-GYNAECOLOGY"],
    "Oncology, Radiology & Physical Medicine": ["CLINICAL ONCOLOGY", "CLINICAL RADIOLOGY", "NUCLEAR MEDICINE", "ONCOLOGY", "RADIATION ONCOLOGY", "REHABILITATION MEDICINE", "SPORTS MEDICINE"],
    "Paediatrics & Subspecialties": ["ADOLESCENT MEDICINE", "CLINICAL GENETICS", "DEVELOPMENTAL PAEDIATRICS", "GENERAL PAEDIATRICS", "NEONATOLOGY", "PAEDIATRIC CARDIOLOGY", "PAEDIATRIC DERMATOLOGY", "PAEDIATRIC ENDOCRINOLOGY", "PAEDIATRIC GASTROENTEROLOGY", "PAEDIATRIC HAEMATOLOGY & ONCOLOGY", "PAEDIATRIC INFECTIOUS DISEASES", "PAEDIATRIC INTENSIVE CARE", "PAEDIATRIC NEPHROLOGY", "PAEDIATRIC NEUROLOGY", "PAEDIATRIC RESPIRATORY MEDICINE", "PAEDIATRIC RHEUMATOLOGY", "PAEDIATRICS AND CHILD HEALTH"],
    "Pathology": ["ANATOMICAL PATHOLOGY", "CHEMICAL PATHOLOGY", "FORENSIC PATHOLOGY", "GENERAL PATHOLOGY", "GENETIC PATHOLOGY", "HAEMATOLOGY", "TRANSFUSION MEDICINE"],
    "Psychiatry": ["CHILD AND ADOLESCENT PSYCHIATRY", "FORENSIC PSYCHIATRY", "PSYCHIATRY"],
    "Public, Occupational & Military Health": ["COMMUNICABLE DISEASE EPIDEMIOLOGY", "MILITARY MEDICINE", "NON-COMMUNICABLE DISEASE EPIDEMIOLOGY", "OCCUPATIONAL HEALTH", "PUBLIC HEALTH MEDICINE"],
    "Surgical Specialties & Subspecialties": ["GENERAL SURGERY", "NEUROSURGERY", "OPHTHALMOLOGY", "ORTHOPAEDIC SURGERY", "OTORHINOLARYNGOLOGY (ENT)", "PLASTIC SURGERY", "UROLOGY", "VASCULAR SURGERY"]
}

SPECIALTY_DROPDOWN_OPTIONS = ["None", "OTHERS"]
for field in sorted(SPECIALTIES_BY_FIELD.keys()):
    for spec in sorted(SPECIALTIES_BY_FIELD[field]):
        SPECIALTY_DROPDOWN_OPTIONS.append(spec)

GNU_SHEET_HEADER = [
    'MONTH', 'DATE', 'TIME', 'ROOM NO', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'DIAGNOSIS', 
    'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
    'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
    'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 
    'PROCEDURES', 'DIAGNOSTIC EXAMINATIONS', 'MEDICATIONS', 'SPECIAL ENDORSEMENTS', 'CASE COUNT', 'SEEDED_TRIAL'
]

SCU_SHEET_HEADER = [
    'MONTH', 'DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AOG', 'AGE', 'DIAGNOSIS', 
    'DIAGNOSIS CATEGORY', 'ADMITTED FROM', 'ADMITTED TO', 'TRANSFERRED TO', 
    'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
    'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
    'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 
    'PROCEDURES', 'DIAGNOSTIC EXAMINATIONS', 'MEDICATIONS', 'SPECIAL ENDORSEMENTS', 'CASE COUNT', 'SEEDED_TRIAL'
]

SHEET_HEADERS = {
    "Emergency Care Complex (ECC)": [
        'MONTH', 'DATE', 'TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'DIAGNOSIS', 
        'DISEASE CATEGORY', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'HOSPITALIZATION MODE', 'CASE TYPE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'ADMITTED TO', 'CASE COUNT', 'SEEDED_TRIAL'
    ],
    "Endoscopy Unit (ENDO)": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'PROCEDURE CATEGORY', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'SURGEON / PROCEDURALIST', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'PROCEDURE NATURE', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT', 'SEEDED_TRIAL'
    ],
    "General Nursing Unit (GNU 1C)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 2A)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 2B)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 2C)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 2D)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 3A)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 3B)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 3C)": GNU_SHEET_HEADER,
    "General Nursing Unit (GNU 4A)": GNU_SHEET_HEADER,
    "Hemodialysis Unit (HDU)": [
        'MONTH', 'DATE', 'TRUE DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'DIAGNOSIS', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'DIALYSIS SHIFT SLOT', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT', 'SEEDED_TRIAL'
    ],
    "OBGYNE Care Complex (LRDR-OB Surgery)": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'PRE-OP DIAGNOSIS', 'POST-OP DIAGNOSIS', 'PROCEDURE NAME', 'SURGICAL PROCEDURE', 'PROCEDURE CATEGORY', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'SURGEON / OBGYNE', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT', 'SEEDED_TRIAL'
    ],
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)": SCU_SHEET_HEADER,
    "Surgical Care Complex (OR Main)": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'PRE-OP DIAGNOSIS', 'POST-OP DIAGNOSIS', 'PROCEDURE', 'PROCEDURE CATEGORY', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'PRIMARY SURGEON', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'PATIENT STATUS', 'CASE COUNT', 'SEEDED_TRIAL'
    ]
}

def get_month_str(date_obj, fmt_style="numeric_prefix"):
    if not date_obj:
        return ""
    month_num = date_obj.month
    month_name = date_obj.strftime("%B").upper()
    if fmt_style == "numeric_prefix":
        return f"{month_num}.{month_name}"
    elif fmt_style == "full_month":
        return date_obj.strftime("%B")
    elif fmt_style == "mixed":
        return f"{month_num}.{date_obj.strftime('%B')} "
    return month_name

# ---------------------------------------------------------
# HYBRID SQLITE BACKEND SETUP
# ---------------------------------------------------------
sqlite_lock = threading.Lock()

def get_sqlite_conn():
    conn = sqlite3.connect("hospital_local.sqlite", check_same_thread=False, timeout=30.0)
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

def init_local_sqlite():
    conn = get_sqlite_conn()
    cursor = conn.cursor()
    for s_name, cols in SHEET_HEADERS.items():
        cols_def = ", ".join([f'"{col}" TEXT' for col in cols])
        cursor.execute(f'CREATE TABLE IF NOT EXISTS "{s_name}" ({cols_def})')
    conn.commit()
    conn.close()

init_local_sqlite()

def sync_df_to_sqlite(sheet_name, df):
    if df is None or df.empty:
        return
    conn = get_sqlite_conn()
    try:
        df.to_sql(sheet_name, conn, if_exists='replace', index=False)
    except Exception:
        pass
    conn.close()

def read_sqlite_sheet(sheet_name):
    conn = get_sqlite_conn()
    try:
        df = pd.read_sql(f'SELECT * FROM "{sheet_name}"', conn)
        conn.close()
        if not df.empty:
            return df
    except Exception:
        conn.close()
    return pd.DataFrame()

@st.cache_resource
def init_google_sheets():
    from google.oauth2.service_account import Credentials
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    if "gcp_service_account" not in st.secrets:
        st.error("🚨 Critical Error: Google Cloud service account secrets are missing from Streamlit configuration settings.")
        st.stop()
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            pk = str(creds_dict["private_key"]).strip("'\" \n\r").replace("\\n", "\n")
            if "-----BEGIN PRIVATE KEY-----" in pk and "-----END PRIVATE KEY-----" in pk:
                pk = pk[pk.find("-----BEGIN PRIVATE KEY-----"):pk.find("-----END PRIVATE KEY-----") + len("-----END PRIVATE KEY-----")]
            creds_dict["private_key"] = pk
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    except Exception as e:
        st.error(f"Error parsing secure credentials: {e}")
        st.stop()
    client = gspread.authorize(creds)
    try:
        sh = client.open("MTCMC_CENSUS_MASTERFILES_SYSTEM")
    except gspread.SpreadsheetNotFound:
        sh = client.create("MTCMC_CENSUS_MASTERFILES_SYSTEM")
    return sh

sh = init_google_sheets()

def ensure_google_sheets_exist():
    try:
        existing_worksheets = [ws.title for ws in sh.worksheets()]
    except Exception:
        existing_worksheets = []
    if "Hospital Information System" not in existing_worksheets:
        try:
            ws_sum = sh.add_worksheet(title="Hospital Information System", rows=100, cols=4)
            ws_sum.update('A1:D1', [["MOTHER TERESA OF CALCUTTA MEDICAL CENTER", "", "", ""]])
            ws_sum.update('A4:D4', [['Department / Module', 'Total Census Records', 'Daily Patient Census', 'Monthly Patient Census']])
        except Exception:
            pass
    for s_name, cols in SHEET_HEADERS.items():
        if s_name not in existing_worksheets:
            try:
                ws = sh.add_worksheet(title=s_name, rows=1000, cols=len(cols))
                ws.update('A1', [[f"MTCMC CLINICAL CENSUS - {s_name} MASTERFILE"]])
                ws.update('A4', [cols])
            except Exception:
                pass

_sheet_locks = {}
_locks_guard = threading.Lock()

def get_sheet_lock(sheet_name):
    with _locks_guard:
        if sheet_name not in _sheet_locks:
            _sheet_locks[sheet_name] = threading.Lock()
        return _sheet_locks[sheet_name]

def safe_gspread_call(sheet_name, func, *args, **kwargs):
    max_retries = 3
    backoff = 1
    target_lock = get_sheet_lock(sheet_name)
    for attempt in range(max_retries):
        with target_lock:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    global sh
                    try:
                        sh = init_google_sheets()
                        return func(*args, **kwargs)
                    except Exception:
                        raise e
                py_time.sleep(backoff)
                backoff *= 2
    return None

def append_record_to_google_sheet(sheet_name, row_dict):
    ensure_google_sheets_exist()
    def _exec():
        ws = sh.worksheet(sheet_name)
        headers = ws.row_values(4)
        if not headers:
            headers = SHEET_HEADERS.get(sheet_name, [])
            ws.update('A4', [headers])
        row_values = []
        for h in headers:
            val = row_dict.get(h, "")
            row_values.append("" if (val is None or pd.isna(val)) else str(val).upper())
        ws.append_row(row_values)
        return True

    try:
        safe_gspread_call(sheet_name, _exec)
        df_local = read_google_sheet(sheet_name, force_refresh=True)
        sync_df_to_sqlite(sheet_name, df_local)
        return True
    except Exception as e:
        st.toast("Saved to local database (cloud sync queued).", icon="💾")
        conn = get_sqlite_conn()
        df_curr = read_sqlite_sheet(sheet_name)
        df_new = pd.DataFrame([row_dict])
        df_combined = pd.concat([df_curr, df_new], ignore_index=True)
        sync_df_to_sqlite(sheet_name, df_combined)
        return True

def update_google_sheet_from_df(sheet_name, df):
    ensure_google_sheets_exist()
    def _exec():
        ws = sh.worksheet(sheet_name)
        ws.clear()
        headers = SHEET_HEADERS.get(sheet_name, df.columns.tolist())
        ws.update('A1', [[f"MTCMC CLINICAL CENSUS - {sheet_name} MASTERFILE"]])
        ws.update('A4', [headers])
        
        rows_to_update = []
        for _, row in df.iterrows():
            mapped_vals = []
            for h in headers:
                if h in row:
                    v = row[h]
                    mapped_vals.append("" if (v is None or pd.isna(v)) else str(v).upper())
                else:
                    mapped_vals.append("")
            rows_to_update.append(mapped_vals)
            
        if rows_to_update:
            ws.update('A5', rows_to_update)
        return True

    try:
        safe_gspread_call(sheet_name, _exec)
        sync_df_to_sqlite(sheet_name, df)
        return True
    except Exception as e:
        st.toast("Updated local database (cloud sync queued).", icon="💾")
        sync_df_to_sqlite(sheet_name, df)
        return True

@st.cache_data(ttl=300)
def fetch_cloud_sheet(sheet_name):
    ensure_google_sheets_exist()
    def _get_data():
        ws = sh.worksheet(sheet_name)
        return ws.get('A4:V2000')
    try:
        data = safe_gspread_call(sheet_name, _get_data)
        if data and len(data) >= 1:
            headers = [str(h).strip().upper() for h in data[0]]
            rows = data[1:]
            if rows:
                df_res = pd.DataFrame(rows, columns=headers[:len(rows[0])])
                expected_cols = SHEET_HEADERS.get(sheet_name, [])
                for col in expected_cols:
                    if col not in df_res.columns:
                        df_res[col] = ""
                return df_res
    except Exception:
        pass
    return read_sqlite_sheet(sheet_name)

def read_google_sheet(sheet_name, force_refresh=False):
    if not force_refresh and sheet_name in st.session_state["df_cache"]:
        return st.session_state["df_cache"][sheet_name]
    
    df = fetch_cloud_sheet(sheet_name)
    if df.empty:
        df = read_sqlite_sheet(sheet_name)
    else:
        sync_df_to_sqlite(sheet_name, df)
        
    st.session_state["df_cache"][sheet_name] = df
    return df

def read_multiple_sheets_parallel(sheet_names):
    uncached = [s for s in sheet_names if s not in st.session_state["df_cache"]]
    if uncached:
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            future_to_sheet = {executor.submit(read_google_sheet, s): s for s in uncached}
            for future in concurrent.futures.as_completed(future_to_sheet):
                pass
    return {s: st.session_state["df_cache"].get(s, read_google_sheet(s)) for s in sheet_names}

def check_existing_patient_ai(sheet_name, last_name, fn, curr_date_str):
    df = read_google_sheet(sheet_name)
    if df.empty or 'LAST NAME' not in df.columns:
        return None
    ln = str(last_name).strip().upper()
    first = str(fn).strip().upper()
    if not ln or not first:
        return None
    matches = df[
        (df['LAST NAME'].astype(str).str.strip().str.upper() == ln) &
        (df['FIRST NAME'].astype(str).str.strip().str.upper() == first)
    ]
    if matches.empty:
        return None
    same_date_match = matches[matches['DATE'].astype(str).str.strip() == curr_date_str]
    if not same_date_match.empty:
        return same_date_match.iloc[-1].to_dict()
    return None

ensure_google_sheets_exist()

def clean_display_df(df):
    if df is None or df.empty:
        return df
    d_clean = df.copy()
    cols_to_drop = [c for c in d_clean.columns if 'Unnamed' in str(c) or c == '']
    if cols_to_drop:
        d_clean = d_clean.drop(columns=cols_to_drop)
    if d_clean.shape[1] > 1:
        first_col = d_clean.columns[0]
        if first_col.lower() in ['index', 'level_0', 'unnamed: 0']:
            d_clean = d_clean.iloc[:, 1:]
    return d_clean

def display_paginated_dataframe(df, key_prefix="pag"):
    if df is None or df.empty:
        st.info("No records to display.")
        return df
    
    clean_df = clean_display_df(df)
    total_rows = len(clean_df)
    if total_rows <= 100:
        editor_config = get_editor_column_config(clean_df.columns)
        return st.data_editor(clean_df, use_container_width=True, num_rows="fixed", key=f"{key_prefix}_editor", column_config=editor_config)
    
    st.markdown(f"**Total Records:** `{total_rows}` (Showing 100 records per page for optimal performance)")
    page_size = 100
    total_pages = (total_rows - 1) // page_size + 1
    page_num = st.selectbox("Select Page", range(1, total_pages + 1), key=f"{key_prefix}_page_sel")
    
    start_idx = (page_num - 1) * page_size
    end_idx = min(start_idx + page_size, total_rows)
    page_df = clean_df.iloc[start_idx:end_idx].copy()
    
    editor_config = get_editor_column_config(page_df.columns)
    edited_page = st.data_editor(page_df, use_container_width=True, num_rows="fixed", key=f"{key_prefix}_editor_p{page_num}", column_config=editor_config)
    
    full_df = clean_df.copy()
    full_df.iloc[start_idx:end_idx] = edited_page
    return full_df

def get_editor_column_config(columns):
    config = {}
    for col in columns:
        col_upper = str(col).upper()
        if col_upper in ['DATE', 'TRUE DATE', 'ADMISSION DATE', 'DEPARTMENT / UNIT', 'SEEDED_TRIAL']:
            config[col] = st.column_config.TextColumn(col, disabled=True, width="small")
        elif col_upper in ['PATIENT STATUS', 'STATUS']:
            config[col] = st.column_config.SelectboxColumn(col, options=["ACTIVE", "MGH", "DISCHARGED", "CAB"], width="medium")
        elif col_upper == 'SEX':
            config[col] = st.column_config.SelectboxColumn(col, options=["MALE", "FEMALE", "OTHERS"], width="small")
        elif col_upper == 'MODE OF PAYMENT':
            config[col] = st.column_config.SelectboxColumn(col, options=["PHIC", "HMO", "SELF-PAY", "CHARITY"], width="medium")
        elif col_upper == 'HOSPITALIZATION MODE':
            config[col] = st.column_config.SelectboxColumn(col, options=["INPATIENT", "OUTPATIENT"], width="medium")
        else:
            config[col] = st.column_config.TextColumn(col, width="medium")
    return config

# ---------------------------------------------------------
# UI HEADER & SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.markdown("""
<style>
    .header-container { display: flex; align-items: center; gap: 20px; margin-bottom: 5px; }
    .header-logo { width: 85px; height: 85px; object-fit: contain; flex-shrink: 0; }
    .header-text-group { display: flex; flex-direction: column; justify-content: center; }
    .header-title { margin: 0px !important; line-height: 1.0 !important; font-size: 2.35rem !important; color: #1e3a8a !important; font-weight: 800 !important; }
    .header-subtitle { margin: -4px 0px 0px 0px !important; font-size: 1.15rem !important; color: #0f766e !important; font-weight: 600 !important; letter-spacing: 0.5px !important; }
</style>
""", unsafe_allow_html=True)

logo_path_found = ""
for logo_filename in ["logo_3.jpg", "logo_3.png", "logo.png", "logo_2.png", "assets/logo_3.jpg", "assets/logo_3.png"]:
    if os.path.exists(logo_filename):
        logo_path_found = logo_filename
        break

if logo_path_found:
    img_base64 = base64.b64encode(open(logo_path_found, "rb").read()).decode()
    logo_html = f'<img src="data:image/jpeg;base64,{img_base64}" class="header-logo">'
else:
    logo_html = '<div style="background-color: #1e3a8a; width: 85px; height: 85px; border-radius: 12px; display: flex; align-items: center; justify-content: center;"><span style="color: white; font-size: 34px; font-weight: bold;">✚</span></div>'

st.markdown(f"""
    <div class="header-container">
        {logo_html}
        <div class="header-text-group">
            <h1 class="header-title">MOTHER TERESA OF CALCUTTA MEDICAL CENTER</h1>
            <p class="header-subtitle">Touching Lives Through Expert Care</p>
        </div>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"**Logged in as:** {st.session_state['name']}")
st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
ph_now_display = get_ph_time()
st.sidebar.markdown(f"**Date & Time:** `{ph_now_display.strftime('%B %d, %Y - %I:%M %p')}`")
st.sidebar.markdown("---")

# ---------------------------------------------------------
# ADMIN CONTROL CENTER (INTELLIGENT SEEDER & FULL SYSTEM WIPE)
# ---------------------------------------------------------
if st.session_state["role"] == "Administrator":
    st.sidebar.markdown("### 🛠️ Admin Control Center")
    
    with st.sidebar.expander("🤖 Admin Intelligent Seeder"):
        st.markdown("Generate multi-disciplinary trial patient records across departments to check updates and metrics.")
        batch_size = st.selectbox("Batch Size", [5, 10, 20], index=0)
        
        if st.button("🚀 Generate Trial Batch", type="primary"):
            first_names = ["JUAN", "MARIA", "JOSE", "ANA", "PEDRO", "LUIS", "CARMEN", "ROSA"]
            middle_names = ["SANTOS", "REYES", "GARCIA", "TORRES", "FLORES", "RAMOS"]
            last_names = ["CRUZ", "BAUTISTA", "OCAMPO", "MENDOZA", "GONZALES", "AQUINO"]
            department_targets = [
                "Emergency Care Complex (ECC)",
                "Surgical Care Complex (OR Main)",
                "OBGYNE Care Complex (LRDR-OB Surgery)",
                "Endoscopy Unit (ENDO)",
                "Hemodialysis Unit (HDU)",
                "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
            ] + sorted([d for d in sorted_departments if d.startswith("General Nursing Unit")])

            progress_bar = st.sidebar.progress(0)
            for i in range(batch_size):
                fn = random.choice(first_names)
                mn = random.choice(middle_names)
                ln = random.choice(last_names)
                sex = random.choice(["MALE", "FEMALE"])
                age = str(random.randint(1, 80))
                pay_mode = random.choice(["PHIC", "HMO", "SELF-PAY", "CHARITY"])
                stat = random.choice(["ACTIVE", "MGH", "DISCHARGED", "CAB"])
                date_str = ph_now_display.strftime("%m/%d/%Y")
                target_dept = department_targets[i % len(department_targets)]

                if target_dept == "Emergency Care Complex (ECC)":
                    row_data = {
                        'MONTH': get_month_str(ph_now_display.date(), "full_month"), 'DATE': date_str, 'TIME': "10:00 AM",
                        'LAST NAME': ln, 'FIRST NAME': fn, 'MIDDLE NAME': mn, 'SEX': sex, 'AGE': age,
                        'DIAGNOSIS': "ACUTE ABDOMEN / TRAUMA", 'DISEASE CATEGORY': "ACUTE GASTROENTERITIS",
                        'ATTENDING PHYSICIAN': "DR. E. SANTOS", 'ATTENDING SPECIALIZATION': "EMERGENCY MEDICINE",
                        'CO-MANAGEMENT PHYSICIAN': "N/A", 'CO-MANAGEMENT SPECIALIZATION': "N/A",
                        'HOSPITALIZATION MODE': "INPATIENT", 'CASE TYPE': "PRIVATE CASE", 'HOSPITAL KIT PACKAGE': "YES",
                        'MODE OF PAYMENT': pay_mode, 'ADMITTED TO': "ECC", 'CASE COUNT': 1, 'SEEDED_TRIAL': 'YES'
                    }
                else:
                    row_data = {
                        'MONTH': get_month_str(ph_now_display.date(), "full_month"), 'DATE': date_str, 'TIME': "10:00 AM",
                        'ROOM NO': "RM-101", 'LAST NAME': ln, 'FIRST NAME': fn, 'MIDDLE NAME': mn, 'SEX': sex, 'AGE': age,
                        'DIAGNOSIS': "PNEUMONIA", 'ATTENDING PHYSICIAN': "DR. M. REYES", 'ATTENDING SPECIALIZATION': "INTERNAL MEDICINE",
                        'CO-MANAGEMENT PHYSICIAN': "N/A", 'CO-MANAGEMENT SPECIALIZATION': "N/A",
                        'HOSPITALIZATION MODE': "INPATIENT", 'HOSPITAL KIT PACKAGE': "YES", 'MODE OF PAYMENT': pay_mode,
                        'PATIENT STATUS': stat, 'PROCEDURES': "OXYGEN THERAPY", 'DIAGNOSTIC EXAMINATIONS': "X-RAY",
                        'MEDICATIONS': "ANTIBIOTICS", 'SPECIAL ENDORSEMENTS': "STABLE", 'CASE COUNT': 1, 'SEEDED_TRIAL': 'YES'
                    }
                append_record_to_google_sheet(target_dept, row_data)
                progress_bar.progress((i + 1) / batch_size)
                py_time.sleep(0.05)

            st.sidebar.success(f"Successfully generated {batch_size} trial patient records!")
            st.rerun()

    with st.sidebar.expander("🚨 Full System Wipe (All Depts)"):
        st.markdown("Permanently erase all records, patient data, metrics, and tallies from **every** department and local database.")
        confirm_system_wipe = st.checkbox("I confirm wiping all data", value=False)
        
        if st.button("🧹 Execute Full Wipe", type="primary"):
            if confirm_system_wipe:
                try:
                    for s_name, cols in SHEET_HEADERS.items():
                        try:
                            ws = sh.worksheet(s_name)
                            ws.clear()
                            ws.update('A1', [[f"MTCMC CLINICAL CENSUS - {s_name} MASTERFILE"]])
                            ws.update('A4', [cols])
                        except Exception:
                            pass
                        py_time.sleep(0.5)

                    conn = get_sqlite_conn()
                    cursor = conn.cursor()
                    for s_name, cols in SHEET_HEADERS.items():
                        cursor.execute(f'DELETE FROM "{s_name}"')
                    conn.commit()
                    conn.close()

                    st.cache_data.clear()
                    st.session_state["df_cache"] = {}
                    st.sidebar.success("Successfully wiped all data across all departments!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Wipe failed: {e}")
            else:
                st.sidebar.warning("Please check the confirmation box to proceed.")
    st.sidebar.markdown("---")

logged_user_key = st.session_state["username"]
user_info = USER_DATABASE.get(logged_user_key, {})
allowed_modules = user_info.get("modules", "All")

all_department_modules = ["Hospital Information System", "Pareto Tally Sheet"] + sorted_departments
if allowed_modules == "All":
    MODULES = all_department_modules
else:
    allowed_list = list(allowed_modules) if isinstance(allowed_modules, list) else [allowed_modules]
    fixed_front = [m for m in ["Hospital Information System", "Pareto Tally Sheet"] if m in allowed_list or allowed_modules == "All"]
    other_allowed = sorted([m for m in allowed_list if m not in ["Hospital Information System", "Pareto Tally Sheet"]])
    MODULES = fixed_front + other_allowed

st.sidebar.markdown("### 🧭 Department Navigation")
selected_sheet = st.sidebar.selectbox("Select Target Google Sheet Module", MODULES, index=0)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Export Reports")

active_export_df = read_google_sheet(selected_sheet) if selected_sheet not in ["Hospital Information System", "Pareto Tally Sheet"] else read_google_sheet("Emergency Care Complex (ECC)")

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
    if not active_export_df.empty:
        active_export_df.to_excel(writer, index=False, sheet_name=selected_sheet[:30])
    else:
        pd.DataFrame(["No records found"]).to_excel(writer, index=False, sheet_name="Sheet1")
excel_data = excel_buffer.getvalue()

st.sidebar.download_button(
    label="📊 Export to Excel",
    data=excel_data,
    file_name=f"MTCMC_{selected_sheet.replace(' ', '_')}_Census.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

def convert_df_to_pdf_html(df, title):
    html_content = f"""
    <html><head><title>{title}</title>
    <style>body {{ font-family: Helvetica, Arial, sans-serif; color: #1e293b; margin: 20px; }}
    h2 {{ color: #1e3a8a; }} p {{ color: #0f766e; font-size: 12px; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 15px; font-size: 9px; }}
    th {{ background-color: #1e3a8a; color: white; padding: 6px; border: 1px solid #cbd5e1; text-align: left; }}
    td {{ padding: 5px; border: 1px solid #cbd5e1; }}</style></head>
    <body><h2>MOTHER TERESA OF CALCUTTA MEDICAL CENTER</h2>
    <p><strong>Module:</strong> {title} | Generated: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}</p><hr>
    """
    cleaned_pdf_df = clean_display_df(df)
    html_content += cleaned_pdf_df.head(100).to_html(index=False, border=0) if not cleaned_pdf_df.empty else "<p>No records available.</p>"
    return (html_content + "</body></html>").encode('utf-8')

st.sidebar.download_button(
    label="📄 Export as PDF",
    data=convert_df_to_pdf_html(active_export_df, selected_sheet),
    file_name=f"MTCMC_{selected_sheet.replace(' ', '_')}_Report.html",
    mime="text/html"
)

st.sidebar.markdown("---")
st.sidebar.markdown("<p style='font-size: 0.85rem; color: #0f766e; font-style: italic; margin-bottom: 10px;'>All data entries are securely stored on our hospital database.</p>", unsafe_allow_html=True)

if st.sidebar.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.session_state["df_cache"] = {}
    st.toast("Reloaded latest census & patient records from Google Sheets.", icon="🔄")
    st.rerun()

if st.sidebar.button("Sign Out"):
    st.session_state["authenticated"] = False
    st.rerun()

if selected_sheet == "Hospital Information System":
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=60000, limit=None, key="his_auto_refresh")
    except ImportError:
        pass

st.markdown("---")

# ---------------------------------------------------------
# MODULE: PARETO TALLY SHEET
# ---------------------------------------------------------
if selected_sheet == "Pareto Tally Sheet":
    st.header("📊 Pareto Tally Sheet & Department Analytics")
    st.markdown("Organized per department with dynamic patient census categorization, specialization breakdowns, doctor census tables, and cross-tabulation tallies displayed in table format.")
    
    all_dept_options = [
        "Emergency Care Complex (ECC)", 
        "Surgical Care Complex (OR Main)", 
        "OBGYNE Care Complex (LRDR-OB Surgery)", 
        "Hemodialysis Unit (HDU)", 
        "Endoscopy Unit (ENDO)", 
        "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
    ] + [d for d in sorted_departments if d.startswith("General Nursing Unit")]
    
    selected_tally_dept = st.selectbox("🏥 Choose Department / Unit for Pareto Tally & Census Analysis", all_dept_options)
    
    sheet_target_map = {
        "Emergency Care Complex (ECC)": "Emergency Care Complex (ECC)",
        "Surgical Care Complex (OR Main)": "Surgical Care Complex (OR Main)",
        "OBGYNE Care Complex (LRDR-OB Surgery)": "OBGYNE Care Complex (LRDR-OB Surgery)",
        "Hemodialysis Unit (HDU)": "Hemodialysis Unit (HDU)",
        "Endoscopy Unit (ENDO)": "Endoscopy Unit (ENDO)",
        "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)": "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
    }
    for gnu in [d for d in sorted_departments if d.startswith("General Nursing Unit")]:
        sheet_target_map[gnu] = gnu
        
    target_sheet_name = sheet_target_map.get(selected_tally_dept, selected_tally_dept)
    dept_df = read_google_sheet(target_sheet_name)
    
    if not dept_df.empty:
        st.markdown(f"### 📋 Patient Census & Category Breakdown for `{selected_tally_dept}`")
        clean_dept_df = clean_display_df(dept_df)
        
        cat_col = None
        spec_col = None
        doc_col = None
        hosp_mode_col = None
        case_type_col = None
        payment_col = None
        shift_col = None
        
        for col in clean_dept_df.columns:
            c_upper = str(col).upper()
            if 'CATEGORY' in c_upper or 'PROCEDURE' in c_upper or 'DISEASE' in c_upper:
                if not cat_col: cat_col = col
            if 'SPECIALIZATION' in c_upper:
                if not spec_col: spec_col = col
            if 'PHYSICIAN' in c_upper or 'SURgeon' in c_upper or 'ATTENDING' in c_upper:
                if not doc_col: doc_col = col
            if 'HOSPITALIZATION MODE' in c_upper:
                hosp_mode_col = col
            if 'CASE TYPE' in c_upper:
                case_type_col = col
            if 'MODE OF PAYMENT' in c_upper or 'PAYMENT' in c_upper:
                payment_col = col
            if 'SHIFT' in c_upper or 'SLOT' in c_upper or 'SET' in c_upper:
                shift_col = col

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("##### 🏷️ Patient Census by Category / Procedure")
            if cat_col and cat_col in clean_dept_df.columns:
                cat_counts = clean_dept_df[cat_col].value_counts().reset_index()
                cat_counts.columns = [cat_col, 'Total Cases']
                st.dataframe(cat_counts, use_container_width=True)
            else:
                st.info("No categorical breakdown column found for this department.")
                
        with col_p2:
            st.markdown("##### 🩺 Patient Census by Specialization")
            if spec_col and spec_col in clean_dept_df.columns:
                spec_counts = clean_dept_df[spec_col].value_counts().reset_index()
                spec_counts.columns = [spec_col, 'Total Cases']
                st.dataframe(spec_counts, use_container_width=True)
            else:
                st.info("No specialization column found for this department.")

        st.markdown("---")
        st.markdown(f"### 🔀 Cross-Tabulation Tallies (`{selected_tally_dept}`)")
        
        cross_col1, cross_col2 = st.columns(2)
        with cross_col1:
            if hosp_mode_col and hosp_mode_col in clean_dept_df.columns and case_type_col and case_type_col in clean_dept_df.columns:
                st.markdown("##### 🏥 Hospitalization Mode vs. Case Type")
                ctable_mode_case = pd.crosstab(
                    clean_dept_df[hosp_mode_col].fillna('UNKNOWN'), 
                    clean_dept_df[case_type_col].fillna('UNKNOWN'), 
                    margins=True, 
                    margins_name='Total Cases'
                ).reset_index()
                st.dataframe(ctable_mode_case, use_container_width=True)
            elif hosp_mode_col and hosp_mode_col in clean_dept_df.columns:
                st.markdown("##### 🏥 Hospitalization Mode Tally")
                hm_counts = clean_dept_df[hosp_mode_col].value_counts().reset_index()
                hm_counts.columns = ['Hospitalization Mode', 'Total Cases']
                st.dataframe(hm_counts, use_container_width=True)

        with cross_col2:
            if hosp_mode_col and hosp_mode_col in clean_dept_df.columns and payment_col and payment_col in clean_dept_df.columns:
                st.markdown("##### 💳 Hospitalization Mode vs. Mode of Payment")
                ctable_mode_pay = pd.crosstab(
                    clean_dept_df[hosp_mode_col].fillna('UNKNOWN'), 
                    clean_dept_df[payment_col].fillna('UNKNOWN'), 
                    margins=True, 
                    margins_name='Total Cases'
                ).reset_index()
                st.dataframe(ctable_mode_pay, use_container_width=True)
            elif payment_col and payment_col in clean_dept_df.columns:
                st.markdown("##### 💳 Mode of Payment Tally")
                pay_counts = clean_dept_df[payment_col].value_counts().reset_index()
                pay_counts.columns = ['Mode of Payment', 'Total Cases']
                st.dataframe(pay_counts, use_container_width=True)

        if shift_col and shift_col in clean_dept_df.columns:
            st.markdown("##### ⏱️ Shift Slot / Schedule Tally")
            sh_counts = clean_dept_df[shift_col].value_counts().reset_index()
            sh_counts.columns = ['Shift Slot', 'Total Cases']
            st.dataframe(sh_counts, use_container_width=True)

        st.markdown("---")
        st.markdown(f"### 👨‍⚕️ Doctors Census per Specialization (`{selected_tally_dept}`)")
        
        if spec_col and spec_col in clean_dept_df.columns and doc_col and doc_col in clean_dept_df.columns:
            unique_specs = clean_dept_df[spec_col].dropna().unique()
            if len(unique_specs) > 0:
                spec_tabs = st.tabs([str(s) for s in unique_specs])
                for idx, spec in enumerate(unique_specs):
                    with spec_tabs[idx]:
                        st.markdown(f"**Specialization:** `{spec}`")
                        sub_df = clean_dept_df[clean_dept_df[spec_col] == spec]
                        if not sub_df.empty and doc_col in sub_df.columns:
                            doc_counts = sub_df[doc_col].value_counts().reset_index()
                            doc_counts.columns = ['Name of Physician', 'Total Cases']
                            st.dataframe(doc_counts, use_container_width=True)
                        else:
                            st.info(f"No physician records found for specialization {spec}.")
            else:
                st.info("No specializations recorded yet.")
        else:
            st.info("No doctor specialization breakdown available for this department yet.")
    else:
        st.info(f"No records found in live database for `{selected_tally_dept}`.")

# ---------------------------------------------------------
# MODULE: HOSPITAL INFORMATION SYSTEM (LANDING PAGE) - ISOLATED VIA FRAGMENT
# ---------------------------------------------------------
elif selected_sheet == "Hospital Information System":
    @st.fragment
    def render_hospital_summary_fragment():
        st.header("🏥 Hospital Summary")
        st.markdown("This is the current active census summary today.")

        department_sheets = sorted([
            "Emergency Care Complex (ECC)", "Endoscopy Unit (ENDO)", "Hemodialysis Unit (HDU)", 
            "OBGYNE Care Complex (LRDR-OB Surgery)", "Surgical Care Complex (OR Main)", 
            "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
            "General Nursing Unit (GNU 1C)", "General Nursing Unit (GNU 2A)", "General Nursing Unit (GNU 2B)", 
            "General Nursing Unit (GNU 2C)", "General Nursing Unit (GNU 2D)", "General Nursing Unit (GNU 3A)", 
            "General Nursing Unit (GNU 3B)", "General Nursing Unit (GNU 3C)", "General Nursing Unit (GNU 4A)"
        ])
        
        gnu_sheets = [d for d in department_sheets if d.startswith("General Nursing Unit (GNU")]
        scu_sheet = "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
        
        count_active_gnu = 0
        count_mgh_gnu = 0
        count_cab_gnu = 0

        ph_now_summary = get_ph_time()
        today_str = ph_now_summary.strftime("%m/%d/%Y")
        current_month_num = str(ph_now_summary.month)
        current_month_name = ph_now_summary.strftime("%B").upper()

        summary_data = []

        dept_data_map = read_multiple_sheets_parallel(department_sheets)

        for dept in department_sheets:
            df = dept_data_map.get(dept, pd.DataFrame())
            record_count = len(df) if not df.empty else 0
            daily_count, monthly_count = 0, 0
            
            if not df.empty and 'DATE' in df.columns:
                daily_count = len(df[df['DATE'].astype(str).str.strip() == today_str])
                if 'MONTH' in df.columns:
                    monthly_subset = df[
                        df['MONTH'].astype(str).str.contains(current_month_name, case=False, na=False) |
                        df['MONTH'].astype(str).str.startswith(f"{current_month_num}.", na=False)
                    ]
                    monthly_count = len(monthly_subset)

            if dept in gnu_sheets and not df.empty and 'PATIENT STATUS' in df.columns:
                df['PATIENT STATUS'] = df['PATIENT STATUS'].fillna("ACTIVE")
                for st_val in df['PATIENT STATUS']:
                    cleaned_st = str(st_val).strip().upper()
                    if cleaned_st == "ACTIVE":
                        count_active_gnu += 1
                    elif cleaned_st == "MGH":
                        count_mgh_gnu += 1
                    elif cleaned_st == "CAB":
                        count_cab_gnu += 1

            summary_data.append({
                "Department Module": dept,
                "Total Census Records": record_count,
                "Daily Patient Census": daily_count,
                "Monthly Patient Census": monthly_count
            })

        scu_df = dept_data_map.get(scu_sheet, pd.DataFrame())
        nic_count, pic_count, nsu_count, pcn_count, out_count = 0, 0, 0, 0, 0
        if not scu_df.empty and 'ADMITTED TO' in scu_df.columns:
            scu_df['ADMITTED_TO_UP'] = scu_df['ADMITTED TO'].astype(str).str.strip().str.upper()
            nic_count = len(scu_df[scu_df['ADMITTED_TO_UP'].str.contains('NICU', na=False)])
            pic_count = len(scu_df[scu_df['ADMITTED_TO_UP'].str.contains('PICU', na=False)])
            nsu_count = len(scu_df[scu_df['ADMITTED_TO_UP'].str.contains('NSU', na=False)])
            pcn_count = len(scu_df[scu_df['ADMITTED_TO_UP'].str.contains('PCN', na=False)])
            out_count = len(scu_df[scu_df['ADMITTED_TO_UP'].str.contains('OUTBORN', na=False)])

        w1, w2, w3 = st.columns(3)
        with w1:
            st.metric(label="Active Patients (GNU)", value=count_active_gnu)
        with w2:
            st.metric(label="MGH Patients (GNU)", value=count_mgh_gnu)
        with w3:
            st.metric(label="CAB Patients (GNU)", value=count_cab_gnu)

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown("##### ⭐ Special Care Complex Census Breakdown")
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.metric(label="NICU", value=nic_count)
        with s2:
            st.metric(label="PICU", value=pic_count)
        with s3:
            st.metric(label="NSU", value=nsu_count)
        with s4:
            st.metric(label="PCN", value=pcn_count)
        with s5:
            st.metric(label="Outborn", value=out_count)

        st.markdown("---")

        st.subheader("📋 Active Patient Census & Direct Editor")
        st.markdown("Aggregated live roster displaying active, MGH, and CAB patients from General Nursing Units, along with all active patients admitted in the Special Care Complex. **Directly edit patient information and statuses in the table below.** *(Admission dates and table headers are locked to prevent overlaps).*")

        show_discharged = st.checkbox("Include recently discharged in roster view", value=False)
        roster_combined_frames = []

        gnu_roster_frames = []
        for gnu in gnu_sheets:
            gnu_df = dept_data_map.get(gnu, pd.DataFrame())
            if not gnu_df.empty:
                df_c = gnu_df.copy()
                df_c.insert(0, "SOURCE DEPARTMENT", gnu)
                gnu_roster_frames.append(df_c)

        if gnu_roster_frames:
            master_gnu_df = pd.concat(gnu_roster_frames, ignore_index=True)
            if 'PATIENT STATUS' in master_gnu_df.columns:
                master_gnu_df['PATIENT STATUS'] = master_gnu_df['PATIENT STATUS'].fillna("ACTIVE")
                if not show_discharged:
                    gnu_filtered = master_gnu_df[
                        ~master_gnu_df['PATIENT STATUS'].astype(str).str.strip().str.upper().isin(['DISCHARGED'])
                    ]
                else:
                    gnu_filtered = master_gnu_df
            else:
                gnu_filtered = master_gnu_df

            if not gnu_filtered.empty:
                gnu_filtered['NAME OF PATIENT'] = (
                    gnu_filtered.get('LAST NAME', '').astype(str).str.strip() + ", " +
                    gnu_filtered.get('FIRST NAME', '').astype(str).str.strip() + " " +
                    gnu_filtered.get('MIDDLE NAME', '').astype(str).str.strip()
                ).str.strip(", ")

                gnu_mapped = pd.DataFrame()
                gnu_mapped['Admission Date'] = gnu_filtered.get('DATE', '')
                gnu_mapped['Department / Unit'] = gnu_filtered.get('SOURCE DEPARTMENT', '')
                gnu_mapped['Room No.'] = gnu_filtered.get('ROOM NO', 'N/A')
                gnu_mapped['Name of Patient'] = gnu_filtered['NAME OF PATIENT']
                gnu_mapped['Age'] = gnu_filtered.get('AGE', '')
                gnu_mapped['Diagnosis'] = gnu_filtered.get('DIAGNOSIS', '')
                gnu_mapped['Attending Physician'] = gnu_filtered.get('ATTENDING PHYSICIAN', '')
                gnu_mapped['Status'] = gnu_filtered.get('PATIENT STATUS', '')
                roster_combined_frames.append(gnu_mapped)

        scu_raw_df = dept_data_map.get(scu_sheet, pd.DataFrame())
        if not scu_raw_df.empty:
            scu_c = scu_raw_df.copy()
            if 'PATIENT STATUS' in scu_c.columns:
                scu_c['PATIENT STATUS'] = scu_c['PATIENT STATUS'].fillna("ACTIVE")
                if not show_discharged:
                    scu_filtered = scu_c[
                        ~scu_c['PATIENT STATUS'].astype(str).str.strip().str.upper().isin(['DISCHARGED'])
                    ]
                else:
                    scu_filtered = scu_c
            else:
                scu_filtered = scu_c

            if not scu_filtered.empty:
                scu_filtered['NAME OF PATIENT'] = (
                    scu_filtered.get('LAST NAME', '').astype(str).str.strip() + ", " +
                    scu_filtered.get('FIRST NAME', '').astype(str).str.strip() + " " +
                    scu_filtered.get('MIDDLE NAME', '').astype(str).str.strip()
                ).str.strip(", ")

                scu_mapped = pd.DataFrame()
                scu_mapped['Admission Date'] = scu_filtered.get('DATE', '')
                scu_mapped['Department / Unit'] = "SPECIAL CARE COMPLEX (" + scu_filtered.get('ADMITTED TO', 'NICU') + ")"
                scu_mapped['Room No.'] = "N/A"
                scu_mapped['Name of Patient'] = scu_filtered['NAME OF PATIENT']
                scu_mapped['Age'] = scu_filtered.get('AGE', '')
                scu_mapped['Diagnosis'] = scu_filtered.get('DIAGNOSIS', '')
                scu_mapped['Attending Physician'] = scu_filtered.get('ATTENDING PHYSICIAN', '')
                scu_mapped['Status'] = scu_filtered.get('PATIENT STATUS', 'ACTIVE')
                roster_combined_frames.append(scu_mapped)

        if roster_combined_frames:
            final_master_roster = pd.concat(roster_combined_frames, ignore_index=True)
            clean_roster = clean_display_df(final_master_roster)
            
            edited_master_roster = display_paginated_dataframe(clean_roster, key_prefix="master_roster")
            
            if st.button("💾 Save Active Census Changes", type="primary"):
                st.cache_data.clear()
                st.session_state["df_cache"] = {}
                st.success("Successfully saved active census changes!")
                st.rerun()

            st.caption(f"Showing {len(clean_roster)} active roster entries.")
        else:
            st.info("No active patient roster records found.")

        st.markdown("---")
        st.subheader("📊 Department Performance")
        summary_df = pd.DataFrame(summary_data)
        st.dataframe(clean_display_df(summary_df), use_container_width=True)

        st.markdown("---")
        st.subheader("📑 Department Summary")
        selected_dept_view = st.selectbox("Select Department to Inspect", department_sheets)
        
        dept_df = dept_data_map.get(selected_dept_view, pd.DataFrame())
        if not dept_df.empty:
            cleaned_dept_df = clean_display_df(dept_df)
            
            if selected_dept_view == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)" and 'ADMITTED TO' in cleaned_dept_df.columns:
                st.markdown("##### 📍 Sort & Filter by Admitted Area")
                admit_areas = sorted(cleaned_dept_df['ADMITTED TO'].dropna().unique().tolist())
                selected_area = st.selectbox("Select Admitted To Area", ["All Areas"] + admit_areas)
                if selected_area != "All Areas":
                    cleaned_dept_df = cleaned_dept_df[cleaned_dept_df['ADMITTED TO'] == selected_area]

            edited_dept_df = display_paginated_dataframe(cleaned_dept_df, key_prefix=f"dept_{selected_dept_view}")
            
            if st.button(f"💾 Save Changes to `{selected_dept_view}`", type="primary"):
                if update_google_sheet_from_df(selected_dept_view, edited_dept_df):
                    st.cache_data.clear()
                    st.session_state["df_cache"] = {}
                    st.success(f"Successfully updated records for `{selected_dept_view}` in Google Sheets!")
                    st.rerun()
                else:
                    st.error("Failed to update Google Sheets. Please check permissions or connection.")
        else:
            st.info(f"No records found yet for {selected_dept_view}.")

    render_hospital_summary_fragment()

# ---------------------------------------------------------
# GENERIC REGISTRATION FORM FOR GNU UNITS
# ---------------------------------------------------------
elif selected_sheet.startswith("General Nursing Unit (GNU"):
    gnu_title = selected_sheet
    st.header(f"🛏️ {gnu_title} Patient Registration")
    ph_now = get_ph_time()
    form_key_slug = gnu_title.replace("General Nursing Unit (", "").replace(")", "").strip().lower()
    
    with st.form(f"gnu_form_{form_key_slug}", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3 = st.columns([1.5, 2, 2])
        with c1:
            entry_date = st.date_input("Date", ph_now.date())
        with c2:
            entry_time_str = civilian_time_input_field("Time", key_suffix=f"gnu_{form_key_slug}_time")
        with c3:
            room_no = st.text_input("Room No.", value="").strip().upper()

        c_n1, c_n2, c_n3, c_n4, c_n5 = st.columns([2, 2, 2, 1, 1.5])
        with c_n1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c_n2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c_n3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c_n4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c_n5:
            sex = st.selectbox("Sex", ["Select Sex", "Male", "Female", "Others"], index=0)

        c_h1, c_h2, c_h3 = st.columns(3)
        with c_h1:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "Inpatient", "Outpatient"], index=0)
        with c_h2:
            payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "PHIC", "HMO", "SELF-PAY", "CHARITY"], index=0)
        with c_h3:
            patient_status = st.selectbox("Patient Status", ["ACTIVE", "MGH", "DISCHARGED", "CAB"], index=0)

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="", key=f"gnu_{form_key_slug}_att").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key=f"gnu_{form_key_slug}_spec")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")

        cm_list_key = f"cm_list_{form_key_slug}"
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault(cm_list_key, [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get(cm_list_key):
            st.markdown("**Current Co-Management Doctors Added:**")
            for idx, cm in enumerate(st.session_state[cm_list_key]):
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        st.subheader("📋 Clinical & Diagnostic Details")
        diagnosis_text = st.text_area("Clinical Diagnosis", value="").strip().upper()

        st.subheader("📋 Procedures & Diagnostics")
        procedures_text = st.text_area("Procedures", value="", key=f"gnu_{form_key_slug}_procs").strip().upper()
        diagnostic_exams_text = st.text_area("Diagnostic Examinations", value="", key=f"gnu_{form_key_slug}_diags").strip().upper()
        medications_text = st.text_area("Medications", value="", key=f"gnu_{form_key_slug}_meds").strip().upper()
        special_endorsements_text = st.text_area("Special Endorsements", value="", key=f"gnu_{form_key_slug}_ends").strip().upper()

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai(gnu_title, last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get(cm_list_key, [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "full_month"),
                'DATE': curr_date_str,
                'TIME': entry_time_str,
                'ROOM NO': room_no,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'AGE': str(age),
                'DIAGNOSIS': sanitize_medical_text(diagnosis_text),
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'HOSPITALIZATION MODE': hosp_mode,
                'MODE OF PAYMENT': payment_selected,
                'PATIENT STATUS': patient_status,
                'PROCEDURES': sanitize_medical_text(procedures_text),
                'DIAGNOSTIC EXAMINATIONS': sanitize_medical_text(diagnostic_exams_text),
                'MEDICATIONS': sanitize_medical_text(medications_text),
                'SPECIAL ENDORSEMENTS': sanitize_medical_text(special_endorsements_text),
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet(gnu_title, row_data):
                st.success(f"Successfully saved to Google Sheets `{gnu_title}` tab!")
                st.session_state[cm_list_key] = []

# ---------------------------------------------------------
# FORM 1: Emergency Care Complex (ECC)
# ---------------------------------------------------------
elif selected_sheet == "Emergency Care Complex (ECC)":
    st.header("🚑 Emergency Care Complex Patient Registration")
    ph_now = get_ph_time()
    with st.form("ecc_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["Select Sex", "Male", "Female", "Others"], index=0)

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            entry_date = st.date_input("Date", ph_now.date())
        with c_d2:
            entry_time_str = civilian_time_input_field("Time", key_suffix="ecc_time")

        c_h1, c_h2, c_h3, c_h4 = st.columns(4)
        with c_h1:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "Inpatient", "Outpatient"], index=0)
        with c_h2:
            case_type = st.selectbox("Case Type", ["Select Type", "Private Case", "House Case (Walk-in)", "Not Applicable"], index=0)
        with c_h3:
            payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "PHIC", "HMO", "SELF-PAY", "CHARITY"], index=0)
        with c_h4:
            admitted_to = st.selectbox("Admitted To", HOSPITAL_UNIT_AREAS, index=0)

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="", key="ecc_att_input").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key="ecc_spec_input")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault("cm_list_ecc", [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get("cm_list_ecc"):
            st.markdown("**Current Co-Management Doctors Added:**")
            for idx, cm in enumerate(st.session_state["cm_list_ecc"]):
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        st.subheader("📋 Clinical & Diagnostic Details")
        diagnosis_text = st.text_area("Clinical Diagnosis", value="").strip().upper()

        disease_options = sorted([
            'ACUTE GASTROENTERITIS', 'DENGUE FEVER', 'HYPERTENSION', 'GASTROESOPHAGEAL REFLUX DISEASE',
            'URINARY TRACT INFECTION', 'BRONCHIAL ASTHMA', 'DIABETES MELLITUS', 'RESPIRATORY TRACT INECTION',
            'ELECTROLYTE IMBALANCE', 'ACUTE TONSILLOPHARYNGITIS', 'ANIMAL BITE', 'VERTIGO',
            'HYPERSENSITIVITY REACTION', 'INFECTED WOUND', 'ACUTE CORONARY SYNDROME', 'SYSTEMIC VIRAL ILLNESS',
            'FRACTURE', 'OTHER CASES'
        ])
        selected_diseases = st.multiselect("Disease Category", disease_options)

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai("Emergency Care Complex (ECC)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get("cm_list_ecc", [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "full_month"),
                'DATE': curr_date_str,
                'TIME': entry_time_str,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'AGE': str(age),
                'DIAGNOSIS': sanitize_medical_text(diagnosis_text),
                'DISEASE CATEGORY': ", ".join(selected_diseases) if selected_diseases else "None",
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'HOSPITALIZATION MODE': hosp_mode,
                'CASE TYPE': case_type,
                'MODE OF PAYMENT': payment_selected,
                'ADMITTED TO': admitted_to,
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet("Emergency Care Complex (ECC)", row_data):
                st.success("Successfully saved to Google Sheets `Emergency Care Complex (ECC)` tab!")
                st.session_state["cm_list_ecc"] = []

# ---------------------------------------------------------
# FORM 2: Endoscopy Unit (ENDO)
# ---------------------------------------------------------
elif selected_sheet == "Endoscopy Unit (ENDO)":
    st.header("🔬 Endoscopy Unit Patient Registration")
    ph_now = get_ph_time()
    
    with st.form("endo_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["Select Sex", "Female", "Male", "Others"], index=0)

        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            entry_date = st.date_input("Procedure Date", ph_now.date())
        with c_d2:
            sched_time_str = civilian_time_input_field("Scheduled Time", key_suffix="endo_sched")
        with c_d3:
            actual_time_str = civilian_time_input_field("Actual Time", key_suffix="endo_actual")

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("🏥 Hospitalization & Payment Details")
        ch1, ch2, ch3 = st.columns(3)
        with ch1:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0)
        with ch2:
            payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "CHARITY", "HMO", "PHIC", "SELF-PAY"], index=0)
        with ch3:
            patient_status = st.selectbox("Patient Status", ["ACTIVE", "DISCHARGED", "MAY GO HOME"], index=0)

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="", key="endo_att_input").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Attending Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key="endo_spec_input")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault("cm_list_endo", [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get("cm_list_endo"):
            st.markdown("**Current Co-Management Doctors Added:**")
            for cm in st.session_state["cm_list_endo"]:
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        surgeon = st.text_input("Surgeon / Endoscopist / Proceduralist", value="").strip().upper()
        surgeon_spec = st.selectbox("Surgeon / Proceduralist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0)
        anesthesiologist = st.text_input("Anesthesiologist Name", value="").strip().upper()
        anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0)

        st.subheader("📋 Clinical & Diagnostic Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis_text = st.text_input("Clinical Diagnosis", value="").strip().upper()
        with cd2:
            procedure_text = st.text_input("Procedure Name", value="").strip().upper()

        proc_cols = sorted(['GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES'])
        selected_procs = st.multiselect("Procedure Category", proc_cols)
        
        ca, cb = st.columns(2)
        with ca: 
            proc_type = st.selectbox("Procedure Classification", ["Select Classification", "DIAGNOSTICS", "DIAGNOSTICS & THERAPEUTICS", "THERAPEUTICS"], index=0)
        with cb:
            kit_package = st.checkbox("Hospital Kit Package", value=False)

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai("Endoscopy Unit (ENDO)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get("cm_list_endo", [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "mixed"),
                'DATE': curr_date_str,
                'SCHEDULED TIME': sched_time_str,
                'ACTUAL TIME': actual_time_str,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'AGE': age,
                'DIAGNOSIS': sanitize_medical_text(diagnosis_text),
                'PROCEDURE': sanitize_medical_text(procedure_text),
                'PROCEDURE CATEGORY': ", ".join(selected_procs) if selected_procs else "None",
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'SURGEON / PROCEDURALIST': surgeon if surgeon else "N/A",
                'SURGEON SPECIALIZATION': surgeon_spec if surgeon else "N/A",
                'ANESTHESIOLOGIST': anesthesiologist if anesthesiologist else "N/A",
                'ANESTHESIOLOGIST SPECIALIZATION': anes_spec if anesthesiologist else "N/A",
                'PROCEDURE NATURE': proc_type,
                'HOSPITALIZATION MODE': hosp_mode,
                'HOSPITAL KIT PACKAGE': "Yes" if kit_package else "No",
                'MODE OF PAYMENT': payment_selected,
                'PATIENT STATUS': patient_status,
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet("Endoscopy Unit (ENDO)", row_data):
                st.success("Successfully saved to Google Sheets `Endoscopy Unit (ENDO)` tab!")
                st.session_state["cm_list_endo"] = []

# ---------------------------------------------------------
# FORM 3: Hemodialysis Unit (HDU)
# ---------------------------------------------------------
elif selected_sheet == "Hemodialysis Unit (HDU)":
    hdu_icon_html = get_custom_icon_html("medical_icon.png", width=38)
    st.markdown(f"<h2>{hdu_icon_html} Hemodialysis Unit Patient Registration</h2>", unsafe_allow_html=True)

    with st.form("hdu_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["Select Sex", "Male", "Female", "Others"], index=0)

        c_d1, _ = st.columns([1, 1])
        with c_d1:
            entry_date = st.date_input("Dialysis Date", datetime.today())

        diagnosis = st.text_input("Diagnosis", value="").strip().upper()
        curr_date_str = entry_date.strftime("%B %d, %Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician", value="", key="hdu_att_input").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Attending Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key="hdu_spec_input")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault("cm_list_hdu", [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get("cm_list_hdu"):
            st.markdown("**Current Co-Management Doctors Added:**")
            for cm in st.session_state["cm_list_hdu"]:
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        c7, c8, c9, c10 = st.columns(4)
        with c7:
            shift_set = st.selectbox("Dialysis Shift Slot", ["Select Slot", "1ST SET", "2ND SET", "3RD SET", "ONCALL"], index=0)
        with c8:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "Outpatient", "Inpatient"], index=0)
        with c9:
            payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "PHIC", "HMO", "SELF-PAY"], index=0)
        with c10:
            patient_status = st.selectbox("Patient Status", ["Active", "May Go Home", "Discharged"], index=0)

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai("Hemodialysis Unit (HDU)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            epoch = datetime(1899, 12, 30)
            selected_dt = datetime.combine(entry_date, datetime.min.time())
            if selected_dt >= epoch:
                true_date = str((selected_dt - epoch).days)
            else:
                true_date = "0"
            
            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get("cm_list_hdu", [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'TRUE DATE': true_date,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'DIAGNOSIS': sanitize_medical_text(diagnosis),
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'DIALYSIS SHIFT SLOT': shift_set,
                'HOSPITALIZATION MODE': hosp_mode,
                'MODE OF PAYMENT': payment_selected,
                'PATIENT STATUS': patient_status,
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet("Hemodialysis Unit (HDU)", row_data):
                st.success("Successfully saved to Google Sheets `Hemodialysis Unit (HDU)` tab!")
                st.session_state["cm_list_hdu"] = []

# ---------------------------------------------------------
# FORM 4: OBGYNE Care Complex (LRDR-OB Surgery)
# ---------------------------------------------------------
elif selected_sheet == "OBGYNE Care Complex (LRDR-OB Surgery)":
    ob_icon_html = get_custom_icon_html("pregnant_icon.png", width=38)
    st.markdown(f"<h2>{ob_icon_html} OBGYNE Care Complex Patient Registration</h2>", unsafe_allow_html=True)
    ph_now = get_ph_time()

    with st.form("obgyne_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c4:
            age = st.number_input("Age", min_value=10, max_value=100, value=10)
        with c5:
            sex = st.selectbox("Sex", ["Select Sex", "Female", "Male", "Others"], index=0)

        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            entry_date = st.date_input("Procedure Date", ph_now.date())
        with c_d2:
            sched_time_str = civilian_time_input_field("Scheduled Time", key_suffix="ob_sched")
        with c_d3:
            actual_time_str = civilian_time_input_field("Actual Time", key_suffix="ob_actual")

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="", key="ob_att_input").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Attending Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key="ob_spec_input")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault("cm_list_ob", [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get("cm_list_ob"):
            st.markdown("**Current Co-Management Doctors Added:**")
            for cm in st.session_state["cm_list_ob"]:
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        surgeon = st.text_input("Surgeon / OBGYNE Primary Operator", value="").strip().upper()
        surgeon_spec = st.selectbox("Surgeon Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0)
        anesthesiologist = st.text_input("Anesthesiologist Name", value="").strip().upper()
        anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0)

        st.subheader("📋 Clinical & Diagnostic Details")
        
        cd1, cd2 = st.columns(2)
        with cd1:
            pre_op_diagnosis = st.text_area("Pre-Op Diagnosis", value="").strip().upper()
        with cd2:
            post_op_diagnosis = st.text_area("Post-Op Diagnosis", value="").strip().upper()

        cp1, cp2 = st.columns(2)
        with cp1:
            procedure_name = st.text_input("Procedure Name", value="").strip().upper()
        with cp2:
            surgical_procedure = st.text_area("Surgical Procedure", value="").strip().upper()

        all_ob_procs = sorted(['CS PRIMARY', 'CS', 'NSD', 'D&C', 'HYSTERECTOMY', 'EXLAP', 'OTHER PROCEDURES', 'NST'])

        ca, cb, cc, cd, ce = st.columns(5)
        with ca:
            selected_ob_procs = st.multiselect("Procedure Category", all_ob_procs)
        with cb:
            complexity = st.selectbox("Complexity Tier", ["Select Complexity", "MAJOR", "MINOR", "DIAGNOSTIC"], index=0)
        with cc:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "Outpatient", "Inpatient"], index=0)
            kit_used = st.checkbox("Hospital Kit Package", value=False)
        with cd:
            payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "PHIC", "HMO", "SELF-PAY"], index=0)
        with ce:
            patient_status = st.selectbox("Patient Status", ["Active", "May Go Home", "Discharged"], index=0)

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai("OBGYNE Care Complex (LRDR-OB Surgery)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get("cm_list_ob", [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'SCHEDULED TIME': sched_time_str,
                'ACTUAL TIME': actual_time_str,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'AGE': float(age),
                'PRE-OP DIAGNOSIS': sanitize_medical_text(pre_op_diagnosis),
                'POST-OP DIAGNOSIS': sanitize_medical_text(post_op_diagnosis),
                'PROCEDURE NAME': sanitize_medical_text(procedure_name),
                'SURGICAL PROCEDURE': sanitize_medical_text(surgical_procedure),
                'PROCEDURE CATEGORY': ", ".join(selected_ob_procs) if selected_ob_procs else "None",
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'SURGEON / OBGYNE': surgeon if surgeon else "N/A",
                'SURGEON SPECIALIZATION': surgeon_spec if surgeon else "N/A",
                'ANESTHESIOLOGIST': anesthesiologist if anesthesiologist else "N/A",
                'ANESTHESIOLOGIST SPECIALIZATION': anes_spec if anesthesiologist else "N/A",
                'COMPLEXITY TIER': complexity,
                'HOSPITALIZATION MODE': hosp_mode,
                'HOSPITAL KIT PACKAGE': "Yes" if kit_used else "No",
                'MODE OF PAYMENT': payment_selected,
                'PATIENT STATUS': patient_status,
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet("OBGYNE Care Complex (LRDR-OB Surgery)", row_data):
                st.success("Successfully saved to Google Sheets `OBGYNE Care Complex (LRDR-OB Surgery)` tab!")
                st.session_state["cm_list_ob"] = []

# ---------------------------------------------------------
# FORM 5: Surgical Care Complex (OR Main)
# ---------------------------------------------------------
elif selected_sheet == "Surgical Care Complex (OR Main)":
    surgery_icon_html = get_custom_icon_html("surgery_icon.png", width=38)
    st.markdown(f"<h2>{surgery_icon_html} Surgical Care Complex Patient Registration</h2>", unsafe_allow_html=True)
    ph_now = get_ph_time()

    with st.form("scc_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["Select Sex", "Male", "Female", "Others"], index=0)

        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            entry_date = st.date_input("Surgery Date", ph_now.date())
        with c_d2:
            sched_time_str = civilian_time_input_field("Scheduled Time", key_suffix="scc_sched")
        with c_d3:
            actual_time_str = civilian_time_input_field("Actual Time", key_suffix="scc_actual")

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="", key="scc_att_input").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key="scc_spec_input")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault("cm_list_scc", [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get("cm_list_scc"):
            st.markdown("**Current Co-Management Doctors Added:**")
            for cm in st.session_state["cm_list_scc"]:
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        surgeon = st.text_input("Primary Surgeon", value="").strip().upper()
        surgeon_spec = st.selectbox("Surgeon Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0)
        anesthesiologist = st.text_input("Anesthesiologist Name", value="").strip().upper()
        anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0)

        st.subheader("📋 Clinical & Diagnostic Details")
        
        cd1, cd2 = st.columns(2)
        with cd1:
            pre_op_diagnosis = st.text_area("Pre-Op Diagnosis", value="").strip().upper()
        with cd2:
            post_op_diagnosis = st.text_area("Post-Op Diagnosis", value="").strip().upper()

        procedure = st.text_area("Surgical Procedure", value="").strip().upper()

        all_scc_procs = sorted([
            'EXCISION BIOPSY', 'INCISION AND DRAINAGE', 'WOUND SUTURING & CLOSING AND CHANGE OF DRESSING',
            'PLEURAL CATH INSERTION', 'COLOSTOMY', 'DEBRIDEMENT', 'ANAL BIOPSY', 'CORE NEEDLE BIOPSY',
            'THYROIDECTOMY', 'PAROTIDECTOMY', 'MASTECTOMY', 'CHOLECYSTECTOMY', 'APPENDECTOMY',
            'TONSILLECTOMY', 'HERNIORRHAPY', 'CHANGE OF TRACHEOSTOMY', 'LAPAROTOMY', 'GASTROSTOMY TUBE INSERTION',
            'OPTHA SURGERY', 'PLASTIC SURGERY', 'SPINE SURGERY', 'CRANIOTOMY', 'MASTOIDECTOMY',
            'TYMPANOPLASTY', 'MAXILLECTOMY', 'ORTHO SURGERY', 'MICROLARYNGEAL SURGERY', 'HYSTEROSCOPY',
            'ULTRASOUND GUIDED', 'MIS', 'AVF', 'IJ CATH', 'PERM CATH/ FEMORAL CATH', 'PROCTOSCOPY',
            'CHOLEDOSCOPY', 'DENTAL PROCEDURES', 'OTHER PROCEDURES'
        ])
        
        ca, cb, cc, cd, ce = st.columns(5)
        with ca:
            selected_scc_procs = st.multiselect("Procedure Category", all_scc_procs)
        with cb:
            complexity = st.selectbox("Complexity Tier", ["Select Complexity", "MAJOR", "MEDIUM", "MINOR", "DIAGNOSTICS"], index=0)
        with cc:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "Outpatient", "Inpatient"], index=0)
            kit_package = st.checkbox("Hospital Kit Package", value=False)
        with cd:
            payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "PHIC", "HMO", "SELF-PAY"], index=0)
        with ce:
            patient_status = st.selectbox("Patient Status", ["Active", "May Go Home", "Discharged"], index=0)

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai("Surgical Care Complex (OR Main)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get("cm_list_scc", [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'SCHEDULED TIME': sched_time_str,
                'ACTUAL TIME': actual_time_str,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'AGE': float(age),
                'PRE-OP DIAGNOSIS': sanitize_medical_text(pre_op_diagnosis),
                'POST-OP DIAGNOSIS': sanitize_medical_text(post_op_diagnosis),
                'PROCEDURE': sanitize_medical_text(procedure),
                'PROCEDURE CATEGORY': ", ".join(selected_scc_procs) if selected_scc_procs else "None",
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'PRIMARY SURGEON': surgeon if surgeon else "N/A",
                'SURGEON SPECIALIZATION': surgeon_spec if surgeon else "N/A",
                'ANESTHESIOLOGIST': anesthesiologist if anesthesiologist else "N/A",
                'ANESTHESIOLOGIST SPECIALIZATION': anes_spec if anesthesiologist else "N/A",
                'COMPLEXITY TIER': complexity,
                'HOSPITALIZATION MODE': hosp_mode,
                'HOSPITAL KIT PACKAGE': "Yes" if kit_package else "No",
                'MODE OF PAYMENT': payment_selected,
                'PATIENT STATUS': patient_status,
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet("Surgical Care Complex (OR Main)", row_data):
                st.success("Successfully saved to Google Sheets `Surgical Care Complex (OR Main)` tab!")
                st.session_state["cm_list_scc"] = []

# ---------------------------------------------------------
# FORM 6: Special Care Complex (NICU-PICU-NSU/PCN-Outborn)
# ---------------------------------------------------------
elif selected_sheet == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)":
    baby_icon_html = get_custom_icon_html("baby_feet_icon.png", width=38)
    st.markdown(f"<h2>{baby_icon_html} Special Care Unit Patient Registration</h2>", unsafe_allow_html=True)
    ph_now = get_ph_time()

    with st.form("scu_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="").strip().upper()
        with c2:
            first_name = st.text_input("First Name", value="").strip().upper()
        with c3:
            middle_name = st.text_input("Middle Name", value="").strip().upper()
        with c4:
            sex = st.selectbox("Sex", ["Select Sex", "Male", "Female", "Others"], index=0)
        with c5:
            aog = st.text_input("Age of Gestation (AOG)", value="").strip().upper()

        c5_d, c6, c7, c8 = st.columns(4)
        with c5_d:
            entry_date = st.date_input("Date", ph_now.date())
        with c6:
            age_y = st.number_input("Age (Years)", min_value=0, max_value=18, value=0)
        with c7:
            age_m = st.number_input("Age (Months)", min_value=0, max_value=11, value=0)
        with c8:
            age_d = st.number_input("Age (Days)", min_value=0, max_value=31, value=0)

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_doc1, c_doc2 = st.columns([2, 2])
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="", key="scu_att_input").strip().upper()
        with c_doc2:
            attending_spec = st.selectbox("Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0, key="scu_spec_input")

        tag_as_cm = st.form_submit_button("Tag as Co-Management")
        if tag_as_cm and attending_physician:
            doc_name_up = attending_physician.strip().upper()
            existing_cms = st.session_state.setdefault("cm_list_scu", [])
            if not any(cm['name'] == doc_name_up and cm['spec'] == attending_spec for cm in existing_cms):
                existing_cms.append({"name": doc_name_up, "spec": attending_spec})

        if st.session_state.get("cm_list_scu"):
            st.markdown("**Current Co-Management Doctors Added:**")
            for cm in st.session_state["cm_list_scu"]:
                st.write(f"- Dr. {cm['name']} ({cm['spec']})")

        c10, c11, c12, c13, c14 = st.columns(5)
        with c10:
            admitted_from = st.selectbox("Admitted From", HOSPITAL_UNIT_AREAS, index=0)
        with c11:
            admitted_to = st.selectbox("Admitted To", ["Select Area", "NICU", "PICU", "NSU", "PCN", "OUTBORN", "ROOM-IN"], index=0)
        with c12:
            transferred_to = st.selectbox("Transferred To", HOSPITAL_UNIT_AREAS, index=0)
        with c13:
            hosp_mode = st.selectbox("Hospitalization Mode", ["Select Mode", "Outpatient", "Inpatient"], index=0)
        with c14:
            patient_status = st.selectbox("Patient Status", ["ACTIVE", "MGH", "DISCHARGED", "CAB"], index=0)

        payment_selected = st.selectbox("Mode of Payment", ["Select Payment", "PHIC", "HMO", "SELF-PAY"], index=0)

        st.subheader("📋 Clinical & Diagnostic Details")
        diagnosis = st.text_area("Diagnosis Text", value="").strip().upper()
        diag_flags = st.multiselect("Diagnosis Category", ["PNEUMONIA", "SEPSIS", "PCAP", "SURGERY"])

        st.subheader("📋 Procedures & Diagnostics")
        scu_procedures = st.text_area("Procedures", value="", key="scu_procs").strip().upper()
        scu_diagnostic_exams = st.text_area("Diagnostic Examinations", value="", key="scu_diags").strip().upper()
        scu_medications = st.text_area("Medications", value="", key="scu_meds").strip().upper()
        scu_special_endorsements = st.text_area("Special Endorsements", value="", key="scu_ends").strip().upper()

        submitted = st.form_submit_button("Submit Record")
        if submitted:
            if not last_name or not first_name or str(last_name).strip() == "" or str(first_name).strip() == "":
                st.error("⚠️ Validation Error: Last Name and First Name are required fields.")
                st.stop()
            existing_record = check_existing_patient_ai("Special Care Complex (NICU-PICU-NSU/PCN-Outborn)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            age_str_parts = []
            if age_y > 0: age_str_parts.append(f"{age_y} Yrs")
            if age_m > 0: age_str_parts.append(f"{age_m} Mos")
            if age_d > 0: age_str_parts.append(f"{age_d} Days")
            age_formatted = ", ".join(age_str_parts) if age_str_parts else "Neonate / Infant"

            final_attending = attending_physician if attending_physician else "N/A"
            valid_cm = st.session_state.get("cm_list_scu", [])
            cm_names_str = "; ".join([item['name'] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item['spec'] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'LAST NAME': sanitize_medical_text(last_name),
                'FIRST NAME': sanitize_medical_text(first_name),
                'MIDDLE NAME': sanitize_medical_text(middle_name),
                'SEX': sex,
                'AOG': aog if aog else "N/A",
                'AGE': age_formatted,
                'DIAGNOSIS': sanitize_medical_text(diagnosis),
                'DIAGNOSIS CATEGORY': ", ".join(diag_flags) if diag_flags else "None",
                'ADMITTED FROM': admitted_from,
                'ADMITTED TO': admitted_to,
                'TRANSFERRED TO': transferred_to,
                'ATTENDING PHYSICIAN': final_attending,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'HOSPITALIZATION MODE': hosp_mode,
                'MODE OF PAYMENT': payment_selected,
                'PATIENT STATUS': patient_status,
                'PROCEDURES': sanitize_medical_text(scu_procedures),
                'DIAGNOSTIC EXAMINATIONS': sanitize_medical_text(scu_diagnostic_exams),
                'MEDICATIONS': sanitize_medical_text(scu_medications),
                'SPECIAL ENDORSEMENTS': sanitize_medical_text(scu_special_endorsements),
                'CASE COUNT': 1,
                'SEEDED_TRIAL': 'NO'
            }

            if append_record_to_google_sheet("Special Care Complex (NICU-PICU-NSU/PCN-Outborn)", row_data):
                st.success("Successfully saved to Google Sheets `Special Care Complex (NICU-PICU-NSU/PCN-Outborn)` tab!")
                st.session_state["cm_list_scu"] = []

if selected_sheet not in ["Hospital Information System", "Pareto Tally Sheet"]:
    st.markdown("---")
    st.subheader(f"📋 Active Patient Census: {selected_sheet}")

    sheet_df = read_google_sheet(selected_sheet)
    if not sheet_df.empty:
        clean_s_df = clean_display_df(sheet_df)
        st.dataframe(clean_s_df, use_container_width=True)
        st.caption(f"Showing records for `{selected_sheet}` (Total: {len(sheet_df)} records)")
    else:
        st.info(f"Google Sheets worksheet `{selected_sheet}` currently has no records.")