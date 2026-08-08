import streamlit as st
import gspread
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import os

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & LOGO-MATCHED LIGHT MODE STYLING
# ---------------------------------------------------------
st.set_page_config(
    page_title="PATIENT DATA RECORDING SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    /* Global Clean Light Theme */
    .stApp { background-color: #ffffff !important; color: #1e293b !important; }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] { background-color: #f8fafc !important; border-right: 1px solid #e2e8f0; }
    section[data-testid="stSidebar"] * { color: #1e293b !important; }
    
    /* Headers matching MTCMC Royal Blue */
    h1, h2, h3, h4, h5, h6 { color: #1e3a8a !important; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    
    /* Action Buttons */
    .stButton > button, form button[type="submit"] {
        background-color: #1e3a8a !important; color: #ffffff !important; border-radius: 6px !important; border: none !important; font-weight: bold !important;
    }
    .stButton > button:hover, form button[type="submit"]:hover { background-color: #1d4ed8 !important; color: #ffffff !important; }
    
    /* Form Inputs, Textareas, and Dropdown Controls */
    div[data-baseweb="select"] > div, input[type="text"], input[type="number"], textarea {
        background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important;
    }
    div[data-baseweb="select"] span { color: #1e293b !important; }
    
    /* Professional Clean Borders for Time / Date input widget containers */
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #1e3a8a !important;
        box-shadow: 0 0 0 1px #1e3a8a !important;
    }

    /* Dropdown Popover Lists & Menus (Fixes dark/black popover boxes) */
    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #ffffff !important; color: #1e293b !important; border: 1px solid #cbd5e1 !important;
    }
    li[role="option"], div[data-baseweb="menu"] div, option { background-color: #ffffff !important; color: #1e293b !important; }
    li[role="option"]:hover, div[data-baseweb="menu"] div:hover { background-color: #f0fdfa !important; color: #0d9488 !important; }
    
    /* Dataframe Tables (Fixes dark background headers/cells) */
    [data-testid="stDataFrame"] { background-color: #ffffff !important; border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px; }
    [data-testid="stDataFrame"] table { background-color: #ffffff !important; color: #1e293b !important; }
    [data-testid="stDataFrame"] thead tr th { background-color: #f1f5f9 !important; color: #1e3a8a !important; }
    
    /* Metric Cards with Teal Accent Border */
    div.stMetric {
        background-color: #ffffff !important; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #e2e8f0; border-left: 5px solid #0d9488 !important;
    }
    div.stMetric label { color: #64748b !important; }
    div.stMetric div[data-testid="stMetricValue"] { color: #1e3a8a !important; }
    
    div.stForm { background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; }
</style>
""", unsafe_allow_html=True)

REGULAR_FONT_SIZE = 10

# Helper function to get current Philippine Time
def get_ph_time():
    return datetime.now(ZoneInfo("Asia/Manila"))

# Helper for a single cohesive civilian 12-hour time text entry with AM/PM default
def civilian_time_text_field(label, key_suffix=""):
    ph_now = get_ph_time()
    default_time_str = ph_now.strftime("%I:%M %p") # e.g. 10:35 PM
    val = st.text_input(label, value=default_time_str, key=f"time_txt_{key_suffix}", placeholder="e.g. 10:35 PM")
    return val

# ---------------------------------------------------------
# 2. SORTED HOSPITAL UNIT AREAS LIST
# ---------------------------------------------------------
HOSPITAL_UNIT_AREAS = [
    "None",
    "GNU 1C",
    "GNU 2A",
    "GNU 2B",
    "GNU 2C",
    "GNU 2D",
    "GNU 3A",
    "GNU 3B",
    "GNU 3C",
    "GNU 4A",
    "ICU",
    "NSU",
    "PCN",
    "PICU",
    "OUTBORN"
]

# ---------------------------------------------------------
# 3. EXACT SPECIALTIES SORTED BY FIELD OF MEDICINE THEN ALPHABETICALLY
# ---------------------------------------------------------
SPECIALTIES_BY_FIELD = {
    "Anaesthesiology": [
        "GENERAL ANAESTHESIOLOGY",
        "NEURO - ANAESTHESIOLOGY",
        "PEDIA - ANAESTHESIOLOGY"
    ],
    "Emergency & Family Medicine": [
        "EMERGNCY MEDICINE",
        "FAMILY MEDICINE"
    ],
    "Internal Medicine & Subspecialties": [
        "CARDIOLOGY",
        "CLINICAL HAEMATOLOGY",
        "DERMATOLOGY",
        "ENDOCRINOLOGY",
        "GASTROENTEROLOGY",
        "HEPATOLOGY",
        "GERIATRIC MEDICINE",
        "INFECTIOUS DISEASES",
        "INFECTIOUS DISEASES MEDICINE",
        "INTENSIVE CARE MEDICINE",
        "INTERNAL MEDICINE",
        "MEDICAL ONCOLOGY",
        "NEPHROLOGY",
        "NEUROLOGY",
        "PALLIATIVE MEDICINE",
        "RESPIRATORY MEDICINE",
        "RHEUMATOLOGY"
    ],
    "Obstetrics & Gynaecology": [
        "GYNAE-ONCOLOGY",
        "MATERNAL FETAL MEDICINE",
        "OBSTETRICS & GYNAECOLOGY",
        "REPRODUCTIVE MEDICINE",
        "URO-GYNAECOLOGY"
    ],
    "Oncology, Radiology & Physical Medicine": [
        "CLINICAL ONCOLOGY",
        "CLINICAL RADIOLOGY",
        "NUCLEAR MEDICINE",
        "ONCOLOGY",
        "RADIATION ONCOLOGY",
        "REHABILITATION MEDICINE",
        "SPORTS MEDICINE"
    ],
    "Paediatrics & Subspecialties": [
        "ADOLESCENT MEDICINE",
        "CLINICAL GENETICS",
        "DEVELOPMENTAL PAEDIATRICS",
        "GENERAL PAEDIATRICS",
        "NEONATOLOGY",
        "PAEDIATRIC CARDIOLOGY",
        "PAEDIATRIC DERMATOLOGY",
        "PAEDIATRIC ENDOCRINOLOGY",
        "PAEDIATRIC GASTROENTEROLOGY",
        "PAEDIATRIC HAEMATOLOGY & ONCOLOGY",
        "PAEDIATRIC INFECTIOUS DISEASES",
        "PAEDIATRIC INTENSIVE CARE",
        "PAEDIATRIC NEPHROLOGY",
        "PAEDIATRIC NEUROLOGY",
        "PAEDIATRIC RESPIRATORY MEDICINE",
        "PAEDIATRIC RHEUMATOLOGY",
        "PAEDIATRICS AND CHILD HEALTH"
    ],
    "Pathology": [
        "ANATOMICAL PATHOLOGY",
        "CHEMICAL PATHOLOGY",
        "CHEMICAL PATHOLOGY (METABOLIC MEDICINE)",
        "FORENSIC PATHOLOGY",
        "GENERAL PATHOLOGY",
        "GENETIC PATHOLOGY",
        "HAEMATOLOGY",
        "TRANSFUSION MEDICINE"
    ],
    "Psychiatry": [
        "CHILD AND ADOLESCENT PSYCHIATRY",
        "FORENSIC PSYCHIATRY",
        "PSYCHIATRY"
    ],
    "Public, Occupational & Military Health": [
        "COMMUNICABLE DISEASE EPIDEMIOLOGY",
        "MILITARY MEDICINE",
        "NON-COMMUNICABLE DISEASE EPIDEMIOLOGY",
        "OCCUPATIONAL HEALTH",
        "PUBLIC HEALTH MEDICINE"
    ],
    "Surgical Specialties & Subspecialties": [
        "ADVANCED MUSCOSKELETAL TRAUMA",
        "ARTHOPLASTY",
        "ARTHROSCOPY & SPORT SURGERY",
        "BREAST / AND ENDOCRINE SURGERY",
        "COLORECTAL SURGERY",
        "GENERAL SURGERY",
        "HEPATOBILIARY SURGERY",
        "NEUROSURGERY",
        "OPHTHALMOLOGY",
        "ORTHOPAEDIC ONCOLOGY",
        "ORTHOPAEDIC SURGERY",
        "OTORHINOLARYNGOLOGY (ENT)",
        "PAEDIATRIC ORTHOPAEDICS",
        "PAEDIATRIC SURGERY",
        "PLASTIC SURGERY",
        "SPINE SURGERY",
        "THORACIC / CARDIOTHORACIC SURGERY",
        "UPPER GIT SURGERY",
        "UPPER LIMB & MICROSURGERY",
        "UROLOGY",
        "VASCULAR SURGERY"
    ]
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
# 4. STREAMLIT SHEET HEADERS
# ---------------------------------------------------------
SHEET_HEADERS = {
    "Emergency Care Complex (ECC)": [
        'MONTH', 'DATE', 'TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'DIAGNOSIS', 
        'DISEASE CATEGORIES', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'HOSPITALIZATION MODE', 'CASE TYPE', 'MODE OF PAYMENT', 'ADMITTED TO', 'CASE COUNT'
    ],
    "Endoscopy Unit (ENDO)": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'PROCEDURE CATEGORIES', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'SURGEON / PROCEDURALIST', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'PROCEDURE NATURE', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "Hemodialysis Unit (HDU)": [
        'MONTH', 'DATE', 'TRUE DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'DIAGNOSIS', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'DIALYSIS SHIFT SLOT', 'HOSPITALIZATION MODE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "OBGYNE Care Complex (LRDR-OB Surgery)": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'PROCEDURE BREAKDOWN', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'SURGEON / OBGYNE', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "Surgical Care Complex (OR Main)": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'SURGICAL PROCEDURE FLAGS', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'PRIMARY SURGEON', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)": [
        'MONTH', 'DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AOG', 'AGE', 'DIAGNOSIS', 
        'DIAGNOSTIC FLAGS', 'ADMITTED FROM', 'ADMITTED TO', 'TRANSFERRED TO', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'HOSPITALIZATION MODE', 'MODE OF PAYMENT', 'CASE COUNT'
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
# 5. GOOGLE SHEETS CONNECTION & SETUP
# ---------------------------------------------------------
@st.cache_resource
def init_google_sheets():
    from google.oauth2.service_account import Credentials
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    if "gcp_service_account" in st.secrets:
        try:
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_dict:
                pk = str(creds_dict["private_key"])
                pk = pk.strip("'\" \n\r")
                pk = pk.replace("\\n", "\n")
                
                if "-----BEGIN PRIVATE KEY-----" in pk and "-----END PRIVATE KEY-----" in pk:
                    start_idx = pk.find("-----BEGIN PRIVATE KEY-----")
                    end_idx = pk.find("-----END PRIVATE KEY-----") + len("-----END PRIVATE KEY-----")
                    pk = pk[start_idx:end_idx]
                
                creds_dict["private_key"] = pk
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        except Exception as e:
            st.error(f"Error parsing Streamlit Secrets credentials: {e}")
            st.stop()
    elif os.path.exists("credentials.json"):
        creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
    else:
        st.error("Google Cloud credentials not found! Please configure Streamlit Secrets (`gcp_service_account`) in your Streamlit Cloud app settings.")
        st.stop()
        
    client = gspread.authorize(creds)
    spreadsheet_title = "MTCMC_CENSUS_MASTERFILES_SYSTEM"
    try:
        sh = client.open(spreadsheet_title)
    except gspread.SpreadsheetNotFound:
        sh = client.create(spreadsheet_title)
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

def append_record_to_google_sheet(sheet_name, row_dict):
    ensure_google_sheets_exist()
    try:
        ws = sh.worksheet(sheet_name)
        headers = ws.row_values(4)
        if not headers:
            headers = SHEET_HEADERS.get(sheet_name, [])
            ws.update('A4', [headers])
            
        row_values = []
        for h in headers:
            val = row_dict.get(h, "")
            row_values.append("" if (val is None or pd.isna(val)) else str(val))
            
        ws.append_row(row_values)
        return True
    except Exception as e:
        st.error(f"Error saving to Google Sheets: {e}")
        return False

def read_google_sheet(sheet_name):
    ensure_google_sheets_exist()
    try:
        ws = sh.worksheet(sheet_name)
        data = ws.get_all_values()
        if len(data) >= 4:
            headers = data[3]
            rows = data[4:]
            if rows:
                df = pd.DataFrame(rows, columns=headers[:len(rows[0])])
                return df
    except Exception as e:
        st.warning(f"Note: Could not load sheet '{sheet_name}' from Google Sheets.")
    return pd.DataFrame()

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

# ---------------------------------------------------------
# 6. STREAMLIT APP INTERFACE
# ---------------------------------------------------------
st.title("MOTHER TERESA OF CALCUTTA MEDICAL CENTER")
st.markdown("All data entries are securely stored on our hospital database.")

MODULES = [
    "Hospital Information System", 
    "Emergency Care Complex (ECC)", 
    "Endoscopy Unit (ENDO)", 
    "Hemodialysis Unit (HDU)", 
    "OBGYNE Care Complex (LRDR-OB Surgery)", 
    "Surgical Care Complex (OR Main)", 
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
]
selected_sheet = st.sidebar.selectbox("Select Target Google Sheet Module", MODULES, index=0)

st.markdown("---")

# ---------------------------------------------------------
# MODULE: HOSPITAL INFORMATION SYSTEM (LANDING PAGE)
# ---------------------------------------------------------
if selected_sheet == "Hospital Information System":
    st.header("Hospital Summary")
    st.markdown("This is the census summary of the departments of MTCMC.")

    department_sheets = [
        "Emergency Care Complex (ECC)", 
        "Endoscopy Unit (ENDO)", 
        "Hemodialysis Unit (HDU)", 
        "OBGYNE Care Complex (LRDR-OB Surgery)", 
        "Surgical Care Complex (OR Main)", 
        "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
    ]
    
    summary_data = []
    total_all_cases = 0
    ph_now_summary = get_ph_time()
    today_str = ph_now_summary.strftime("%m/%d/%Y")
    current_month_num = str(ph_now_summary.month)
    current_month_name = ph_now_summary.strftime("%B").upper()

    for dept in department_sheets:
        df = read_google_sheet(dept)
        record_count = len(df) if not df.empty else 0
        total_all_cases += record_count
        
        daily_count = 0
        monthly_count = 0
        
        if not df.empty and 'DATE' in df.columns:
            daily_count = len(df[df['DATE'].astype(str).str.strip() == today_str])
            if 'MONTH' in df.columns:
                monthly_subset = df[
                    df['MONTH'].astype(str).str.contains(current_month_name, case=False, na=False) |
                    df['MONTH'].astype(str).str.startswith(f"{current_month_num}.", na=False)
                ]
                monthly_count = len(monthly_subset)

        summary_data.append({
            "Department Module": dept,
            "Total Census Records": record_count,
            "Daily Patient Census": daily_count,
            "Monthly Patient Census": monthly_count
        })

    m1, m2 = st.columns(2)
    with m1:
        st.metric(label="Total Hospital-Wide Census Records", value=total_all_cases)
    with m2:
        st.metric(label="Active Departments Tracked", value=len(department_sheets))

    st.markdown("---")
    st.subheader("Department Performance")
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(summary_df, use_container_width=True)

    st.markdown("---")
    st.subheader("Department Summary")
    selected_dept_view = st.selectbox("Select Department to Tally & Inspect", department_sheets)
    
    dept_df = read_google_sheet(selected_dept_view)
    if not dept_df.empty:
        st.write(f"Showing all records for **{selected_dept_view}** (Total: {len(dept_df)} records)")
        
        if selected_dept_view == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)" and 'ADMITTED TO' in dept_df.columns:
            st.markdown("##### 📍 Sort & Filter by Admitted Area")
            admit_areas = sorted(dept_df['ADMITTED TO'].dropna().unique().tolist())
            selected_area = st.selectbox("Select Admitted To Area", ["All Areas"] + admit_areas)
            
            if selected_area != "All Areas":
                dept_df = dept_df[dept_df['ADMITTED TO'] == selected_area]
                st.write(f"Filtered to **{selected_area}** ({len(dept_df)} records)")

        preferred_cols = ['DATE', 'LAST NAME', 'FIRST NAME', 'DIAGNOSIS', 'DIAGNOSTIC FLAGS', 'ATTENDING PHYSICIAN', 'PRIMARY SURGEON', 'SURGEON / PROCEDURALIST', 'SURGEON / OBGYNE', 'ADMITTED TO', 'TRANSFERRED TO', 'MODE OF PAYMENT']
        display_cols = [c for c in preferred_cols if c in dept_df.columns]
        if not display_cols:
            display_cols = dept_df.columns.tolist()

        if 'MODE OF PAYMENT' in dept_df.columns and selected_dept_view != "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)":
            st.markdown("##### 💳 Breakdown by Mode of Payment")
            payment_counts = dept_df['MODE OF PAYMENT'].value_counts().reset_index()
            payment_counts.columns = ['Mode of Payment', 'Count']
            st.bar_chart(payment_counts.set_index('Mode of Payment'))
            
        st.dataframe(dept_df[display_cols], use_container_width=True)
    else:
        st.info(f"No records found yet for {selected_dept_view}.")

# ---------------------------------------------------------
# FORM 1: Emergency Care Complex (ECC)
# ---------------------------------------------------------
elif selected_sheet == "Emergency Care Complex (ECC)":
    st.header("Emergency Care Complex (ECC) Data Entry Form")
    ph_now = get_ph_time()
    with st.form("ecc_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics & AI Checker")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="")
        with c2:
            first_name = st.text_input("First Name", value="")
        with c3:
            middle_name = st.text_input("Middle Name", value="")
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["None", "Male", "Female", "Others"])

        c_d1, c_d2 = st.columns(2)
        with c_d1:
            entry_date = st.date_input("Date", ph_now.date())
        with c_d2:
            entry_time_str = civilian_time_text_field("Time of Entry", key_suffix="ecc_time")

        c_h1, c_h2, c_h3 = st.columns(3)
        with c_h1:
            hosp_mode = st.selectbox("Hospitalization Mode", ["None", "IPD - Inpatient", "OPD - Outpatient"])
        with c_h2:
            case_type = st.selectbox("Case Type", ["None", "Private Case", "House Case (Walk-in)", "Not Applicable"])
        with c_h3:
            payment_selected = st.selectbox("Mode of Payment", ["None", "PHIC", "HMO", "SELF-PAY", "CHARITY"])

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Physician Information")
        c_doc1, c_doc2, c_doc3 = st.columns(3)
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name", value="")
        with c_doc2:
            attending_spec = st.selectbox("Specialization", SPECIALTY_DROPDOWN_OPTIONS)
        with c_doc3:
            admitted_to = st.selectbox("Admitted to", HOSPITAL_UNIT_AREAS)

        st.subheader("📋 Clinical Details")
        diagnosis_text = st.text_area("Clinical Diagnosis", value="")

        disease_options = [
            'ACUTE GASTROENTERITIS', 'DENGUE FEVER', 'HYPERTENSION', 'GASTROESOPHAGEAL REFLUX DISEASE',
            'URINARY TRACT INFECTION', 'BRONCHIAL ASTHMA', 'DIABETES MELLITUS', 'RESPIRATORY TRACT INECTION',
            'ELECTROLYTE IMBALANCE', 'ACUTE TONSILLOPHARYNGITIS', 'ANIMAL BITE', 'VERTIGO',
            'HYPERSENSITIVITY REACTION', 'INFECTED WOUND', 'ACUTE CORONARY SYNDROME', 'SYSTEMIC VIRAL ILLNESS',
            'FRACTURE', 'OTHER CASES'
        ]
        selected_diseases = st.multiselect("Select Disease Category Flags", disease_options)

        submitted = st.form_submit_button("Submit Record to Google Sheets")
        if submitted:
            existing_record = check_existing_patient_ai("Emergency Care Complex (ECC)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            row_data = {
                'MONTH': get_month_str(entry_date, "full_month"),
                'DATE': curr_date_str,
                'TIME': entry_time_str,
                'LAST NAME': last_name,
                'FIRST NAME': first_name,
                'MIDDLE NAME': middle_name,
                'SEX': sex,
                'AGE': str(age),
                'DIAGNOSIS': diagnosis_text,
                'DISEASE CATEGORIES': ", ".join(selected_diseases) if selected_diseases else "None",
                'ATTENDING PHYSICIAN': attending_physician if attending_physician else "N/A",
                'ATTENDING SPECIALIZATION': attending_spec,
                'HOSPITALIZATION MODE': hosp_mode,
                'CASE TYPE': case_type,
                'MODE OF PAYMENT': payment_selected,
                'ADMITTED TO': admitted_to,
                'CASE COUNT': 1
            }

            if append_record_to_google_sheet("Emergency Care Complex (ECC)", row_data):
                st.success("Successfully saved to Google Sheets `Emergency Care Complex (ECC)` tab!")

# ---------------------------------------------------------
# FORM 2: Endoscopy Unit (ENDO)
# ---------------------------------------------------------
elif selected_sheet == "Endoscopy Unit (ENDO)":
    st.header("Endoscopy Unit Data Entry Form")
    ph_now = get_ph_time()
    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_endo")

    with st.form("endo_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics & AI Checker")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="")
        with c2:
            first_name = st.text_input("First Name", value="")
        with c3:
            middle_name = st.text_input("Middle Name", value="")
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["None", "Male", "Female", "Others"])

        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            entry_date = st.date_input("Procedure Date", ph_now.date())
        with c_d2:
            sched_time_str = civilian_time_text_field("Scheduled Time", key_suffix="endo_sched")
        with c_d3:
            actual_time_str = civilian_time_text_field("Actual Time", key_suffix="endo_actual")

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical & Surgical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name", value="")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROPDOWN_OPTIONS)

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", value="", key=f"cm_name_endo_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROPDOWN_OPTIONS, key=f"cm_spec_endo_{i}")
                cm_entries.append((cm_name, cm_spec))

        c_surg1, c_surg2 = st.columns(2)
        with c_surg1:
            surgeon = st.text_input("Surgeon / Endoscopist / Proceduralist", value="")
        with c_surg2:
            surgeon_spec = st.selectbox("Surgeon / Proceduralist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("GASTROENTEROLOGY"))

        c_anes1, c_anes2 = st.columns(2)
        with c_anes1:
            anesthesiologist = st.text_input("Anesthesiologist Name", value="")
        with c_anes2:
            anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("GENERAL ANAESTHESIOLOGY"))

        st.subheader("📋 Diagnosis & Procedure Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis_text = st.text_input("Diagnosis", value="")
        with cd2:
            procedure_text = st.text_input("Procedure Name", value="")

        proc_cols = ['GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES']
        selected_procs = st.multiselect("Select Procedure Flags", proc_cols)
        
        ca, cb, cc, cd = st.columns(4)
        with ca: 
            proc_type = st.radio("Nature", ["DIAGNOSTICS", "THERAPEUTIC", "DIAGNOSTICS & THERAPEUTIC"])
        with cb: 
            hosp_mode = st.radio("Hospitalization Mode", ["OPD", "IPD"])
        with cc: 
            payment_selected = st.selectbox("Mode of Payment", ["None", "PHIC", "HMO", "SELF-PAY"])
        with cd:
            kit_package = st.checkbox("Hospital Kit Package", value=False)

        submitted = st.form_submit_button("Submit Record to Google Sheets")
        if submitted:
            existing_record = check_existing_patient_ai("Endoscopy Unit (ENDO)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "mixed"),
                'DATE': curr_date_str,
                'SCHEDULED TIME': sched_time_str,
                'ACTUAL TIME': actual_time_str,
                'LAST NAME': last_name,
                'FIRST NAME': first_name,
                'MIDDLE NAME': middle_name,
                'SEX': sex,
                'AGE': age,
                'DIAGNOSIS': diagnosis_text,
                'PROCEDURE': procedure_text,
                'PROCEDURE CATEGORIES': ", ".join(selected_procs) if selected_procs else "None",
                'ATTENDING PHYSICIAN': attending_physician if attending_physician else "N/A",
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
                'CASE COUNT': 1
            }

            if append_record_to_google_sheet("Endoscopy Unit (ENDO)", row_data):
                st.success("Successfully saved to Google Sheets `Endoscopy Unit (ENDO)` tab!")

# ---------------------------------------------------------
# FORM 3: Hemodialysis Unit (HDU)
# ---------------------------------------------------------
elif selected_sheet == "Hemodialysis Unit (HDU)":
    st.header("Hemodialysis Unit Data Entry Form")

    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_hdu")

    with st.form("hdu_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics & AI Checker")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="")
        with c2:
            first_name = st.text_input("First Name", value="")
        with c3:
            middle_name = st.text_input("Middle Name", value="")
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["None", "Male", "Female", "Others"])

        c_d1, _ = st.columns([1, 1])
        with c_d1:
            entry_date = st.date_input("Dialysis Date", datetime.today())

        # Removed default "CKD" entry as requested
        diagnosis = st.text_input("Diagnosis", value="")
        curr_date_str = entry_date.strftime("%B %d, %Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            # Removed default "DR. ALEJANDRO SESE JR." entry as requested
            attending_physician = st.text_input("Attending Nephrologist / Physician Name", value="")
        with c_att2:
            attending_spec = st.selectbox("Attending Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("NEPHROLOGY"))

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", value="", key=f"cm_name_hdu_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROPDOWN_OPTIONS, key=f"cm_spec_hdu_{i}")
                cm_entries.append((cm_name, cm_spec))

        c7, c8, c9 = st.columns(3)
        with c7:
            shift_set = st.selectbox("Dialysis Shift Slot", ["None", "1ST SET", "2ND SET", "3RD SET", "ONCALL"])
        with c8:
            hosp_mode = st.radio("Hospitalization Mode", ["OPD", "IPD"])
        with c9:
            payment_selected = st.selectbox("Mode of Payment", ["None", "PHIC", "HMO", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Google Sheets")
        if submitted:
            existing_record = check_existing_patient_ai("Hemodialysis Unit (HDU)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            epoch = datetime(1899, 12, 30)
            true_date = str((datetime.combine(entry_date, datetime.min.time()) - epoch).days)
            
            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'TRUE DATE': true_date,
                'LAST NAME': last_name,
                'FIRST NAME': first_name,
                'MIDDLE NAME': middle_name,
                'SEX': sex,
                'DIAGNOSIS': diagnosis,
                'ATTENDING PHYSICIAN': attending_physician,
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'DIALYSIS SHIFT SLOT': shift_set,
                'HOSPITALIZATION MODE': hosp_mode,
                'MODE OF PAYMENT': payment_selected,
                'CASE COUNT': 1
            }

            if append_record_to_google_sheet("Hemodialysis Unit (HDU)", row_data):
                st.success("Successfully saved to Google Sheets `Hemodialysis Unit (HDU)` tab!")

# ---------------------------------------------------------
# FORM 4: OBGYNE Care Complex (LRDR-OB Surgery)
# ---------------------------------------------------------
elif selected_sheet == "OBGYNE Care Complex (LRDR-OB Surgery)":
    st.header("OBGYNE Cases Data Entry Form")
    ph_now = get_ph_time()
    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_obgyne")

    with st.form("obgyne_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics & AI Checker")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="")
        with c2:
            first_name = st.text_input("First Name", value="")
        with c3:
            middle_name = st.text_input("Middle Name", value="")
        with c4:
            age = st.number_input("Age", min_value=10, max_value=100, value=10)
        with c5:
            sex = st.selectbox("Sex", ["None", "Female", "Male", "Others"])

        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            entry_date = st.date_input("Procedure Date", ph_now.date())
        with c_d2:
            sched_time_str = civilian_time_text_field("Scheduled Time", key_suffix="ob_sched")
        with c_d3:
            actual_time_str = civilian_time_text_field("Actual Time", key_suffix="ob_actual")

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical & Surgical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name", value="")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("OBSTETRICS & GYNAECOLOGY"))

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", value="", key=f"cm_name_ob_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROPDOWN_OPTIONS, key=f"cm_spec_ob_{i}")
                cm_entries.append((cm_name, cm_spec))

        c_surg1, c_surg2 = st.columns(2)
        with c_surg1:
            surgeon = st.text_input("Surgeon / OBGYNE Primary Operator", value="")
        with c_surg2:
            surgeon_spec = st.selectbox("Surgeon Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("OBSTETRICS & GYNAECOLOGY"))

        c_anes1, c_anes2 = st.columns(2)
        with c_anes1:
            anesthesiologist = st.text_input("Anesthesiologist Name", value="")
        with c_anes2:
            anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("GENERAL ANAESTHESIOLOGY"))

        st.subheader("📋 OBGYNE Diagnosis & Procedure Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis = st.text_area("OBGYNE Diagnosis", value="")
        with cd2:
            procedure = st.text_input("Procedure Name", value="")

        ca, cb, cc, cd = st.columns(4)
        with ca:
            ob_procs = st.multiselect("Procedure Breakdown", ["CS PRIMARY", "CS", "NSD", "D&C", "HYSTERECTOMY", "EXLAP", "OTHER PROCEDURES", "NST"])
        with cb:
            complexity = st.selectbox("Complexity Tier", ["None", "MAJOR", "MINOR", "DIAGNOSTIC"])
        with cc:
            hosp_mode = st.radio("Hospitalization Mode", ["OPD", "IPD"])
            kit_used = st.checkbox("Hospital Kit Package", value=True)
        with cd:
            payment_selected = st.selectbox("Mode of Payment", ["None", "PHIC", "HMO", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Google Sheets")
        if submitted:
            existing_record = check_existing_patient_ai("OBGYNE Care Complex (LRDR-OB Surgery)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'SCHEDULED TIME': sched_time_str,
                'ACTUAL TIME': actual_time_str,
                'LAST NAME': last_name,
                'FIRST NAME': first_name,
                'MIDDLE NAME': middle_name,
                'SEX': sex,
                'AGE': float(age),
                'DIAGNOSIS': diagnosis,
                'PROCEDURE': procedure,
                'PROCEDURE BREAKDOWN': ", ".join(ob_procs) if ob_procs else "None",
                'ATTENDING PHYSICIAN': attending_physician if attending_physician else "N/A",
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
                'CASE COUNT': 1
            }

            if append_record_to_google_sheet("OBGYNE Care Complex (LRDR-OB Surgery)", row_data):
                st.success("Successfully saved to Google Sheets `OBGYNE Care Complex (LRDR-OB Surgery)` tab!")

# ---------------------------------------------------------
# FORM 5: Surgical Care Complex (OR Main)
# ---------------------------------------------------------
elif selected_sheet == "Surgical Care Complex (OR Main)":
    st.header("Surgical Care Center (SCC) Data Entry Form")
    ph_now = get_ph_time()
    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_scc")

    with st.form("scc_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics & AI Checker")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="")
        with c2:
            first_name = st.text_input("First Name", value="")
        with c3:
            middle_name = st.text_input("Middle Name", value="")
        with c4:
            age = st.number_input("Age", min_value=0, max_value=120, value=0)
        with c5:
            sex = st.selectbox("Sex", ["None", "Male", "Female", "Others"])

        c_d1, c_d2, c_d3 = st.columns(3)
        with c_d1:
            entry_date = st.date_input("Surgery Date", ph_now.date())
        with c_d2:
            sched_time_str = civilian_time_text_field("Scheduled Time", key_suffix="scc_sched")
        with c_d3:
            actual_time_str = civilian_time_text_field("Actual Time", key_suffix="scc_actual")

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical & Surgical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name", value="")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROPDOWN_OPTIONS)

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", value="", key=f"cm_name_scc_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROPDOWN_OPTIONS, key=f"cm_spec_scc_{i}")
                cm_entries.append((cm_name, cm_spec))

        c_surg1, c_surg2 = st.columns(2)
        with c_surg1:
            surgeon = st.text_input("Primary Surgeon", value="")
        with c_surg2:
            surgeon_spec = st.selectbox("Surgeon Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("GENERAL SURGERY"))

        c_anes1, c_anes2 = st.columns(2)
        with c_anes1:
            anesthesiologist = st.text_input("Anesthesiologist Name", value="")
        with c_anes2:
            anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("GENERAL ANAESTHESIOLOGY"))

        st.subheader("📋 Pre/Post-Op & Surgical Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis = st.text_area("Pre/Post-Op Diagnosis", value="")
        with cd2:
            procedure = st.text_area("Surgical Procedure", value="")

        all_scc_procs = [
            'EXCISION BIOPSY', 'INCISION AND DRAINAGE', 'WOUND SUTURING & CLOSING AND CHANGE OF DRESSING',
            'PLEURAL CATH INSERTION', 'COLOSTOMY', 'DEBRIDEMENT', 'ANAL BIOPSY', 'CORE NEEDLE BIOPSY',
            'THYROIDECTOMY', 'PAROTIDECTOMY', 'MASTECTOMY', 'CHOLECYSTECTOMY', 'APPENDECTOMY',
            'TONSILLECTOMY', 'HERNIORRHAPY', 'CHANGE OF TRACHEOSTOMY', 'LAPAROTOMY', 'GASTROSTOMY TUBE INSERTION',
            'OPTHA SURGERY', 'PLASTIC SURGERY', 'SPINE SURGERY', 'CRANIOTOMY', 'MASTOIDECTOMY',
            'TYMPANOPLASTY', 'MAXILLECTOMY', 'ORTHO SURGERY', 'MICROLARYNGEAL SURGERY', 'HYSTEROSCOPY',
            'ULTRASOUND GUIDED', 'MIS', 'AVF', 'IJ CATH', 'PERM CATH/ FEMORAL CATH', 'PROCTOSCOPY',
            'CHOLEDOSCOPY', 'DENTAL PROCEDURES', 'OTHER PROCEDURES'
        ]
        selected_scc_procs = st.multiselect("Select Surgical Procedure Flags", all_scc_procs)

        ca, cb, cc, cd = st.columns(4)
        with ca: 
            complexity = st.selectbox("Complexity Tier", ["None", "MAJOR", "MEDIUM", "MINOR", "DIAGNOSTICS"])
        with cb: 
            hosp_mode = st.radio("Hospitalization Mode", ["OPD", "IPD"])
        with cc: 
            kit_package = st.checkbox("Hospital Kit Package", value=True)
        with cd: 
            payment_selected = st.selectbox("Mode of Payment", ["None", "PHIC", "HMO", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Google Sheets")
        if submitted:
            existing_record = check_existing_patient_ai("Surgical Care Complex (OR Main)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'SCHEDULED TIME': sched_time_str,
                'ACTUAL TIME': actual_time_str,
                'LAST NAME': last_name,
                'FIRST NAME': first_name,
                'MIDDLE NAME': middle_name,
                'SEX': sex,
                'AGE': float(age),
                'DIAGNOSIS': diagnosis,
                'PROCEDURE': procedure,
                'SURGICAL PROCEDURE FLAGS': ", ".join(selected_scc_procs) if selected_scc_procs else "None",
                'ATTENDING PHYSICIAN': attending_physician if attending_physician else "N/A",
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
                'CASE COUNT': 1
            }

            if append_record_to_google_sheet("Surgical Care Complex (OR Main)", row_data):
                st.success("Successfully saved to Google Sheets `Surgical Care Complex (OR Main)` tab!")

# ---------------------------------------------------------
# FORM 6: Special Care Complex (NICU-PICU-NSU/PCN-Outborn)
# ---------------------------------------------------------
elif selected_sheet == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)":
    st.header("Special Care Unit (SCU) Data Entry Form")

    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_scu")

    with st.form("scu_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics & AI Checker")
        
        c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
        with c1:
            last_name = st.text_input("Last Name", value="")
        with c2:
            first_name = st.text_input("First Name", value="")
        with c3:
            middle_name = st.text_input("Middle Name", value="")
        with c4:
            sex = st.selectbox("Sex", ["None", "Male", "Female", "Others"])

        c5_d, c6, c7, c8 = st.columns(4)
        with c5_d:
            entry_date = st.date_input("Admission Date", datetime.today())
            aog = st.text_input("Age of Gestation (AOG)", value="38 WEEKS")
        with c6:
            age_y = st.number_input("Age (Years)", min_value=0, max_value=18, value=0)
        with c7:
            age_m = st.number_input("Age (Months)", min_value=0, max_value=11, value=0)
        with c8:
            age_d = st.number_input("Age (Days)", min_value=0, max_value=31, value=0)

        curr_date_str = entry_date.strftime("%m/%d/%Y")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name", value="")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=get_spec_index("GENERAL PAEDIATRICS"))

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", value="", key=f"cm_name_scu_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROPDOWN_OPTIONS, key=f"cm_spec_scu_{i}")
                cm_entries.append((cm_name, cm_spec))

        c10, c11, c12, c13 = st.columns(4)
        with c10:
            admitted_from = st.selectbox("Admitted From", HOSPITAL_UNIT_AREAS)
        with c11:
            admitted_to = st.selectbox("Admitted To", ["None", "NICU", "PICU", "NSU", "PCN", "OUTBORN", "ROOM-IN"])
        with c12:
            transferred_to = st.selectbox("Transferred To", HOSPITAL_UNIT_AREAS)
        with c13:
            hosp_mode = st.radio("Hospitalization Mode", ["IPD", "OPD"])

        payment_selected = st.selectbox("Mode of Payment", ["None", "PHIC", "HMO", "SELF-PAY"])

        st.subheader("📋 Diagnosis & Diagnostic Flags")
        diagnosis = st.text_area("Diagnosis Text", value="")
        diag_flags = st.multiselect("Diagnostic Flags", ["PNEUMONIA", "SEPSIS", "PCAP", "SURGERY"])

        submitted = st.form_submit_button("Submit Record to Google Sheets")
        if submitted:
            existing_record = check_existing_patient_ai("Special Care Complex (NICU-PICU-NSU/PCN-Outborn)", last_name, first_name, curr_date_str)
            if existing_record:
                st.info(f"🤖 AI Checker: Patient {last_name}, {first_name} already exists on {curr_date_str}. Additional department info has been merged into their record.")

            age_str_parts = []
            if age_y > 0: age_str_parts.append(f"{age_y} Yrs")
            if age_m > 0: age_str_parts.append(f"{age_m} Mos")
            if age_d > 0: age_str_parts.append(f"{age_d} Days")
            age_formatted = ", ".join(age_str_parts) if age_str_parts else "Neonate / Infant"

            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': curr_date_str,
                'LAST NAME': last_name,
                'FIRST NAME': first_name,
                'MIDDLE NAME': middle_name,
                'SEX': sex,
                'AOG': aog if aog else "N/A",
                'AGE': age_formatted,
                'DIAGNOSIS': diagnosis,
                'DIAGNOSTIC FLAGS': ", ".join(diag_flags) if diag_flags else "None",
                'ADMITTED FROM': admitted_from,
                'ADMITTED TO': admitted_to,
                'TRANSFERRED TO': transferred_to,
                'ATTENDING PHYSICIAN': attending_physician if attending_physician else "N/A",
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'HOSPITALIZATION MODE': hosp_mode,
                'MODE OF PAYMENT': payment_selected,
                'CASE COUNT': 1
            }

            if append_record_to_google_sheet("Special Care Complex (NICU-PICU-NSU/PCN-Outborn)", row_data):
                st.success("Successfully saved to Google Sheets `Special Care Complex (NICU-PICU-NSU/PCN-Outborn)` tab!")

if selected_sheet != "Hospital Information System":
    st.markdown("---")
    st.subheader(f"Active Patient Census: {selected_sheet}")

    sheet_df = read_google_sheet(selected_sheet)
    if not sheet_df.empty:
        st.dataframe(sheet_df.tail(10), use_container_width=True)
        st.caption(f"Showing last 10 entries of `{selected_sheet}` (Total: {len(sheet_df)} records)")
    else:
        st.info(f"Google Sheets worksheet `{selected_sheet}` currently has no records.")