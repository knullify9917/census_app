import base64
import concurrent.futures
from datetime import datetime
import hashlib
import io
import json
import os
import pickle
import random
import sqlite3
import threading
import time as py_time
from zoneinfo import ZoneInfo
import gspread
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION & LOGO-MATCHED BLUE/GREEN COLORWAY
# ---------------------------------------------------------
st.set_page_config(
    page_title="PATIENT DATA RECORDING SYSTEM",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
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
    
    /* Unified Button Theme across all forms and actions */
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

    /* Form Inputs, Textareas, and Dropdown Controls */
    div[data-baseweb="select"] > div, input[type="text"]:not([type="password"]), input[type="number"], textarea {
        background-color: #ffffff !important; color: #1e3a8a !important; border: 1px solid #cbd5e1 !important; border-radius: 6px !important; text-transform: uppercase !important;
    }
    input[type="password"] {
        text-transform: none !important;
    }
    div[data-baseweb="select"] span { color: #1e3a8a !important; }
    
    div[data-baseweb="input"] {
        background-color: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 6px !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #0f766e !important;
        box-shadow: 0 0 0 1px #0f766e !important;
    }

    div[data-baseweb="popover"], div[data-baseweb="menu"], ul[role="listbox"] {
        background-color: #ffffff !important; color: #1e3a8a !important; border: 1px solid #cbd5e1 !important; z-index: 999999 !important; box-shadow: 0 4px 12px rgba(0,0,0,0.1) !important;
    }
    li[role="option"], div[data-baseweb="menu"] div, option { background-color: #ffffff !important; color: #1e3a8a !important; }
    li[role="option"]:hover, div[data-baseweb="menu"] div:hover { background-color: #f0fdf4 !important; color: #0f766e !important; }
    
    [data-testid="stDataFrame"] { background-color: #ffffff !important; border: 1px solid #cbd5e1; border-radius: 6px; padding: 4px; }
    [data-testid="stDataFrame"] table { background-color: #ffffff !important; color: #1e293b !important; }
    [data-testid="stDataFrame"] thead tr th { background-color: #e2e8f0 !important; color: #1e3a8a !important; font-weight: bold !important; }
    
    div.stMetric {
        background-color: #ffffff !important; padding: 15px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); border: 1px solid #cbd5e1; border-left: 5px solid #0f766e !important;
    }
    div.stMetric label { color: #0f766e !important; font-weight: 600 !important; }
    div.stMetric div[data-testid="stMetricValue"] { color: #1e3a8a !important; font-weight: bold !important; }
    
    div.stForm { background-color: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; box-shadow: 0 1px 2px rgba(0,0,0,0.02); }
</style>
""",
    unsafe_allow_html=True,
)


def hash_password(password):
  return hashlib.sha256(password.encode()).hexdigest()


DEFAULT_USER_DATABASE = {
    "admin": {
        "password": hash_password("894413"),
        "role": "Administrator",
        "name": "System Administrator",
        "modules": "All",
    },
    "ecc_staff": {
        "password": hash_password("ecc2026"),
        "role": "ECC Staff",
        "name": "Emergency Care Staff",
        "modules": [
            "Hospital Information System",
            "Pareto Tally Sheet",
            "Emergency Care Complex (ECC)",
        ],
    },
    "scc_staff": {
        "password": hash_password("scc2026"),
        "role": "SCC Staff",
        "name": "Surgical Care Staff",
        "modules": [
            "Hospital Information System",
            "Pareto Tally Sheet",
            "Surgical Care Complex (OR Main)",
        ],
    },
    "endo_staff": {
        "password": hash_password("endo2026"),
        "role": "ENDO Staff",
        "name": "Endoscopy Unit Staff",
        "modules": [
            "Hospital Information System",
            "Pareto Tally Sheet",
            "Endoscopy Unit (ENDO)",
        ],
    },
    "hdu_staff": {
        "password": hash_password("hdu2026"),
        "role": "HDU Staff",
        "name": "Hemodialysis Unit Staff",
        "modules": [
            "Hospital Information System",
            "Pareto Tally Sheet",
            "Hemodialysis Unit (HDU)",
        ],
    },
    "nsu_staff": {
        "password": hash_password("nsu2026"),
        "role": "Special Care Staff",
        "name": "Special Care Unit Staff",
        "modules": [
            "Hospital Information System",
            "Pareto Tally Sheet",
            "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
        ],
    },
    "obgyne_staff": {
        "password": hash_password("obgyne2026"),
        "role": "OBGYNE Staff",
        "name": "OBGYNE Care Staff",
        "modules": [
            "Hospital Information System",
            "Pareto Tally Sheet",
            "OBGYNE Care Complex (LRDR-OB Surgery)",
        ],
    },
    "nsgcon_staff": {
        "password": hash_password("nsgcon2026"),
        "role": "Nursing Administration",
        "name": "Nursing Control Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet"],
    },
    "ha_staff": {
        "password": hash_password("hastaff2026"),
        "role": "Hospital Administration",
        "name": "Hospital Administration Staff",
        "modules": ["Hospital Information System", "Pareto Tally Sheet"],
    },
    "ha_staff1": {
        "password": hash_password("hastaff12026"),
        "role": "Hospital Administration",
        "name": "Hospital Administration Staff 1",
        "modules": ["Hospital Information System", "Pareto Tally Sheet"],
    },
}

USER_DATABASE = st.secrets.get("users", DEFAULT_USER_DATABASE)

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
if "sync_health_status" not in st.session_state:
  st.session_state["sync_health_status"] = "Healthy (Idle)"
if "status_checksum" not in st.session_state:
  st.session_state["status_checksum"] = ""

for form_key in [
    "ecc",
    "endo",
    "hdu",
    "ob",
    "scc",
    "scu",
    "1c",
    "2a",
    "2b",
    "2c",
    "2d",
    "3a",
    "3b",
    "3c",
    "4a",
]:
  if f"cm_list_{form_key}" not in st.session_state:
    st.session_state[f"cm_list_{form_key}"] = []

if not st.session_state["authenticated"]:
  col_l1, col_l2, col_l3 = st.columns([0.2, 2.6, 0.2])
  with col_l2:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.markdown(
        """
            <div style="text-align: center; margin-bottom: 25px;">
                <h1 style="color: #1e3a8a; margin-bottom: -2px; font-size: 2.8rem; white-space: nowrap; font-weight: 800;">Mother Teresa of Calcutta Medical Center</h1>
                <p style="color: #0f766e; font-weight: 600; font-size: 1.4rem; margin-top: 0px; letter-spacing: 0.5px;">Patient Data System</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
      username_input = st.text_input("Username")
      password_input = st.text_input("Password", type="password")
      submit_login = st.form_submit_button("Sign In")

      if submit_login:
        user_record = USER_DATABASE.get(username_input.strip().lower())
        if user_record and user_record["password"] == hash_password(
            password_input
        ):
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
  t_val = st.time_input(
      label, value=current_default_time, key=f"time_widget_{key_suffix}"
  )
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


HOSPITAL_UNIT_AREAS = [
    "None",
    "ECC",
    "GNU 1C",
    "GNU 2A",
    "GNU 2B",
    "GNU 2C",
    "GNU 2D",
    "GNU 3A",
    "GNU 3B",
    "GNU 3C",
    "GNU 4A",
    "MS-ICU (MEDICAL SURGICAL – INTENSIVE CARE UNIT)",
    "NICU (NEONATAL INTENSIVE CARE UNIT)",
    "PICU (PEDIATRIC INTENSIVE CARE UNIT)",
    "NSU (NEWBORN SERVICE UNIT)",
    "PCN (PROGRESSIVE CARE UNIT)",
    "OUTBORN (OUTBORN BABIES ADMITTED IN THE UNIT)",
]
HOSPITAL_UNIT_AREAS = ["None"] + sorted([x for x in HOSPITAL_UNIT_AREAS if x != "None"])

raw_sorted_departments = [
    "Emergency Care Complex (ECC)",
    "Endoscopy Unit (ENDO)",
    "Hemodialysis Unit (HDU)",
    "OBGYNE Care Complex (LRDR-OB Surgery)",
    "Surgical Care Complex (OR Main)",
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
    "General Nursing Unit (GNU 1C)",
    "General Nursing Unit (GNU 2A)",
    "General Nursing Unit (GNU 2B)",
    "General Nursing Unit (GNU 2C)",
    "General Nursing Unit (GNU 2D)",
    "General Nursing Unit (GNU 3A)",
    "General Nursing Unit (GNU 3B)",
    "General Nursing Unit (GNU 3C)",
    "General Nursing Unit (GNU 4A)",
]
sorted_departments = sorted(raw_sorted_departments)

SPECIALTIES_BY_FIELD = {
    "Anaesthesiology": [
        "GENERAL ANAESTHESIOLOGY",
        "NEURO - ANAESTHESIOLOGY",
        "PEDIA - ANAESTHESIOLOGY",
    ],
    "Emergency & Family Medicine": ["EMERGNCY MEDICINE", "FAMILY MEDICINE"],
    "Internal Medicine & Subspecialties": [
        "CARDIOLOGY",
        "CLINICAL HAEMATOLOGY",
        "DERMATOLOGY",
        "ENDOCRINOLOGY",
        "GASTROENTEROLOGY",
        "HEPATOLOGY",
        "GERIATRIC MEDICINE",
        "INFECTIOUS DISEASES",
        "INTENSIVE CARE MEDICINE",
        "INTERNAL MEDICINE",
        "MEDICAL ONCOLOGY",
        "NEPHROLOGY",
        "NEUROLOGY",
        "PALLIATIVE MEDICINE",
        "RESPIRATORY MEDICINE",
        "RHEUMATOLOGY",
    ],
    "Obstetrics & Gynaecology": [
        "GYNAE-ONCOLOGY",
        "MATERNAL FETAL MEDICINE",
        "OBSTETRICS & GYNAECOLOGY",
        "REPRODUCTIVE MEDICINE",
        "URO-GYNAECOLOGY",
    ],
    "Oncology, Radiology & Physical Medicine": [
        "CLINICAL ONCOLOGY",
        "CLINICAL RADIOLOGY",
        "NUCLEAR MEDICINE",
        "ONCOLOGY",
        "RADIATION ONCOLOGY",
        "REHABILITATION MEDICINE",
        "SPORTS MEDICINE",
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
        "PAEDIATRICS AND CHILD HEALTH",
    ],
    "Pathology": [
        "ANATOMICAL PATHOLOGY",
        "CHEMICAL PATHOLOGY",
        "FORENSIC PATHOLOGY",
        "GENERAL PATHOLOGY",
        "GENETIC PATHOLOGY",
        "HAEMATOLOGY",
        "TRANSFUSION MEDICINE",
    ],
    "Psychiatry": [
        "CHILD AND ADOLESCENT PSYCHIATRY",
        "FORENSIC PSYCHIATRY",
        "PSYCHIATRY",
    ],
    "Public, Occupational & Military Health": [
        "COMMUNICABLE DISEASE EPIDEMIOLOGY",
        "MILITARY MEDICINE",
        "NON-COMMUNICABLE DISEASE EPIDEMIOLOGY",
        "OCCUPATIONAL HEALTH",
        "PUBLIC HEALTH MEDICINE",
    ],
    "Surgical Specialties & Subspecialties": [
        "GENERAL SURGERY",
        "NEUROSURGERY",
        "OPHTHALMOLOGY",
        "ORTHOPAEDIC SURGERY",
        "OTORHINOLARYNGOLOGY (ENT)",
        "PLASTIC SURGERY",
        "UROLOGY",
        "VASCULAR SURGERY",
    ],
}

spec_list = []
for field in sorted(SPECIALTIES_BY_FIELD.keys()):
  for spec in sorted(SPECIALTIES_BY_FIELD[field]):
    spec_list.append(spec)
SPECIALTY_DROPDOWN_OPTIONS = ["None"] + sorted(list(set(spec_list) - {"OTHERS", "Others"})) + ["Others"]

HOSPITAL_PACKAGE_BUNDLES = [
    "None",
    "Hospital Package Kit (ENDO/YAKAP)",
    "Hospital Package (GS Laparoscopic Cholecystectomy)",
    "Hospital Package (GS Laparoscopic Appendectomy)",
    "Hospital Package (GS Laparoscopic Herniorrhaphy)",
    "Hospital Package (GS Thyroidectomy)",
    "Hospital Package (GS Open Cholecystectomy)",
    "Hospital Package (GS Open Appendectomy)",
    "Hospital Package (GS Modified Radical Mastectomy)",
    "Hospital Package (GS Open Herniorrhaphy)",
    "Hospital Package (OB Hysteroscopy)",
    "Hospital Package (OB Laparoscopic Gynecology)",
    "Hospital Package (OB Cesarean Section)",
    "Hospital Package (OB TAHBSO)",
    "Hospital Package (OB Exploratory Laparotomy)",
    "Hospital Package (OB D&C/Pregnant)",
    "Hospital Package (OB D&C/Non-Pregnant)",
    "Hospital Package (OB Normal Spontaneous Delivery)",
]

# Master Complete Annex B Database (110 Pages)
ANNEX_B_CATEGORIZED_PROCEDURES = {
    "SKIN & SUBCUTANEOUS TISSUES": [
        "10060 - INCISION AND DRAINAGE OF ABSCESS (CARBUNCLE/CYST) [₱7,098.00]",
        "10080 - INCISION AND DRAINAGE OF PILONIDAL CYST [₱7,098.00]",
        "10120 - INCISION AND REMOVAL OF FOREIGN BODY, SUBCUTANEOUS [₱7,098.00]",
        "10140 - INCISION AND DRAINAGE OF HEMATOMA, SEROMA, OR FLUID COLLECTION [₱7,098.00]",
        "10160 - PUNCTURE ASPIRATION OF ABSCESS, HEMATOMA BULLA OR CYST [₱7,098.00]",
        "10180 - INCISION AND DRAINAGE, COMPLEX, POSTOPERATIVE WOUND INFECTION [₱10,842.00]",
        "11000 - DEBRIDEMENT OF EXTENSIVE ECZEMATOUS OR INFECTED SKIN [₱20,553.00]",
        "11400 - EXCISION, BENIGN LESION, TRUNK, ARMS OR LEGS [₱7,098.00]",
        "11600 - EXCISION, MALIGNANT LESION, TRUNK, ARMS, OR LEGS [₱10,842.00]",
        "12001 - SIMPLE REPAIR OF SUPERFICIAL WOUNDS [₱7,098.00]",
        "14000 - ADJACENT TISSUE TRANSFER OR REARRANGEMENT / FLAPS [₱23,634.00]",
        "15100 - SPLIT GRAFT / FULL THICKNESS GRAFT [₱16,107.00]",
        "15820 - BLEPHAROPLASTY, LOWER EYELID [₱19,734.00]",
        "15822 - BLEPHAROPLASTY, UPPER EYELID [₱19,734.00]",
        "16035 - ESCHAROTOMY [₱59,943.00]",
    ],
    "MUSCULOSKELETAL SYSTEM": [
        "20220 - BIOPSY BONE, TROCAR, OR NEEDLE SUPERFICIAL [₱21,216.00]",
        "20610 - ARTHROCENTESIS, ASPIRATION AND/OR INJECTION, MAJOR JOINT [₱18,135.00]",
        "20680 - REMOVAL OF IMPLANT DEEP (PIN, SCREW, PLATE) [₱23,361.00]",
        "20802 - REPLANTATION, ARM, COMPLETE AMPUTATION [₱18,135.00]",
        "20805 - REPLANTATION, FOREARM, COMPLETE AMPUTATION [₱78,624.00]",
        "21315 - CLOSED / OPEN TREATMENT OF NASAL BONE FRACTURE [₱20,553.00]",
        "22554 - ARTHRODESIS, ANTERIOR INTERBODY TECHNIQUE, CERVICAL [₱104,130.00]",
        "23410 - REPAIR OF RUPTURED ROTATOR CUFF [₱40,911.00]",
        "27130 - TOTAL HIP REPLACEMENT [₱104,130.00]",
        "27447 - TOTAL KNEE REPLACEMENT [₱78,624.00]",
        "29881 - ARTHROSCOPY, KNEE, SURGICAL W/MENISCECTOMY [₱59,943.00]",
    ],
    "EYE AND OCULAR ADNEXA (OPHTHALMOLOGY)": [
        "65205 - REMOVAL OF FOREIGN BODY FROM EXTERNAL EYE, CONJUNCTIVAL [₱3,500.00]",
        "65220 - REMOVAL OF FOREIGN BODY FROM CORNEA W/O SLIT LAMP [₱4,200.00]",
        "65430 - CORNEAL SMEAR OR SCRAPING FOR MICROBIOLOGICAL EXAMINATION [₱3,800.00]",
        "65710 - KERATOPLASTY (CORNEAL TRANSPLANT) [₱45,000.00]",
        "66170 - TRABECULECTOMY AB EXTERNO IN GLAUCOMA SURGERY [₱25,600.00]",
        "66820 - DISCISSION OF SECONDARY CATARACT (NEEDLING METHOD) [₱12,500.00]",
        "66984 - EXTRACAPSULAR CATARACT EXTRACTION W/ IOL IMPLANTATION (PHACOEMULSIFICATION) [₱16,000.00]",
        "67036 - VITRECTOMY, MECHANICAL, PARS PLANA APPROACH [₱38,000.00]",
        "67107 - REPAIR OF RETINAL DETACHMENT W/ SCLERAL BUCKLING [₱32,000.00]",
        "67311 - STRABISMUS SURGERY, RECESSION OR RESECTION, ONE HORIZONTAL MUSCLE [₱14,500.00]",
        "67800 - EXCISION OF CHALAZION, SINGLE [₱5,200.00]",
        "67904 - REPAIR OF BLEPHAROPTOSIS (PTOSIS REPAIR) [₱18,200.00]",
        "68100 - BIOPSY OF CONJUNCTIVA [₱6,000.00]",
        "68400 - INCISION, DRAINAGE OF LACRIMAL GLAND [₱7,500.00]",
        "68810 - PROBING OF NASOLACRIMAL DUCT, W/ OR W/O IRRIGATION [₱8,400.00]",
    ],
    "RESPIRATORY SYSTEM": [
        "30110 - EXCISION, NASAL POLYP(S) [₱15,639.00]",
        "30520 - SEPTOPLASTY OR SUBMUCOUS RESECTION [₱25,155.00]",
        "31231 - NASAL ENDOSCOPY, DIAGNOSTIC [₱20,553.00]",
        "31622 - BRONCHOSCOPY DIAGNOSTIC [₱21,372.00]",
        "32440 - REMOVAL OF LUNG, TOTAL PNEUMONECTOMY [₱90,675.00]",
        "32480 - LOBECTOMY / SEGMENTECTOMY [₱80,262.00]",
    ],
    "CARDIOVASCULAR SYSTEM": [
        "33208 - INSERTION OF PERMANENT PACEMAKER (ATRIAL & VENTRICULAR) [₱41,730.00]",
        "33405 - REPLACEMENT AORTIC VALVE [₱104,130.00]",
        "33430 - REPLACEMENT, MITRAL VALVE [₱90,675.00]",
        "33510 - CORONARY ARTERY BYPASS GRAFT (CABG), VEIN ONLY [₱104,130.00]",
        "34201 - EMBOLECTOMY OR THROMBECTOMY, EXTREMITY ARTERY [₱45,435.00]",
        "36821 - ARTERIOVENOUS ANASTOMOSIS (AV FISTULA) [₱18,915.00]",
    ],
    "HEMIC AND LYMPHATIC SYSTEMS": [
        "38100 - SPLENECTOMY TOTAL [₱59,943.00]",
        "38120 - LAPAROSCOPY, SURGICAL SPLENECTOMY [₱59,943.00]",
        "38240 - BONE MARROW OR PERIPHERAL STEM CELL TRANSPLANTATION [₱73,710.00]",
        "38500 - BIOPSY OR EXCISION OF LYMPH NODE(S) SUPERFICIAL [₱11,076.00]",
        "38720 - CERVICAL LYMPHADENECTOMY (COMPLETE) [₱59,085.00]",
    ],
    "DIGESTIVE SYSTEM": [
        "43235 - UPPER GASTROINTESTINAL ENDOSCOPY (DIAGNOSTIC / EGD) [₱20,553.00]",
        "43239 - EGD W/ BIOPSY [₱20,553.00]",
        "43260 - ERCP DIAGNOSTIC [₱40,911.00]",
        "44950 - APPENDECTOMY (OPEN OR LAPAROSCOPIC) [₱46,800.00]",
        "44970 - LAPAROSCOPY, SURGICAL APPENDECTOMY [₱46,800.00]",
        "47562 - LAPAROSCOPY, SURGICAL CHOLECYSTECTOMY [₱60,450.00]",
        "47600 - CHOLECYSTECTOMY (OPEN) [₱60,450.00]",
        "48150 - WHIPPLE PROCEDURE (PANCREATODUODENECTOMY) [₱114,660.00]",
        "49505 - REPAIR INITIAL INGUINAL HERNIA [₱40,950.00]",
        "49560 - REPAIR INITIAL INCISIONAL HERNIA [₱40,950.00]",
    ],
    "URINARY SYSTEM": [
        "50080 - PERCUTANEOUS NEPHROSTOLITHOTOMY (PCNL) [₱59,085.00]",
        "50220 - NEPHRECTOMY, SIMPLE OR RADICAL [₱52,884.00]",
        "50360 - RENAL ALLOTRANSPLANTATION (KIDNEY TRANSPLANT) [₱90,675.00]",
        "51530 - CYSTOTOMY FOR EXCISION OF BLADDER TUMOR [₱52,884.00]",
        "52000 - CYSTOURETHROSCOPY [₱16,107.00]",
        "52601 - TRANSURETHRAL RESECTION OF PROSTATE (TURP) [₱73,710.00]",
    ],
    "MALE GENITAL SYSTEM": [
        "54150 - CIRCUMCISION, SURGICAL / CLAMP [₱2,457.00]",
        "54520 - ORCHIECTOMY, SIMPLE [₱20,553.00]",
        "54640 - ORCHIOPEXY, INGUINAL APPROACH [₱20,553.00]",
        "55040 - EXCISION OF HYDROCELE UNILATERAL [₱18,915.00]",
        "55250 - VASECTOMY, UNILATERAL OR BILATERAL [₱7,800.00]",
        "55840 - PROSTATECTOMY, RETROPUBIC RADICAL [₱90,675.00]",
    ],
    "FEMALE GENITAL SYSTEM": [
        "56620 - VULVECTOMY SIMPLE / RADICAL [₱23,634.00]",
        "57240 - ANTERIOR COLPORRHAPHY (CYSTOCELE REPAIR) [₱40,911.00]",
        "57250 - POSTERIOR COLPORRHAPHY (RECTOCELE REPAIR) [₱40,911.00]",
        "58120 - DILATION AND CURETTAGE (D&C) [₱21,450.00]",
        "58150 - TOTAL ABDOMINAL HYSTERECTOMY (TAHBSO) [₱58,500.00]",
        "58260 - VAGINAL HYSTERECTOMY [₱59,085.00]",
        "58558 - HYSTEROSCOPY W/ ENDOMETRIAL SAMPLING / POLYPECTOMY [₱25,155.00]",
        "58600 - LIGATION OR TRANSECTION OF FALLOPIAN TUBES [₱7,800.00]",
        "59100 - HYSTEROTOMY, ABDOMINAL [₱45,435.00]",
        "59510 - CESAREAN SECTION PROCEDURES [₱19,734.00]",
    ],
}

GNU_SHEET_HEADER = [
    "MONTH",
    "DATE",
    "TIME",
    "ROOM NO",
    "LAST NAME",
    "FIRST NAME",
    "MIDDLE NAME",
    "SEX",
    "AGE",
    "DIAGNOSIS",
    "ATTENDING PHYSICIAN",
    "ATTENDING SPECIALIZATION",
    "CO-MANAGEMENT PHYSICIAN",
    "CO-MANAGEMENT SPECIALIZATION",
    "HOSPITALIZATION MODE",
    "MODE OF PAYMENT",
    "PATIENT STATUS",
    "PROCEDURES",
    "DIAGNOSTIC EXAMINATIONS",
    "MEDICATIONS",
    "SPECIAL ENDORSEMENTS",
    "CASE COUNT",
    "SEEDED_TRIAL",
]

SCU_SHEET_HEADER = [
    "MONTH",
    "DATE",
    "LAST NAME",
    "FIRST NAME",
    "MIDDLE NAME",
    "SEX",
    "AOG",
    "AGE",
    "DIAGNOSIS",
    "DIAGNOSIS CATEGORY",
    "ADMITTED FROM",
    "ADMITTED TO",
    "TRANSFERRED TO",
    "ATTENDING PHYSICIAN",
    "ATTENDING SPECIALIZATION",
    "CO-MANAGEMENT PHYSICIAN",
    "CO-MANAGEMENT SPECIALIZATION",
    "HOSPITALIZATION MODE",
    "MODE OF PAYMENT",
    "PATIENT STATUS",
    "PROCEDURES",
    "DIAGNOSTIC EXAMINATIONS",
    "MEDICATIONS",
    "SPECIAL ENDORSEMENTS",
    "CASE COUNT",
    "SEEDED_TRIAL",
]

ECC_SHEET_HEADER = [
    "MONTH",
    "DATE",
    "TIME",
    "ROOM NO",
    "LAST NAME",
    "FIRST NAME",
    "MIDDLE NAME",
    "SEX",
    "AGE",
    "DIAGNOSIS",
    "DISEASE CATEGORY",
    "ATTENDING PHYSICIAN",
    "ATTENDING SPECIALIZATION",
    "CO-MANAGEMENT PHYSICIAN",
    "CO-MANAGEMENT SPECIALIZATION",
    "HOSPITALIZATION MODE",
    "CASE TYPE",
    "MODE OF PAYMENT",
    "ADMITTED TO",
    "PROCEDURES",
    "DIAGNOSTIC EXAMINATIONS",
    "MEDICATIONS",
    "SPECIAL ENDORSEMENTS",
    "CASE COUNT",
    "SEEDED_TRIAL",
]

HDU_SHEET_HEADER = [
    "MONTH",
    "DATE",
    "TRUE DATE",
    "LAST NAME",
    "FIRST NAME",
    "MIDDLE NAME",
    "SEX",
    "AGE",
    "DIAGNOSIS",
    "ATTENDING PHYSICIAN",
    "ATTENDING SPECIALIZATION",
    "CO-MANAGEMENT PHYSICIAN",
    "CO-MANAGEMENT SPECIALIZATION",
    "DIALYSIS SHIFT SLOT",
    "HOSPITALIZATION MODE",
    "MODE OF PAYMENT",
    "PATIENT STATUS",
    "PROCEDURES",
    "DIAGNOSTIC EXAMINATIONS",
    "MEDICATIONS",
    "SPECIAL ENDORSEMENTS",
    "CASE COUNT",
    "SEEDED_TRIAL",
]

SHEET_HEADERS = {
    "Emergency Care Complex (ECC)": ECC_SHEET_HEADER,
    "Endoscopy Unit (ENDO)": [
        "MONTH",
        "DATE",
        "SCHEDULED TIME",
        "ACTUAL TIME",
        "LAST NAME",
        "FIRST NAME",
        "MIDDLE NAME",
        "SEX",
        "AGE",
        "DIAGNOSIS",
        "PROCEDURE",
        "PROCEDURE CATEGORY",
        "HOSPITAL PACKAGE BUNDLE",
        "PHILHEALTH CASE RATE (RVS CODE)",
        "ATTENDING PHYSICIAN",
        "ATTENDING SPECIALIZATION",
        "CO-MANAGEMENT PHYSICIAN",
        "CO-MANAGEMENT SPECIALIZATION",
        "SURGEON / PROCEDURALIST",
        "SURGEON SPECIALIZATION",
        "ANESTHESIOLOGIST",
        "ANESTHESIOLOGIST SPECIALIZATION",
        "PROCEDURE COMPLEXITY",
        "HOSPITALIZATION MODE",
        "MODE OF PAYMENT",
        "PATIENT STATUS",
        "CASE COUNT",
        "SEEDED_TRIAL",
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
    "Hemodialysis Unit (HDU)": HDU_SHEET_HEADER,
    "OBGYNE Care Complex (LRDR-OB Surgery)": [
        "MONTH",
        "DATE",
        "SCHEDULED TIME",
        "ACTUAL TIME",
        "LAST NAME",
        "FIRST NAME",
        "MIDDLE NAME",
        "SEX",
        "AGE",
        "PRE-OP DIAGNOSIS",
        "POST-OP DIAGNOSIS",
        "PROCEDURE NAME",
        "SURGICAL PROCEDURE",
        "PROCEDURE CATEGORY",
        "HOSPITAL PACKAGE BUNDLE",
        "PHILHEALTH CASE RATE (RVS CODE)",
        "ATTENDING PHYSICIAN",
        "ATTENDING SPECIALIZATION",
        "CO-MANAGEMENT PHYSICIAN",
        "CO-MANAGEMENT SPECIALIZATION",
        "SURGEON / OBGYNE",
        "SURGEON SPECIALIZATION",
        "ANESTHESIOLOGIST",
        "ANESTHESIOLOGIST SPECIALIZATION",
        "PROCEDURE COMPLEXITY",
        "HOSPITALIZATION MODE",
        "MODE OF PAYMENT",
        "PATIENT STATUS",
        "CASE COUNT",
        "SEEDED_TRIAL",
    ],
    "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)": SCU_SHEET_HEADER,
    "Surgical Care Complex (OR Main)": [
        "MONTH",
        "DATE",
        "SCHEDULED TIME",
        "ACTUAL TIME",
        "LAST NAME",
        "FIRST NAME",
        "MIDDLE NAME",
        "SEX",
        "AGE",
        "PRE-OP DIAGNOSIS",
        "POST-OP DIAGNOSIS",
        "PROCEDURE",
        "PROCEDURE CATEGORY",
        "HOSPITAL PACKAGE BUNDLE",
        "PHILHEALTH CASE RATE (RVS CODE)",
        "ATTENDING PHYSICIAN",
        "ATTENDING SPECIALIZATION",
        "CO-MANAGEMENT PHYSICIAN",
        "CO-MANAGEMENT SPECIALIZATION",
        "PRIMARY SURGEON",
        "SURGEON SPECIALIZATION",
        "ANESTHESIOLOGIST",
        "ANESTHESIOLOGIST SPECIALIZATION",
        "PROCEDURE COMPLEXITY",
        "HOSPITALIZATION MODE",
        "MODE OF PAYMENT",
        "PATIENT STATUS",
        "CASE COUNT",
        "SEEDED_TRIAL",
    ],
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
# HYBRID SQLITE BACKEND & LOCAL-FIRST INSTANT READ ARCHITECTURE
# ---------------------------------------------------------
sqlite_lock = threading.Lock()


def get_sqlite_conn():
  conn = sqlite3.connect(
      "hospital_local.sqlite", check_same_thread=False, timeout=30.0
  )
  conn.execute("PRAGMA journal_mode=WAL;")
  return conn


def init_local_sqlite():
  conn = get_sqlite_conn()
  cursor = conn.cursor()
  for s_name, cols in SHEET_HEADERS.items():
    cols_def = ", ".join([f'"{col}" TEXT' for col in cols])
    cursor.execute(f'CREATE TABLE IF NOT EXISTS "{s_name}" ({cols_def})')
    try:
      cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{s_name.replace(" ", "_")}_names ON "{s_name}" ("LAST NAME", "FIRST NAME")')
    except Exception:
      pass

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS "System Audit Logs" (
            TIMESTAMP TEXT,
            USERNAME TEXT,
            ROLE TEXT,
            ACTION TEXT,
            DEPARTMENT TEXT,
            DETAILS TEXT
        )
    """)

  cursor.execute("""
        CREATE TABLE IF NOT EXISTS "Sync_Queue" (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet_name TEXT,
            row_json TEXT,
            is_update INTEGER,
            df_pickle BLOB,
            retries INTEGER DEFAULT 0
        )
    """)
  try:
    cursor.execute('ALTER TABLE "Sync_Queue" ADD COLUMN retries INTEGER DEFAULT 0')
  except Exception:
    pass

  conn.commit()
  conn.close()


init_local_sqlite()


def log_audit_event(action, department, details):
  conn = get_sqlite_conn()
  cursor = conn.cursor()
  ts = get_ph_time().strftime("%Y-%m-%d %I:%M %p")
  username = st.session_state.get("username", "system")
  role = st.session_state.get("role", "system")
  cursor.execute(
      """
        INSERT INTO "System Audit Logs" (TIMESTAMP, USERNAME, ROLE, ACTION, DEPARTMENT, DETAILS)
        VALUES (?, ?, ?, ?, ?, ?)
    """,
      (ts, username, role, action, department, details),
  )
  conn.commit()
  conn.close()


def sync_df_to_sqlite(sheet_name, df):
  if df is None or df.empty:
    return
  conn = get_sqlite_conn()
  try:
    df.to_sql(sheet_name, conn, if_exists="replace", index=False)
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

  scope = [
      "https://www.googleapis.com/auth/spreadsheets",
      "https://www.googleapis.com/auth/drive",
  ]
  if "gcp_service_account" not in st.secrets:
    return None
  try:
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
      pk = (
          str(creds_dict["private_key"])
          .strip("'\" \n\r")
          .replace("\\n", "\n")
      )
      if (
          "-----BEGIN PRIVATE KEY-----" in pk
          and "-----END PRIVATE KEY-----" in pk
      ):
        pk = pk[
            pk.find("-----BEGIN PRIVATE KEY-----") : pk.find(
                "-----END PRIVATE KEY-----"
            )
            + len("-----END PRIVATE KEY-----")
        ]
      creds_dict["private_key"] = pk
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
  except Exception:
    return None
  client = gspread.authorize(creds)
  try:
    sh = client.open("MTCMC_CENSUS_MASTERFILES_SYSTEM")
  except gspread.SpreadsheetNotFound:
    sh = client.create("MTCMC_CENSUS_MASTERFILES_SYSTEM")
  return sh


sh = init_google_sheets()


def get_queue_size():
  conn = get_sqlite_conn()
  cursor = conn.cursor()
  cursor.execute('SELECT COUNT(*) FROM "Sync_Queue"')
  count = cursor.fetchone()[0]
  conn.close()
  return count


def background_durable_sync_worker():
  while True:
    if sh is None:
      py_time.sleep(5)
      continue
    conn = get_sqlite_conn()
    try:
      cursor = conn.cursor()
      cursor.execute(
          'SELECT id, sheet_name, row_json, is_update, df_pickle, retries FROM "Sync_Queue"'
          " ORDER BY id ASC LIMIT 1"
      )
      row = cursor.fetchone()
      if not row:
        conn.close()
        py_time.sleep(2)
        continue

      task_id, sheet_name, row_json, is_update, df_pickle, retries = row
      conn.close()

      def _do_sync():
        ws = sh.worksheet(sheet_name)
        if is_update:
          df = pickle.loads(df_pickle) if df_pickle else pd.DataFrame()
          ws.clear()
          headers = SHEET_HEADERS.get(sheet_name, df.columns.tolist())
          ws.update("A1", [[f"MTCMC CLINICAL CENSUS - {sheet_name} MASTERFILE"]])
          ws.update("A4", [headers])
          rows_to_update = []
          for _, r_val in df.iterrows():
            mapped_vals = []
            for h in headers:
              if h in r_val:
                v = r_val[h]
                mapped_vals.append(
                    "" if (v is None or pd.isna(v)) else str(v).upper()
                )
              else:
                mapped_vals.append("")
            rows_to_update.append(mapped_vals)
          if rows_to_update:
            ws.update("A5", rows_to_update)
        else:
          row_dict = json.loads(row_json) if row_json else {}
          headers = ws.row_values(4)
          if not headers:
            headers = SHEET_HEADERS.get(sheet_name, [])
            ws.update("A4", [headers])
          row_values = []
          for h in headers:
            val = row_dict.get(h, "")
            row_values.append(
                "" if (val is None or pd.isna(val)) else str(val).upper()
            )
          ws.append_row(row_values)

      safe_gspread_call(sheet_name, _do_sync)

      conn_del = get_sqlite_conn()
      conn_del.execute('DELETE FROM "Sync_Queue" WHERE id = ?', (task_id,))
      conn_del.commit()
      conn_del.close()

      st.session_state["sync_health_status"] = (
          f"Healthy (Last synced: {get_ph_time().strftime('%I:%M:%S %p')})"
      )
    except Exception as e:
      try:
        conn.close()
      except:
        pass
      conn_retry = get_sqlite_conn()
      cursor_r = conn_retry.cursor()
      cursor_r.execute('SELECT retries FROM "Sync_Queue" WHERE id = ?', (task_id,))
      r_res = cursor_r.fetchone()
      current_retries = r_res[0] if r_res else 0

      if current_retries >= 2:
        cursor_r.execute('DELETE FROM "Sync_Queue" WHERE id = ?', (task_id,))
        conn_retry.commit()
        log_audit_event("SYNC_FAIL", sheet_name, f"Dropped task after 3 failed sync attempts: {str(e)}")
      else:
        cursor_r.execute('UPDATE "Sync_Queue" SET retries = retries + 1 WHERE id = ?', (task_id,))
        conn_retry.commit()
      conn_retry.close()

      st.session_state["sync_health_status"] = f"Sync Error (Retry {current_retries+1}/3): {str(e)}"
      py_time.sleep(5)


durable_sync_thread = threading.Thread(
    target=background_durable_sync_worker, daemon=True
)
durable_sync_thread.start()


def ensure_google_sheets_exist():
  if sh is None:
    return
  try:
    existing_worksheets = [ws.title for ws in sh.worksheets()]
  except Exception:
    existing_worksheets = []
  if "Hospital Information System" not in existing_worksheets:
    try:
      ws_sum = sh.add_worksheet(
          title="Hospital Information System", rows=100, cols=4
      )
      ws_sum.update(
          "A1:D1",
          [["MOTHER TERESA OF CALCUTTA MEDICAL CENTER", "", "", ""]],
      )
      ws_sum.update(
          "A4:D4",
          [[
              "Department / Module",
              "Total Census Records",
              "Daily Patient Census",
              "Monthly Patient Census",
          ]],
      )
    except Exception:
      pass
  for s_name, cols in SHEET_HEADERS.items():
    if s_name not in existing_worksheets:
      try:
        ws = sh.add_worksheet(title=s_name, rows=1000, cols=len(cols))
        ws.update("A1", [[f"MTCMC CLINICAL CENSUS - {s_name} MASTERFILE"]])
        ws.update("A4", [cols])
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
  global sh
  if sh is None:
    sh = init_google_sheets()
  if sh is None:
    return None
  max_retries = 3
  backoff = 1
  target_lock = get_sheet_lock(sheet_name)
  for attempt in range(max_retries):
    with target_lock:
      try:
        return func(*args, **kwargs)
      except Exception as e:
        if attempt == max_retries - 1:
          try:
            sh = init_google_sheets()
            if sh:
              return func(*args, **kwargs)
          except Exception:
            raise e
        py_time.sleep(backoff)
        backoff *= 2
  return None


def append_record_to_google_sheet(sheet_name, row_dict):
  ensure_google_sheets_exist()
  conn = get_sqlite_conn()
  df_curr = read_sqlite_sheet(sheet_name)
  df_new = pd.DataFrame([row_dict])
  df_combined = pd.concat([df_curr, df_new], ignore_index=True)
  sync_df_to_sqlite(sheet_name, df_combined)
  conn.close()

  conn_q = get_sqlite_conn()
  conn_q.execute(
      'INSERT INTO "Sync_Queue" (sheet_name, row_json, is_update, df_pickle, retries)'
      " VALUES (?, ?, ?, ?, 0)",
      (sheet_name, json.dumps(row_dict), 0, None),
  )
  conn_q.commit()
  conn_q.close()

  log_audit_event(
      "INSERT",
      sheet_name,
      f"Added record for {row_dict.get('LAST NAME', '')}",
  )
  st.toast("Record saved instantly (Local-First). Background sync queued.", icon="💾")
  return True


def update_google_sheet_from_df(sheet_name, df):
  ensure_google_sheets_exist()
  sync_df_to_sqlite(sheet_name, df)

  conn_q = get_sqlite_conn()
  conn_q.execute(
      'INSERT INTO "Sync_Queue" (sheet_name, row_json, is_update, df_pickle, retries)'
      " VALUES (?, ?, ?, ?, 0)",
      (sheet_name, None, 1, pickle.dumps(df)),
  )
  conn_q.commit()
  conn_q.close()

  log_audit_event(
      "UPDATE", sheet_name, f"Updated sheet rows count: {len(df)}"
  )
  st.toast("Changes saved instantly (Local-First). Background sync queued.", icon="💾")
  return True


@st.cache_data(ttl=3600)
def fetch_cloud_sheet(sheet_name):
  if sh is None:
    return pd.DataFrame()
  ensure_google_sheets_exist()

  def _get_data():
    ws = sh.worksheet(sheet_name)
    return ws.get("A4:V2000")

  try:
    data = safe_gspread_call(sheet_name, _get_data)
    if data and len(data) >= 1:
      headers = [str(h).strip().upper() for h in data[0]]
      rows = data[1:]
      if rows:
        df_res = pd.DataFrame(rows, columns=headers[: len(rows[0])])
        expected_cols = SHEET_HEADERS.get(sheet_name, [])
        for col in expected_cols:
          if col not in df_res.columns:
            df_res[col] = ""
        return df_res
  except Exception:
    pass
  return pd.DataFrame()


def read_google_sheet(sheet_name, force_refresh=False):
  """Local-First Instant Reader: Reads strictly from local SQLite for instant loading (<0.1s)."""
  if not force_refresh and sheet_name in st.session_state["df_cache"]:
    return st.session_state["df_cache"][sheet_name]

  df = read_sqlite_sheet(sheet_name)
  if df.empty and sh is not None:
    df = fetch_cloud_sheet(sheet_name)
    if not df.empty:
      sync_df_to_sqlite(sheet_name, df)

  st.session_state["df_cache"][sheet_name] = df
  return df


def read_multiple_sheets_parallel(sheet_names):
  return {s: read_google_sheet(s) for s in sheet_names}


def check_existing_patient_ai(sheet_name, last_name, fn, curr_date_str):
  df = read_google_sheet(sheet_name)
  if df.empty or "LAST NAME" not in df.columns:
    return None
  ln = str(last_name).strip().upper()
  first = str(fn).strip().upper()
  if not ln or not first:
    return None
  matches = df[
      (df["LAST NAME"].astype(str).str.strip().str.upper() == ln)
      & (df["FIRST NAME"].astype(str).str.strip().str.upper() == first)
  ]
  if matches.empty:
    return None
  same_date_match = matches[
      matches["DATE"].astype(str).str.strip() == curr_date_str
  ]
  if not same_date_match.empty:
    return same_date_match.iloc[-1].to_dict()
  return None


ensure_google_sheets_exist()


def clean_display_df(df):
  if df is None or df.empty:
    return df
  d_clean = df.copy()
  cols_to_drop = [c for c in d_clean.columns if "Unnamed" in str(c) or c == ""]
  if cols_to_drop:
    d_clean = d_clean.drop(columns=cols_to_drop)
  if d_clean.shape[1] > 1:
    first_col = d_clean.columns[0]
    if first_col.lower() in ["index", "level_0", "unnamed: 0"]:
      d_clean = d_clean.iloc[:, 1:]
  return d_clean


def get_editor_column_config(columns, is_historical=True):
  config = {}
  for col in columns:
    col_upper = str(col).upper()
    if is_historical and col_upper in [
        "DATE",
        "TRUE DATE",
        "ADMISSION DATE",
        "DEPARTMENT / UNIT",
        "LAST NAME",
        "FIRST NAME",
        "MIDDLE NAME",
        "SEX",
        "AGE",
        "DIAGNOSIS",
        "ATTENDING PHYSICIAN",
    ]:
      config[col] = st.column_config.TextColumn(
          col, disabled=True, width="small"
      )
    elif col_upper in ["PATIENT STATUS", "STATUS"]:
      config[col] = st.column_config.SelectboxColumn(
          col, options=["ACTIVE", "MGH", "DISCHARGED", "CAB"], width="medium"
      )
    elif col_upper == "SEX":
      config[col] = st.column_config.SelectboxColumn(
          col, options=["FEMALE", "MALE", "OTHERS"], width="small"
      )
    elif col_upper == "MODE OF PAYMENT":
      config[col] = st.column_config.SelectboxColumn(
          col, options=["HMO", "PHIC", "SELF-PAY"], width="medium"
      )
    elif col_upper == "HOSPITALIZATION MODE":
      config[col] = st.column_config.SelectboxColumn(
          col, options=["INPATIENT", "OUTPATIENT"], width="medium"
      )
    else:
      config[col] = st.column_config.TextColumn(col, width="medium")
  return config


def display_paginated_dataframe(df, key_prefix="pag", is_historical=True):
  if df is None or df.empty:
    st.info("No records to display.")
    return df

  clean_df = clean_display_df(df)
  total_rows = len(clean_df)
  editor_config = get_editor_column_config(
      clean_df.columns, is_historical=is_historical
  )

  if total_rows <= 100:
    return st.data_editor(
        clean_df,
        use_container_width=True,
        num_rows="fixed",
        key=f"{key_prefix}_editor",
        column_config=editor_config,
    )

  st.markdown(
      f"**Total Records:** `{total_rows}` (Showing 100 records per page for"
      " optimal performance)"
  )
  page_size = 100
  total_pages = (total_rows - 1) // page_size + 1
  page_num = st.selectbox(
      "Select Page", range(1, total_pages + 1), key=f"{key_prefix}_page_sel"
  )

  start_idx = (page_num - 1) * page_size
  end_idx = min(start_idx + page_size, total_rows)
  page_df = clean_df.iloc[start_idx:end_idx].copy()

  edited_page = st.data_editor(
      page_df,
      use_container_width=True,
      num_rows="fixed",
      key=f"{key_prefix}_editor_p{page_num}",
      column_config=editor_config,
  )

  full_df = clean_df.copy()
  full_df.iloc[start_idx:end_idx] = edited_page
  return full_df


# ---------------------------------------------------------
# UI HEADER & SIDEBAR NAVIGATION
# ---------------------------------------------------------
st.markdown(
    """
<style>
    .header-container { display: flex; align-items: center; gap: 20px; margin-bottom: 5px; }
    .header-logo { width: 85px; height: 85px; object-fit: contain; flex-shrink: 0; }
    .header-text-group { display: flex; flex-direction: column; justify-content: center; }
    .header-title { margin: 0px !important; line-height: 1.0 !important; font-size: 2.35rem !important; color: #1e3a8a !important; font-weight: 800 !important; }
    .header-subtitle { margin: -4px 0px 0px 0px !important; font-size: 1.15rem !important; color: #0f766e !important; font-weight: 600 !important; letter-spacing: 0.5px !important; }
</style>
""",
    unsafe_allow_html=True,
)

logo_path_found = ""
for logo_filename in [
    "logo_3.jpg",
    "logo_3.png",
    "logo.png",
    "logo_2.png",
    "assets/logo_3.jpg",
    "assets/logo_3.png",
]:
  if os.path.exists(logo_filename):
    logo_path_found = logo_filename
    break

if logo_path_found:
  img_base64 = base64.b64encode(open(logo_path_found, "rb").read()).decode()
  logo_html = (
      f'<img src="data:image/jpeg;base64,{img_base64}" class="header-logo">'
  )
else:
  logo_html = '<div style="background-color: #1e3a8a; width: 85px; height: 85px; border-radius: 12px; display: flex; align-items: center; justify-content: center;"><span style="color: white; font-size: 34px; font-weight: bold;">✚</span></div>'

st.markdown(
    f"""
    <div class="header-container">
        {logo_html}
        <div class="header-text-group">
            <h1 class="header-title">MOTHER TERESA OF CALCUTTA MEDICAL CENTER</h1>
            <p class="header-subtitle">Touching Lives Through Expert Care</p>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(f"**Logged in as:** {st.session_state['name']}")
st.sidebar.markdown(f"**Role:** `{st.session_state['role']}`")
ph_now_display = get_ph_time()
st.sidebar.markdown(
    f"**Date & Time:** `{ph_now_display.strftime('%B %d, %Y - %I:%M %p')}`"
)
st.sidebar.markdown("---")

# ---------------------------------------------------------
# ADMIN CONTROL CENTER & HEALTH MONITOR DASHBOARD
# ---------------------------------------------------------
if st.session_state["role"] == "Administrator":
  st.sidebar.markdown("### 🛠️ Admin Control Center")

  with st.sidebar.expander("🩺 System Health & Sync Status"):
    st.markdown(
        f"**Status:** `{st.session_state.get('sync_health_status', 'Idle')}`"
    )
    st.markdown(f"**Durable Queue Pending Tasks:** `{get_queue_size()}`")
    if st.button("View Audit Logs"):
      conn = get_sqlite_conn()
      audit_df = pd.read_sql(
          'SELECT * FROM "System Audit Logs" ORDER BY ROWID DESC LIMIT 50', conn
      )
      conn.close()
      st.dataframe(audit_df, use_container_width=True)

  with st.sidebar.expander("🤖 Admin Intelligent Seeder"):
    st.markdown(
        "Generate balanced, realistic multi-disciplinary patient records"
        " distributed evenly across all hospital units with advanced clinical"
        " variations."
    )
    batch_size = st.selectbox(
        "Records per Department", [5, 10, 20, 50], index=1
    )

    if st.button("🚀 Generate Balanced Batch", type="primary"):
      first_names = [
          "JUAN",
          "MARIA",
          "JOSE",
          "ANA",
          "PEDRO",
          "LUIS",
          "CARMEN",
          "ROSA",
          "BEATRICE",
          "CARLOS",
          "DANTE",
          "ELENA",
          "FERDINAND",
          "GRACE",
          "ISABELA",
          "JORGE",
      ]
      middle_names = [
          "SANTOS",
          "REYES",
          "GARCIA",
          "TORRES",
          "FLORES",
          "RAMOS",
          "DIZON",
          "SANTIA",
      ]
      last_names = [
          "CRUZ",
          "BAUTISTA",
          "OCAMPO",
          "MENDOZA",
          "GONZALES",
          "AQUINO",
          "VILLANUEVA",
          "SANTOS",
          "DEL ROSARIO",
      ]

      all_seeded_targets = [
          "Emergency Care Complex (ECC)",
          "Surgical Care Complex (OR Main)",
          "OBGYNE Care Complex (LRDR-OB Surgery)",
          "Endoscopy Unit (ENDO)",
          "Hemodialysis Unit (HDU)",
          "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
      ] + sorted(
          [d for d in sorted_departments if d.startswith("General Nursing Unit")]
      )

      clinical_scenarios = [
          {
              "condition": "ACUTE ST-SEGMENT ELEVATION MYOCARDIAL INFARCTION (STEMI)",
              "category": "CARDIOVASCULAR SYSTEM",
              "spec": "CARDIOLOGY",
              "treatment": "• PRIMARY PERCUTANEOUS CORONARY INTERVENTION (PCI) & HEPARINIZATION",
              "diags": "• 12-LEAD ECG, TROPONIN I, SERUM LIPID PROFILE, CBC",
              "meds": "• ASPIRIN 325MG, CLOPIDOGREL 300MG, ATORVASTATIN 80MG",
              "ends": "• PATIENT STABLE POST-PCI, TRANSFERRED TO CCU FOR CLOSE MONITORING",
              "hosp": "INPATIENT",
              "pay": "PHIC",
              "case_type": "PRIVATE CASE",
          },
          {
              "condition": "ACUTE APPENDICITIS WITH GENERALIZED PERITONITIS",
              "category": "DIGESTIVE SYSTEM",
              "spec": "GENERAL SURGERY",
              "treatment": "• EMERGENCY OPEN APPENDECTOMY & PERITONEAL LAVAGE",
              "diags": "• WHOLE ABDOMEN ULTRASOUND, COMPLETE BLOOD COUNT, CREATININE",
              "meds": "• PIPERACILLIN/TAZOBACTAM 4.5G IV Q8H, KETOROLAC 30MG IV PRN",
              "ends": "• WOUND CLEAN AND DRY, BOWEL SOUNDS NORMOACTIVE, FOR DISCHARGE EVAL",
              "hosp": "INPATIENT",
              "pay": "HMO",
              "case_type": "HOUSE CASE (WALK-IN)",
          },
          {
              "condition": "CHRONIC KIDNEY DISEASE STAGE 5 SECONDARY TO DIABETIC NEPHROPATHY",
              "category": "URINARY SYSTEM",
              "spec": "NEPHROLOGY",
              "treatment": "• BIPOLAR HEMODIALYSIS SESSION VIA PERMANENT AV FISTULA",
              "diags": "• PRE/POST HD CREATININE, BUN, SERUM ELECTROLYTES, CHEST X-RAY",
              "meds": "• INTRADIALYTIC EPOETIN ALFA 4000U, CALCIUM CARBONATE 500MG TID",
              "ends": "• AV FISTULA THRILL INTACT, ULTRAFILTRATION GOAL ACHIEVED",
              "outpatient": True,
              "hosp": "OUTPATIENT",
              "pay": "SELF-PAY",
              "case_type": "PRIVATE CASE",
          },
          {
              "condition": "FULL TERM PREGNANCY, CEPHALOPELVIC DISPROPORTION",
              "category": "FEMALE GENITAL SYSTEM",
              "spec": "OBSTETRICS & GYNAECOLOGY",
              "treatment": "• LOWER SEGMENT CESAREAN SECTION (LSCS) UNDER SPINAL ANESTHESIA",
              "diags": "• OBSTETRIC ULTRASOUND, CBC, BLOOD TYPING & CROSSMATCHING",
              "meds": "• OXYTOCIN 10IU DILUTED IN NACL 1L, CEFOTAXIME 1G IV Q8H",
              "ends": "• DELIVERED LIVE HEALTHY BABY BOY, UTERUS FIRM AND CONTRACTED",
              "hosp": "INPATIENT",
              "pay": "PHIC",
              "case_type": "PRIVATE CASE",
          },
          {
              "condition": "NEONATAL SEPSIS WITH HYPERBILIRUBINEMIA",
              "category": "RESPIRATORY SYSTEM",
              "spec": "NEONATOLOGY",
              "treatment": "• INTENSIVE PHOTOTHERAPY AND OXYGEN HOOD THERAPY",
              "diags": "• TOTAL AND DIRECT BILIRUBIN, CBC, BLOOD CULTURE AND SENSITIVITY",
              "meds": "• AMPICILLIN 100MG/KG/DAY, GENTAMICIN 4MG/KG/DAY IV",
              "ends": "• BILIRUBIN LEVELS TRENDING DOWN, FEEDING WELL ON FORMULA MILK",
              "hosp": "INPATIENT",
              "pay": "HMO",
              "case_type": "HOUSE CASE (WALK-IN)",
          },
          {
              "condition": "COMMUNITY ACQUIRED PNEUMONIA HIGH RISK (CLASS IV)",
              "category": "RESPIRATORY SYSTEM",
              "spec": "PULMONOLOGY",
              "treatment": "• OXYGEN THERAPY VIA NASAL CANNULA & BRONCHODILATOR NEBULIZATION",
              "diags": "• SERIAL CHEST X-RAY, ARB (ARTERIAL BLOOD GAS), SPUTUM GRAM STAIN",
              "meds": "• LEVOFLOXACIN 750MG IV ONCE DAILY, SALBUTAMOL/IPRATROPIUM NEBU",
              "ends": "• OXYGEN SATURATION MAINTAINED AT 98% ON ROOM AIR, COUGH PRODUCTIVE",
              "hosp": "INPATIENT",
              "pay": "SELF-PAY",
              "case_type": "PRIVATE CASE",
          },
          {
              "condition": "ACUTE CEREBROVASCULAR INFARCTION (ISCHEMIC STROKE)",
              "category": "MUSCULOSKELETAL SYSTEM",
              "spec": "NEUROLOGY",
              "treatment": "• NEUROLOGICAL MONITORING & BLOOD PRESSURE OPTIMIZATION",
              "diags": "• CRANIAL CT SCAN W/O CONTRAST, LIPID PROFILE, FASTING BLOOD SUGAR",
              "meds": "• ASPIRIN 80MG TAB OD, AMLODIPINE 10MG TAB OD, MANITOL INFUSION",
              "ends": "• GLASGOW COMA SCALE 14 (E4V4M6), RIGHT-SIDED WEAKNESS NOTED",
              "hosp": "INPATIENT",
              "pay": "PHIC",
              "case_type": "PRIVATE CASE",
          },
      ]

      total_tasks = len(all_seeded_targets) * batch_size
      progress_bar = st.sidebar.progress(0)
      completed_count = 0

      for target_dept in all_seeded_targets:
        for i in range(batch_size):
          scenario = clinical_scenarios[(completed_count + i) % len(clinical_scenarios)]

          fn = random.choice(first_names)
          mn = random.choice(middle_names)
          ln = random.choice(last_names)
          sex = "FEMALE" if "OBGYNE" in target_dept and i % 2 == 0 else random.choice(["FEMALE", "MALE"])
          age = str(random.randint(1, 85))

          date_str = ph_now_display.strftime("%m/%d/%Y")
          headers = SHEET_HEADERS.get(target_dept, [])
          row_data = {h: "" for h in headers}

          row_data["MONTH"] = get_month_str(
              ph_now_display.date(),
              (
                  "full_month"
                  if "General Nursing Unit" in target_dept
                  or target_dept == "Emergency Care Complex (ECC)"
                  else "numeric_prefix"
              ),
          )
          row_data["DATE"] = date_str
          row_data["LAST NAME"] = ln
          row_data["FIRST NAME"] = fn
          row_data["MIDDLE NAME"] = mn
          row_data["SEX"] = sex
          row_data["MODE OF PAYMENT"] = scenario["pay"]
          row_data["CASE COUNT"] = "1"
          row_data["SEEDED_TRIAL"] = "YES"

          if target_dept == "Emergency Care Complex (ECC)":
            row_data["TIME"] = f"{random.randint(1,12):02d}:{random.choice(['00','15','30','45'])} AM"
            row_data["ROOM NO"] = f"ECC-RM-{random.randint(1, 10)}"
            row_data["AGE"] = age
            row_data["DIAGNOSIS"] = scenario["condition"]
            row_data["DISEASE CATEGORY"] = scenario["spec"]
            row_data["ATTENDING PHYSICIAN"] = f"DR. {random.choice(['E. SANTOS', 'M. REYES', 'A. CRUZ'])}"
            row_data["ATTENDING SPECIALIZATION"] = scenario["spec"]
            row_data["CO-MANAGEMENT PHYSICIAN"] = "DR. J. BAUTISTA"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "INTERNAL MEDICINE"
            row_data["HOSPITALIZATION MODE"] = scenario["hosp"]
            row_data["CASE TYPE"] = scenario["case_type"]
            row_data["ADMITTED TO"] = random.choice(["GNU 1C", "GNU 2A", "PCN", "NICU"])
            row_data["PROCEDURES"] = scenario["treatment"]
            row_data["DIAGNOSTIC EXAMINATIONS"] = scenario["diags"]
            row_data["MEDICATIONS"] = scenario["meds"]
            row_data["SPECIAL ENDORSEMENTS"] = scenario["ends"]

          elif target_dept == "Surgical Care Complex (OR Main)":
            row_data["SCHEDULED TIME"] = "09:00 AM"
            row_data["ACTUAL TIME"] = "09:30 AM"
            row_data["AGE"] = float(age)
            row_data["PRE-OP DIAGNOSIS"] = scenario["condition"]
            row_data["POST-OP DIAGNOSIS"] = scenario["condition"]
            row_data["PROCEDURE"] = scenario["treatment"]
            row_data["PROCEDURE CATEGORY"] = scenario["category"]
            row_data["HOSPITAL PACKAGE BUNDLE"] = "Hospital Package (GS Laparoscopic Cholecystectomy)"
            row_data["PHILHEALTH CASE RATE (RVS CODE)"] = f"47562 - {scenario['condition']} [₱60,450.00]"
            row_data["ATTENDING PHYSICIAN"] = "DR. M. REYES"
            row_data["ATTENDING SPECIALIZATION"] = scenario["spec"]
            row_data["CO-MANAGEMENT PHYSICIAN"] = "N/A"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "N/A"
            row_data["PRIMARY SURGEON"] = "DR. J. BAUTISTA"
            row_data["SURGEON SPECIALIZATION"] = scenario["spec"]
            row_data["ANESTHESIOLOGIST"] = "DR. A. CRUZ"
            row_data["ANESTHESIOLOGIST SPECIALIZATION"] = "GENERAL ANAESTHESIOLOGY"
            row_data["PROCEDURE COMPLEXITY"] = "Major"
            row_data["HOSPITALIZATION MODE"] = scenario["hosp"]
            row_data["PATIENT STATUS"] = random.choice(["ACTIVE", "MGH", "CAB"])

          elif target_dept == "OBGYNE Care Complex (LRDR-OB Surgery)":
            row_data["SEX"] = "FEMALE"
            row_data["SCHEDULED TIME"] = "08:00 AM"
            row_data["ACTUAL TIME"] = "08:15 AM"
            row_data["AGE"] = float(age)
            row_data["PRE-OP DIAGNOSIS"] = "FULL TERM PREGNANCY, CEPHALOPELVIC DISPROPORTION"
            row_data["POST-OP DIAGNOSIS"] = "TERM PREGNANCY DELIVERED VIA PRIMARY LSCS"
            row_data["PROCEDURE NAME"] = "LOWER SEGMENT CESAREAN SECTION"
            row_data["SURGICAL PROCEDURE"] = scenario["treatment"]
            row_data["PROCEDURE CATEGORY"] = "FEMALE GENITAL SYSTEM"
            row_data["HOSPITAL PACKAGE BUNDLE"] = "Hospital Package (OB Cesarean Section)"
            row_data["PHILHEALTH CASE RATE (RVS CODE)"] = "59510 - CESAREAN SECTION PROCEDURES [₱19,734.00]"
            row_data["ATTENDING PHYSICIAN"] = "DR. R. OCAMPO"
            row_data["ATTENDING SPECIALIZATION"] = "OBSTETRICS & GYNAECOLOGY"
            row_data["CO-MANAGEMENT PHYSICIAN"] = "N/A"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "N/A"
            row_data["SURGEON / OBGYNE"] = "DR. R. OCAMPO"
            row_data["SURGEON SPECIALIZATION"] = "OBSTETRICS & GYNAECOLOGY"
            row_data["ANESTHESIOLOGIST"] = "DR. E. SANTOS"
            row_data["ANESTHESIOLOGIST SPECIALIZATION"] = "GENERAL ANAESTHESIOLOGY"
            row_data["PROCEDURE COMPLEXITY"] = "Major"
            row_data["HOSPITALIZATION MODE"] = "INPATIENT"
            row_data["PATIENT STATUS"] = random.choice(["ACTIVE", "MGH"])

          elif target_dept == "Endoscopy Unit (ENDO)":
            row_data["SCHEDULED TIME"] = "10:30 AM"
            row_data["ACTUAL TIME"] = "11:00 AM"
            row_data["AGE"] = age
            row_data["DIAGNOSIS"] = "UPPER GASTROINTESTINAL BLEEDING / PEPTIC ULCER DISEASE"
            row_data["PROCEDURE"] = "UPPER GASTROINTESTINAL ENDOSCOPY (DIAGNOSTIC / EGD)"
            row_data["PROCEDURE CATEGORY"] = "DIGESTIVE SYSTEM"
            row_data["HOSPITAL PACKAGE BUNDLE"] = "Hospital Package Kit (ENDO/YAKAP)"
            row_data["PHILHEALTH CASE RATE (RVS CODE)"] = "43235 - UPPER GI ENDOSCOPY [₱20,553.00]"
            row_data["ATTENDING PHYSICIAN"] = "DR. M. REYES"
            row_data["ATTENDING SPECIALIZATION"] = "GASTROENTEROLOGY"
            row_data["CO-MANAGEMENT PHYSICIAN"] = "N/A"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "N/A"
            row_data["SURGEON / PROCEDURALIST"] = "DR. M. REYES"
            row_data["SURGEON SPECIALIZATION"] = "GASTROENTEROLOGY"
            row_data["ANESTHESIOLOGIST"] = "N/A"
            row_data["ANESTHESIOLOGIST SPECIALIZATION"] = "NONE"
            row_data["PROCEDURE COMPLEXITY"] = "Diagnostics"
            row_data["HOSPITALIZATION MODE"] = "OUTPATIENT"
            row_data["PATIENT STATUS"] = "ACTIVE"

          elif target_dept == "Hemodialysis Unit (HDU)":
            row_data["TRUE DATE"] = "0"
            row_data["AGE"] = age
            row_data["DIAGNOSIS"] = scenario["condition"]
            row_data["ATTENDING PHYSICIAN"] = "DR. A. CRUZ"
            row_data["ATTENDING SPECIALIZATION"] = "NEPHROLOGY"
            row_data["CO-MANAGEMENT PHYSICIAN"] = "N/A"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "N/A"
            row_data["DIALYSIS SHIFT SLOT"] = random.choice(["1ST SET", "2ND SET", "3RD SET", "ON-CALL"])
            row_data["HOSPITALIZATION MODE"] = "OUTPATIENT"
            row_data["PATIENT STATUS"] = "ACTIVE"
            row_data["PROCEDURES"] = scenario["treatment"]
            row_data["DIAGNOSTIC EXAMINATIONS"] = scenario["diags"]
            row_data["MEDICATIONS"] = scenario["meds"]
            row_data["SPECIAL ENDORSEMENTS"] = scenario["ends"]

          elif target_dept == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)":
            row_data["AGE"] = f"{random.randint(1, 28)} DAYS"
            row_data["AOG"] = "38 WKS"
            row_data["DIAGNOSIS"] = scenario["condition"]
            row_data["DIAGNOSIS CATEGORY"] = scenario["spec"]
            row_data["ADMITTED FROM"] = "LRDR"
            row_data["ADMITTED TO"] = random.choice(["NICU", "PICU", "NSU", "PCN", "OUTBORN"])
            row_data["TRANSFERRED TO"] = "NONE"
            row_data["ATTENDING PHYSICIAN"] = "DR. E. SANTOS"
            row_data["ATTENDING SPECIALIZATION"] = "NEONATOLOGY"
            row_data["CO-MANAGEMENT PHYSICIAN"] = "N/A"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "N/A"
            row_data["HOSPITALIZATION MODE"] = "INPATIENT"
            row_data["PATIENT STATUS"] = random.choice(["ACTIVE", "CAB"])
            row_data["PROCEDURES"] = scenario["treatment"]
            row_data["DIAGNOSTIC EXAMINATIONS"] = scenario["diags"]
            row_data["MEDICATIONS"] = scenario["meds"]
            row_data["SPECIAL ENDORSEMENTS"] = scenario["ends"]

          else:  # General Nursing Units
            row_data["TIME"] = "10:00 AM"
            row_data["ROOM NO"] = f"RM-{random.randint(201, 450)}"
            row_data["AGE"] = age
            row_data["DIAGNOSIS"] = scenario["condition"]
            row_data["ATTENDING PHYSICIAN"] = "DR. M. REYES"
            row_data["ATTENDING SPECIALIZATION"] = scenario["spec"]
            row_data["CO-MANAGEMENT PHYSICIAN"] = "DR. A. CRUZ"
            row_data["CO-MANAGEMENT SPECIALIZATION"] = "ENDOCRINOLOGY"
            row_data["HOSPITALIZATION MODE"] = scenario["hosp"]
            row_data["PATIENT STATUS"] = random.choice(["ACTIVE", "MGH", "CAB", "DISCHARGED"])
            row_data["PROCEDURES"] = scenario["treatment"]
            row_data["DIAGNOSTIC EXAMINATIONS"] = scenario["diags"]
            row_data["MEDICATIONS"] = scenario["meds"]
            row_data["SPECIAL ENDORSEMENTS"] = scenario["ends"]

          append_record_to_google_sheet(target_dept, row_data)
          completed_count += 1
          progress_bar.progress(completed_count / total_tasks)
          py_time.sleep(0.01)

      st.cache_data.clear()
      st.session_state["df_cache"] = {}
      log_audit_event(
          "SEED",
          "ALL",
          f"Generated balanced multi-scenario batch of {batch_size} records per department",
      )
      st.sidebar.success(
          "Successfully generated advanced multi-scenario trial patient records"
          " across all units!"
      )
      st.rerun()

  with st.sidebar.expander("🚨 Full System Wipe (All Depts)"):
    st.markdown(
        "Permanently erase all records, patient data, metrics, and tallies from"
        " **every** department and local database."
    )
    confirm_system_wipe = st.checkbox("I confirm wiping all data", value=False)

    if st.button("🧹 Execute Full Wipe", type="primary"):
      if confirm_system_wipe:
        try:
          for s_name, cols in SHEET_HEADERS.items():
            try:
              if sh:
                ws = sh.worksheet(s_name)
                ws.clear()
                ws.update(
                    "A1", [[f"MTCMC CLINICAL CENSUS - {s_name} MASTERFILE"]]
                )
                ws.update("A4", [cols])
            except Exception:
              pass
            py_time.sleep(0.2)

          conn = get_sqlite_conn()
          cursor = conn.cursor()
          for s_name, cols in SHEET_HEADERS.items():
            cursor.execute(f'DELETE FROM "{s_name}"')
          conn.commit()
          conn.close()

          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          log_audit_event("WIPE", "ALL", "Executed full system wipe")
          st.sidebar.success(
              "Successfully wiped all data across all departments!"
          )
          st.rerun()
        except Exception as e:
          st.sidebar.error(f"Wipe failed: {e}")
      else:
        st.sidebar.warning("Please check the confirmation box to proceed.")
  st.sidebar.markdown("---")

logged_user_key = st.session_state["username"]
user_info = USER_DATABASE.get(logged_user_key, {})
allowed_modules = user_info.get("modules", "All")

all_department_modules = [
    "Hospital Information System",
    "Pareto Tally Sheet",
] + sorted_departments
if allowed_modules == "All":
  MODULES = all_department_modules
else:
  allowed_list = (
      list(allowed_modules)
      if isinstance(allowed_modules, list)
      else [allowed_modules]
  )
  fixed_front = [
      m
      for m in ["Hospital Information System", "Pareto Tally Sheet"]
      if m in allowed_list or allowed_modules == "All"
  ]
  other_allowed = sorted([
      m
      for m in allowed_list
      if m not in ["Hospital Information System", "Pareto Tally Sheet"]
  ])
  MODULES = fixed_front + other_allowed

pinned_modules = ["Hospital Information System", "Pareto Tally Sheet"]
filtered_modules = [m for m in MODULES if m not in pinned_modules]
MODULES = pinned_modules + sorted(filtered_modules)

st.sidebar.markdown("### 🧭 Department Navigation")
selected_sheet = st.sidebar.selectbox(
    "Select Target Google Sheet Module", MODULES, index=0
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 Export Reports")

active_export_df = (
    read_google_sheet(selected_sheet)
    if selected_sheet
    not in ["Hospital Information System", "Pareto Tally Sheet"]
    else read_google_sheet("Emergency Care Complex (ECC)")
)

excel_buffer = io.BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
  if not active_export_df.empty:
    active_export_df.to_excel(
        writer, index=False, sheet_name=selected_sheet[:30]
    )
  else:
    pd.DataFrame(["No records found"]).to_excel(
        writer, index=False, sheet_name="Sheet1"
    )
excel_data = excel_buffer.getvalue()

st.sidebar.download_button(
    label="📊 Export to Excel",
    data=excel_data,
    file_name=f"MTCMC_{selected_sheet.replace(' ', '_')}_Census.xlsx",
    mime=(
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
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
  html_content += (
      cleaned_pdf_df.head(100).to_html(index=False, border=0)
      if not cleaned_pdf_df.empty
      else "<p>No records available.</p>"
  )
  return (html_content + "</body></html>").encode("utf-8")


st.sidebar.download_button(
    label="📄 Export as PDF",
    data=convert_df_to_pdf_html(active_export_df, selected_sheet),
    file_name=f"MTCMC_{selected_sheet.replace(' ', '_')}_Report.html",
    mime="text/html",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "<p style='font-size: 0.85rem; color: #0f766e; font-style: italic;"
    " margin-bottom: 10px;'>All data entries are securely stored on our hospital"
    " database.</p>",
    unsafe_allow_html=True,
)

if st.sidebar.button("🔄 Refresh Data"):
  st.cache_data.clear()
  st.session_state["df_cache"] = {}
  st.toast(
      "Reloaded latest census & patient records.", icon="🔄"
  )
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


def render_inpatient_order_updater_form(dept_name_label):
  st.markdown(
      f"##### 🔄 Update Inpatient Orders from `{dept_name_label}` to GNU / SCU"
  )

  show_all_toggle = st.checkbox(
      f"Show all active inpatients without smart pre-filtering ({dept_name_label})",
      value=False,
      key=f"toggle_all_{dept_name_label}",
  )

  gnu_sheets = sorted([
      d
      for d in sorted_departments
      if d.startswith("General Nursing Unit (GNU")
  ]) + ["Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"]

  all_inpatients = []
  sheet_data_cache = read_multiple_sheets_parallel(gnu_sheets)
  for gnu in gnu_sheets:
    g_df = sheet_data_cache.get(gnu, pd.DataFrame())
    if not g_df.empty and "LAST NAME" in g_df.columns:
      active_sub = g_df[
          ~g_df.get("PATIENT STATUS", pd.Series(["ACTIVE"] * len(g_df)))
          .astype(str)
          .str.upper()
          .isin(["DISCHARGED"])
      ]

      if not show_all_toggle and not active_sub.empty:
        if dept_name_label == "SCC":
          active_sub = active_sub[
              active_sub["DIAGNOSIS"].astype(str).str.contains(
                  "SURGERY|APPENDICITIS|HERNIA|STONE|TUMOR|OR|COMPLEX",
                  case=False,
                  na=False,
              )
              | active_sub["SPECIAL ENDORSEMENTS"].astype(str).str.contains(
                  "OR|SURGERY|FOR OR", case=False, na=False
              )
          ]
        elif dept_name_label == "ENDO":
          active_sub = active_sub[
              active_sub["DIAGNOSIS"].astype(str).str.contains(
                  "BLEEDING|GASTRO|ULCER|POLYP|SCOPE|LIVER|GI",
                  case=False,
                  na=False,
              )
              | active_sub["PROCEDURES"].astype(str).str.contains(
                  "SCOPE|GASTRO|COLONO", case=False, na=False
              )
          ]
        elif dept_name_label == "OBGYNE":
          active_sub = active_sub[
              active_sub["SEX"].astype(str).str.upper() == "FEMALE"
          ]

      if not active_sub.empty:
        active_sub["TARGET_SHEET"] = gnu
        active_sub["DISPLAY_LABEL"] = (
            "["
            + gnu.split("(")[-1].replace(")", "")
            + "] "
            + active_sub["LAST NAME"]
            + ", "
            + active_sub["FIRST NAME"]
        )
        all_inpatients.append(active_sub)

  if all_inpatients:
    master_inpatient_df = pd.concat(all_inpatients, ignore_index=True)
    if master_inpatient_df.empty:
      st.info(
          f"No matching pre-filtered inpatients found for `{dept_name_label}`."
          " Check the toggle above to view all active inpatients."
      )
      return

    selected_inpatient_label = st.selectbox(
        "Select Active Inpatient from GNU / SCU",
        sorted(master_inpatient_df["DISPLAY_LABEL"].tolist()),
        key=f"cross_inpatient_sel_{dept_name_label}",
    )

    matched_inpatient_row = master_inpatient_df[
        master_inpatient_df["DISPLAY_LABEL"] == selected_inpatient_label
    ].iloc[0]
    target_sheet = matched_inpatient_row["TARGET_SHEET"]

    unit_full_df = read_google_sheet(target_sheet)
    matched_idx = unit_full_df[
        (unit_full_df["LAST NAME"] == matched_inpatient_row["LAST NAME"])
        & (unit_full_df["FIRST NAME"] == matched_inpatient_row["FIRST NAME"])
        & (
            unit_full_df["DATE"].astype(str).str.strip()
            == str(matched_inpatient_row["DATE"]).strip()
        )
    ].index

    st.markdown("##### 5. Diagnostics Procedures and Treatment Plans")
    search_rvs_cross = st.text_input("🔍 Search / Enter Specific RVS Code Directly", value="", key=f"search_rvs_cross_{dept_name_label}").strip().upper()
    matched_rvs_cross = []
    added_cross_procs = ""
    if search_rvs_cross:
      for cat_k, p_list in ANNEX_B_CATEGORIZED_PROCEDURES.items():
        for p_item in p_list:
          if search_rvs_cross in p_item:
            matched_rvs_cross.append(f"[{cat_k}] {p_item}")
      if matched_rvs_cross:
        sel_m = st.selectbox("Matching RVS Codes Found", ["Select Match"] + matched_rvs_cross, key=f"sel_m_cross_{dept_name_label}")
        if sel_m and sel_m != "Select Match":
          added_cross_procs = sel_m
      else:
        added_cross_procs = f"{search_rvs_cross} - CUSTOM RVS ENTRY"
    else:
      chosen_cat_cross = st.selectbox(
          "Select Anatomical / Surgical Category",
          ["Select Category"] + sorted(list(ANNEX_B_CATEGORIZED_PROCEDURES.keys())),
          key=f"cross_cat_{dept_name_label}"
      )
      if chosen_cat_cross and chosen_cat_cross != "Select Category":
        sub_c = sorted(ANNEX_B_CATEGORIZED_PROCEDURES[chosen_cat_cross])
        added_cross_procs = st.selectbox(
            f"PhilHealth Case Rate (RVS Code) under `{chosen_cat_cross}`",
            ["Select Procedure"] + sub_c,
            key=f"cross_proc_{dept_name_label}_{chosen_cat_cross}"
        )

    with st.form(f"cross_dept_form_{dept_name_label}"):
      st.markdown(
          f"**Selected Inpatient:** `{selected_inpatient_label}` | **Unit:**"
          f" `{target_sheet}`"
      )

      add_meds = st.text_area(
          "Add Medications / Orders",
          value="",
          key=f"c_med_{dept_name_label}",
      ).strip().upper()
      add_ends = st.text_area(
          "Special Endorsements / Notes",
          value="",
          key=f"c_end_{dept_name_label}",
      ).strip().upper()

      st.markdown("---")
      confirm_password = st.text_input(
          "🔒 Re-enter Your Account Password to Authorize Update",
          type="password",
          key=f"reauth_pwd_{dept_name_label}",
      )

      submit_cross = st.form_submit_button(
          "💾 Push Order Update to Inpatient Record"
      )
      if submit_cross:
        current_username = st.session_state.get("username", "").strip().lower()
        user_record = USER_DATABASE.get(current_username, {})
        stored_hash = user_record.get("password", "")

        if not confirm_password or hash_password(confirm_password) != stored_hash:
          st.error(
              "🚨 Authorization Error: Incorrect account password. Update"
              " aborted."
          )
          st.stop()

        if len(matched_idx) > 0:
          idx = matched_idx[0]
          now_ts = get_ph_time().strftime(
              f"[%m/%d/%Y %I:%M %p - {st.session_state['name']}]"
          )

          if added_cross_procs and added_cross_procs != "Select Procedure":
            ex_p = (
                str(unit_full_df.loc[idx, "PROCEDURES"])
                if "PROCEDURES" in unit_full_df.columns
                else ""
            )
            bullet_item = f"• {now_ts} {added_cross_procs}"
            unit_full_df.loc[idx, "PROCEDURES"] = (
                f"{ex_p}\n{bullet_item}".strip()
                if ex_p and ex_p != "NAN"
                else bullet_item
            )

          if add_meds:
            ex_m = (
                str(unit_full_df.loc[idx, "MEDICATIONS"])
                if "MEDICATIONS" in unit_full_df.columns
                else ""
            )
            bullet_item = f"• {now_ts} {add_meds}"
            unit_full_df.loc[idx, "MEDICATIONS"] = (
                f"{ex_m}\n{bullet_item}".strip()
                if ex_m and ex_m != "NAN"
                else bullet_item
            )

          if add_ends:
            ex_e = (
                str(unit_full_df.loc[idx, "SPECIAL ENDORSEMENTS"])
                if "SPECIAL ENDORSEMENTS" in unit_full_df.columns
                else ""
            )
            bullet_item = f"• {now_ts} {add_ends}"
            unit_full_df.loc[idx, "SPECIAL ENDORSEMENTS"] = (
                f"{ex_e}\n{bullet_item}".strip()
                if ex_e and ex_e != "NAN"
                else bullet_item
            )

          if update_google_sheet_from_df(target_sheet, unit_full_df):
            st.cache_data.clear()
            st.session_state["df_cache"] = {}
            st.success(
                f"Successfully updated inpatient record in `{target_sheet}` with"
                f" timestamped bullet entries from `{dept_name_label}`!"
            )
            st.rerun()
        else:
          st.error("Could not locate the specific inpatient record index.")
  else:
    st.info("No active inpatients currently admitted in GNU or Special Care Complex.")


def render_department_live_roster(dept_sheet_name):
  st.markdown(f"### 📋 Active Live Roster (`{dept_sheet_name}`)")
  dept_df = read_google_sheet(dept_sheet_name)
  if not dept_df.empty:
    clean_d = clean_display_df(dept_df)
    show_all_dept_patients = st.checkbox(
        "Include discharged patients in unit view", value=False, key=f"d_disc_{dept_sheet_name}"
    )
    if "PATIENT STATUS" in clean_d.columns:
      clean_d["PATIENT STATUS"] = clean_d["PATIENT STATUS"].fillna("ACTIVE")
      if not show_all_dept_patients:
        filtered_d = clean_d[
            clean_d["PATIENT STATUS"].astype(str).str.strip().str.upper().isin(["ACTIVE", "MGH", "CAB"])
        ]
      else:
        filtered_d = clean_d
    else:
      filtered_d = clean_d

    display_paginated_dataframe(filtered_d, key_prefix=f"roster_{dept_sheet_name}", is_historical=True)
  else:
    st.info(f"No records found in `{dept_sheet_name}` yet.")


# ---------------------------------------------------------
# MODULE: PARETO TALLY SHEET
# ---------------------------------------------------------
if selected_sheet == "Pareto Tally Sheet":
  st.header("📊 Pareto Tally Sheet & Department Analytics")
  st.markdown(
      "Organized per department with dynamic patient census categorization,"
      " specialization breakdowns, doctor census tables, and separate Daily &"
      " Monthly Tally tables displayed in table format."
  )

  all_dept_options = sorted([
      "Emergency Care Complex (ECC)",
      "Surgical Care Complex (OR Main)",
      "OBGYNE Care Complex (LRDR-OB Surgery)",
      "Hemodialysis Unit (HDU)",
      "Endoscopy Unit (ENDO)",
      "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
  ]) + sorted([
      d
      for d in sorted_departments
      if d.startswith("General Nursing Unit")
  ])

  selected_tally_dept = st.selectbox(
      "🏥 Choose Department / Unit for Pareto Tally & Census Analysis",
      all_dept_options,
  )

  sheet_target_map = {
      "Emergency Care Complex (ECC)": "Emergency Care Complex (ECC)",
      "Surgical Care Complex (OR Main)": "Surgical Care Complex (OR Main)",
      "OBGYNE Care Complex (LRDR-OB Surgery)": (
          "OBGYNE Care Complex (LRDR-OB Surgery)"
      ),
      "Hemodialysis Unit (HDU)": "Hemodialysis Unit (HDU)",
      "Endoscopy Unit (ENDO)": "Endoscopy Unit (ENDO)",
      "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)": (
          "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
      ),
  }
  for gnu in [
      d for d in sorted_departments if d.startswith("General Nursing Unit")
  ]:
    sheet_target_map[gnu] = gnu

  target_sheet_name = sheet_target_map.get(
      selected_tally_dept, selected_tally_dept
  )
  dept_df = read_google_sheet(target_sheet_name)

  if not dept_df.empty:
    st.markdown(
        f"### 📋 Patient Census & Category Breakdown for `{selected_tally_dept}`"
    )
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
      if "CATEGORY" in c_upper or "PROCEDURE" in c_upper or "DISEASE" in c_upper:
        if not cat_col:
          cat_col = col
      if "SPECIALIZATION" in c_upper:
        if not spec_col:
          spec_col = col
      if (
          "PHYSICIAN" in c_upper
          or "SURGEON" in c_upper
          or "ATTENDING" in c_upper
      ):
        if not doc_col:
          doc_col = col
      if "HOSPITALIZATION MODE" in c_upper:
        hosp_mode_col = col
      if "CASE TYPE" in c_upper:
        case_type_col = col
      if "MODE OF PAYMENT" in c_upper or "PAYMENT" in c_upper:
        payment_col = col
      if "SHIFT" in c_upper or "SLOT" in c_upper or "SET" in c_upper:
        shift_col = col

    st.markdown("---")
    st.markdown(
        f"### 📅 Daily & Monthly Census Tallies (`{selected_tally_dept}`)"
    )
    dt_col1, dt_col2 = st.columns(2)
    with dt_col1:
      st.markdown("##### 📆 Daily Tally (By Date)")
      if "DATE" in clean_dept_df.columns:
        daily_tally = clean_dept_df["DATE"].value_counts().reset_index()
        daily_tally.columns = ["Date", "Total Cases"]
        st.dataframe(daily_tally, use_container_width=True)
      else:
        st.info("No Date column found for daily tally.")
    with dt_col2:
      st.markdown("##### 🗓️ Monthly Tally (By Month)")
      if "MONTH" in clean_dept_df.columns:
        monthly_tally = clean_dept_df["MONTH"].value_counts().reset_index()
        monthly_tally.columns = ["Month", "Total Cases"]
        st.dataframe(monthly_tally, use_container_width=True)
      else:
        st.info("No Month column found for monthly tally.")

    st.markdown("---")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
      st.markdown("##### 🏷️ Patient Census by Category / Procedure")
      if cat_col and cat_col in clean_dept_df.columns:
        cat_counts = (
            clean_dept_df[cat_col].value_counts().reset_index()
        )
        cat_counts.columns = [cat_col, "Total Cases"]
        st.dataframe(cat_counts, use_container_width=True)
      else:
        st.info("No categorical breakdown column found for this department.")

    with col_p2:
      st.markdown("##### 🩺 Patient Census by Specialization")
      if spec_col and spec_col in clean_dept_df.columns:
        spec_counts = (
            clean_dept_df[spec_col].value_counts().reset_index()
        )
        spec_counts.columns = [spec_col, "Total Cases"]
        st.dataframe(spec_counts, use_container_width=True)
      else:
        st.info("No specialization column found for this department.")

    st.markdown("---")
    st.markdown(f"### 🔀 Cross-Tabulation Tallies (`{selected_tally_dept}`)")

    cross_col1, cross_col2 = st.columns(2)
    with cross_col1:
      if (
          hosp_mode_col
          and hosp_mode_col in clean_dept_df.columns
          and case_type_col
          and case_type_col in clean_dept_df.columns
      ):
        st.markdown("##### 🏥 Hospitalization Mode vs. Case Type")
        ctable_mode_case = pd.crosstab(
            clean_dept_df[hosp_mode_col].fillna("UNKNOWN"),
            clean_dept_df[case_type_col].fillna("UNKNOWN"),
            margins=True,
            margins_name="Total Cases",
        ).reset_index()
        st.dataframe(ctable_mode_case, use_container_width=True)
      elif hosp_mode_col and hosp_mode_col in clean_dept_df.columns:
        st.markdown("##### 🏥 Hospitalization Mode Tally")
        hm_counts = (
            clean_dept_df[hosp_mode_col].value_counts().reset_index()
        )
        hm_counts.columns = ["Hospitalization Mode", "Total Cases"]
        st.dataframe(hm_counts, use_container_width=True)

    with cross_col2:
      if (
          hosp_mode_col
          and hosp_mode_col in clean_dept_df.columns
          and payment_col
          and payment_col in clean_dept_df.columns
      ):
        st.markdown("##### 💳 Hospitalization Mode vs. Mode of Payment")
        ctable_mode_pay = pd.crosstab(
            clean_dept_df[hosp_mode_col].fillna("UNKNOWN"),
            clean_dept_df[payment_col].fillna("UNKNOWN"),
            margins=True,
            margins_name="Total Cases",
        ).reset_index()
        st.dataframe(ctable_mode_pay, use_container_width=True)
      elif payment_col and payment_col in clean_dept_df.columns:
        st.markdown("##### 💳 Mode of Payment Tally")
        pay_counts = (
            clean_dept_df[payment_col].value_counts().reset_index()
        )
        pay_counts.columns = ["Mode of Payment", "Total Cases"]
        st.dataframe(pay_counts, use_container_width=True)

    if shift_col and shift_col in clean_dept_df.columns:
      st.markdown("##### ⏱️ Shift Slot / Schedule Tally")
      sh_counts = clean_dept_df[shift_col].value_counts().reset_index()
      sh_counts.columns = ["Shift Slot", "Total Cases"]
      st.dataframe(sh_counts, use_container_width=True)

    st.markdown("---")
    st.markdown(f"### 👨‍⚕️ Doctors Census per Specialization (`{selected_tally_dept}`)")

    if (
        spec_col
        and spec_col in clean_dept_df.columns
        and doc_col
        and doc_col in clean_dept_df.columns
    ):
      unique_specs = clean_dept_df[spec_col].dropna().unique()
      if len(unique_specs) > 0:
        spec_tabs = st.tabs([str(s) for s in unique_specs])
        for idx, spec in enumerate(unique_specs):
          with spec_tabs[idx]:
            st.markdown(f"**Specialization:** `{spec}`")
            sub_df = clean_dept_df[clean_dept_df[spec_col] == spec]
            if not sub_df.empty and doc_col in sub_df.columns:
              doc_counts = (
                  sub_df[doc_col].value_counts().reset_index()
              )
              doc_counts.columns = ["Name of Physician", "Total Cases"]
              st.dataframe(doc_counts, use_container_width=True)
            else:
              st.info(
                  f"No physician records found for specialization {spec}."
              )
      else:
        st.info("No specializations recorded yet.")
    else:
      st.info("No doctor specialization breakdown available for this department yet.")
  else:
    st.info(f"No records found in live database for `{selected_tally_dept}`.")

# ---------------------------------------------------------
# MODULE: HOSPITAL INFORMATION SYSTEM (LANDING PAGE)
# ---------------------------------------------------------
elif selected_sheet == "Hospital Information System":

  @st.fragment(run_every=30)
  def render_hospital_summary_fragment():
    st.header("🏥 Hospital Summary")
    st.markdown("This is the current active census summary today (Instant Local Read & Auto-Refreshed).")

    department_sheets = sorted([
        "Emergency Care Complex (ECC)",
        "Endoscopy Unit (ENDO)",
        "Hemodialysis Unit (HDU)",
        "OBGYNE Care Complex (LRDR-OB Surgery)",
        "Surgical Care Complex (OR Main)",
        "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
        "General Nursing Unit (GNU 1C)",
        "General Nursing Unit (GNU 2A)",
        "General Nursing Unit (GNU 2B)",
        "General Nursing Unit (GNU 2C)",
        "General Nursing Unit (GNU 2D)",
        "General Nursing Unit (GNU 3A)",
        "General Nursing Unit (GNU 3B)",
        "General Nursing Unit (GNU 3C)",
        "General Nursing Unit (GNU 4A)",
    ])

    gnu_sheets = [
        d for d in department_sheets if d.startswith("General Nursing Unit (GNU")
    ]
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

    current_status_tokens = []
    for gnu in gnu_sheets + [scu_sheet]:
      df_chk = dept_data_map.get(gnu, pd.DataFrame())
      if not df_chk.empty and "PATIENT STATUS" in df_chk.columns:
        current_status_tokens.append(str(df_chk["PATIENT STATUS"].fillna("ACTIVE").tolist()))
    new_checksum = hashlib.md5("".join(current_status_tokens).encode()).hexdigest()

    if st.session_state.get("status_checksum", "") != new_checksum:
      st.session_state["status_checksum"] = new_checksum
      st.toast("⚡ Status change detected in GNU/SCU. Hospital Summary auto-refreshed!", icon="🔄")

    for dept in department_sheets:
      df = dept_data_map.get(dept, pd.DataFrame())
      record_count = len(df) if not df.empty else 0
      daily_count, monthly_count = 0, 0

      if not df.empty and "DATE" in df.columns:
        daily_count = len(
            df[df["DATE"].astype(str).str.strip() == today_str]
        )
        if "MONTH" in df.columns:
          monthly_subset = df[
              df["MONTH"]
              .astype(str)
              .str.contains(current_month_name, case=False, na=False)
              | df["MONTH"]
              .astype(str)
              .str.startswith(f"{current_month_num}.", na=False)
          ]
          monthly_count = len(monthly_subset)

      if dept in gnu_sheets and not df.empty and "PATIENT STATUS" in df.columns:
        df["PATIENT STATUS"] = df["PATIENT STATUS"].fillna("ACTIVE")
        for st_val in df["PATIENT STATUS"]:
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
          "Monthly Patient Census": monthly_count,
      })

    scu_df = dept_data_map.get(scu_sheet, pd.DataFrame())
    nic_count, pic_count, nsu_count, pcn_count, out_count = 0, 0, 0, 0, 0
    if not scu_df.empty and "ADMITTED TO" in scu_df.columns:
      scu_df["ADMITTED_TO_UP"] = (
          scu_df["ADMITTED TO"].astype(str).str.strip().str.upper()
      )
      nic_count = len(
          scu_df[scu_df["ADMITTED_TO_UP"].str.contains("NICU", na=False)]
      )
      pic_count = len(
          scu_df[scu_df["ADMITTED_TO_UP"].str.contains("PICU", na=False)]
      )
      nsu_count = len(
          scu_df[scu_df["ADMITTED_TO_UP"].str.contains("NSU", na=False)]
      )
      pcn_count = len(
          scu_df[scu_df["ADMITTED_TO_UP"].str.contains("PCN", na=False)]
      )
      out_count = len(
          scu_df[scu_df["ADMITTED_TO_UP"].str.contains("OUTBORN", na=False)]
      )

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

    st.subheader("📋 Active Live Roster of Patients")
    st.markdown(
        "Aggregated live roster displaying all patients tagged as **ACTIVE**,"
        " **MGH**, or **CAB** across General Nursing Units and Special Care"
        " Complex."
    )

    show_discharged = st.checkbox(
        "Include recently discharged in roster view", value=False
    )
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
      if "PATIENT STATUS" in master_gnu_df.columns:
        master_gnu_df["PATIENT STATUS"] = master_gnu_df["PATIENT STATUS"].fillna(
            "ACTIVE"
        )
        if not show_discharged:
          gnu_filtered = master_gnu_df[
              master_gnu_df["PATIENT STATUS"]
              .astype(str)
              .str.strip()
              .str.upper()
              .isin(["ACTIVE", "MGH", "CAB"])
          ]
        else:
          gnu_filtered = master_gnu_df
      else:
        gnu_filtered = master_gnu_df

      if not gnu_filtered.empty:
        gnu_filtered["NAME OF PATIENT"] = (
            gnu_filtered.get("LAST NAME", "").astype(str).str.strip()
            + ", "
            + gnu_filtered.get("FIRST NAME", "").astype(str).str.strip()
            + " "
            + gnu_filtered.get("MIDDLE NAME", "").astype(str).str.strip()
        ).str.strip(", ")

        gnu_mapped = pd.DataFrame()
        gnu_mapped["Admission Date"] = gnu_filtered.get("DATE", "")
        gnu_mapped["Department / Unit"] = gnu_filtered.get(
            "SOURCE DEPARTMENT", ""
        )
        gnu_mapped["Room No."] = gnu_filtered.get("ROOM NO", "N/A")
        gnu_mapped["Name of Patient"] = gnu_filtered["NAME OF PATIENT"]
        gnu_mapped["Age"] = gnu_filtered.get("AGE", "")
        gnu_mapped["Diagnosis"] = gnu_filtered.get("DIAGNOSIS", "")
        gnu_mapped["Attending Physician"] = gnu_filtered.get(
            "ATTENDING PHYSICIAN", ""
        )
        gnu_mapped["Status"] = gnu_filtered.get("PATIENT STATUS", "")
        roster_combined_frames.append(gnu_mapped)

    scu_raw_df = dept_data_map.get(scu_sheet, pd.DataFrame())
    if not scu_raw_df.empty:
      scu_c = scu_raw_df.copy()
      if "PATIENT STATUS" in scu_c.columns:
        scu_c["PATIENT STATUS"] = scu_c["PATIENT STATUS"].fillna("ACTIVE")
        if not show_discharged:
          scu_filtered = scu_c[
              scu_c["PATIENT STATUS"]
              .astype(str)
              .str.strip()
              .str.upper()
              .isin(["ACTIVE", "MGH", "CAB"])
          ]
        else:
          scu_filtered = scu_c
      else:
        scu_filtered = scu_c

      if not scu_filtered.empty:
        scu_filtered["NAME OF PATIENT"] = (
            scu_filtered.get("LAST NAME", "").astype(str).str.strip()
            + ", "
            + scu_filtered.get("FIRST NAME", "").astype(str).str.strip()
            + " "
            + scu_filtered.get("MIDDLE NAME", "").astype(str).str.strip()
        ).str.strip(", ")

        scu_mapped = pd.DataFrame()
        scu_mapped["Admission Date"] = scu_filtered.get("DATE", "")
        scu_mapped["Department / Unit"] = (
            "SPECIAL CARE COMPLEX ("
            + scu_filtered.get("ADMITTED TO", "NICU")
            + ")"
        )
        scu_mapped["Room No."] = "N/A"
        scu_mapped["Name of Patient"] = scu_filtered["NAME OF PATIENT"]
        scu_mapped["Age"] = scu_filtered.get("AGE", "")
        scu_mapped["Diagnosis"] = scu_filtered.get("DIAGNOSIS", "")
        scu_mapped["Attending Physician"] = scu_filtered.get(
            "ATTENDING PHYSICIAN", ""
        )
        scu_mapped["Status"] = scu_filtered.get("PATIENT STATUS", "ACTIVE")
        roster_combined_frames.append(scu_mapped)

    if roster_combined_frames:
      final_master_roster = pd.concat(roster_combined_frames, ignore_index=True)
      clean_roster = clean_display_df(final_master_roster)

      st.dataframe(clean_roster, use_container_width=True)
      st.caption(f"Showing {len(clean_roster)} active live roster entries.")
    else:
      st.info("No active patient roster records found.")

    st.markdown("---")
    st.subheader("📊 Department Performance")
    summary_df = pd.DataFrame(summary_data)
    st.dataframe(clean_display_df(summary_df), use_container_width=True)

    st.markdown("---")
    st.subheader("📑 Department Summary")
    selected_dept_view = st.selectbox(
        "Select Department to Inspect", department_sheets
    )

    dept_df = dept_data_map.get(selected_dept_view, pd.DataFrame())
    if not dept_df.empty:
      cleaned_dept_df = clean_display_df(dept_df)

      if (
          selected_dept_view
          == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)"
          and "ADMITTED TO" in cleaned_dept_df.columns
      ):
        st.markdown("##### 📍 Sort & Filter by Admitted Area")
        admit_areas = sorted(
            cleaned_dept_df["ADMITTED TO"].dropna().unique().tolist()
        )
        selected_area = st.selectbox(
            "Select Admitted To Area", ["All Areas"] + admit_areas
        )
        if selected_area != "All Areas":
          cleaned_dept_df = cleaned_dept_df[
              cleaned_dept_df["ADMITTED TO"] == selected_area
          ]

      edited_dept_df = display_paginated_dataframe(
          cleaned_dept_df,
          key_prefix=f"dept_{selected_dept_view}",
          is_historical=True,
      )

      if st.button(
          f"💾 Save Changes to `{selected_dept_view}`", type="primary"
      ):
        if update_google_sheet_from_df(selected_dept_view, edited_dept_df):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              f"Successfully updated records for `{selected_dept_view}`!"
          )
          st.rerun()
        else:
          st.error(
              "Failed to update database."
          )
    else:
      st.info(f"No records found yet for {selected_dept_view}.")

  render_hospital_summary_fragment()

# ---------------------------------------------------------
# GENERIC REGISTRATION FORM FOR GNU UNITS
# ---------------------------------------------------------
elif selected_sheet.startswith("General Nursing Unit (GNU"):
  gnu_title = selected_sheet
  st.header(
      f"🛏️ {gnu_title} Patient Registration & Admitted Patient Update"
  )
  ph_now = get_ph_time()
  form_key_slug = (
      gnu_title.replace("General Nursing Unit (", "")
      .replace(")", "")
      .strip()
      .lower()
  )

  tab_reg, tab_update, tab_roster = st.tabs(
      ["📝 New Admission Registration", "🔄 Update Admitted Patient Orders", "📋 Active Live Roster"]
  )

  with tab_reg:
    st.info("ℹ️ **Rule Notice:** If the patient was already registered as an INPATIENT in the Emergency Care Complex (ECC) and designated for transfer to this unit, you do not need to re-register them here using the standard form.")

    chosen_cat_gnu = st.selectbox(
        "Select Anatomical / Surgical Category",
        ["Select Category"] + sorted(list(ANNEX_B_CATEGORIZED_PROCEDURES.keys())),
        key=f"gnu_cat_{form_key_slug}"
    )
    gnu_selected_proc = ""
    if chosen_cat_gnu and chosen_cat_gnu != "Select Category":
      sub_p = sorted(ANNEX_B_CATEGORIZED_PROCEDURES[chosen_cat_gnu])
      gnu_selected_proc = st.selectbox(
          f"PhilHealth Case Rate (RVS Code) under `{chosen_cat_gnu}`",
          ["Select Procedure"] + sub_p,
          key=f"gnu_proc_{form_key_slug}_{chosen_cat_gnu}"
      )

    with st.form(f"gnu_form_{form_key_slug}", clear_on_submit=True):
      st.subheader("1. Patient Demographics")
      c1, c2, c3 = st.columns([1.5, 2, 2])
      with c1:
        entry_date = st.date_input("Date", ph_now.date())
      with c2:
        entry_time_str = civilian_time_input_field(
            "Time", key_suffix=f"gnu_{form_key_slug}_time"
        )
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
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)

      st.subheader("2. Hospitalization Plan")
      c_h1, c_h2, c_h3 = st.columns(3)
      with c_h1:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0
        )
      with c_h2:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with c_h3:
        patient_status = st.selectbox(
            "Patient Status", ["ACTIVE", "CAB", "DISCHARGED", "MGH"], index=0
        )

      curr_date_str = entry_date.strftime("%m/%d/%Y")

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician Name",
            value="",
            key=f"gnu_{form_key_slug}_att",
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key=f"gnu_{form_key_slug}_spec",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      cm_list_key = f"cm_list_{form_key_slug}"
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault(cm_list_key, [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get(cm_list_key):
        st.markdown("**Current Co-Management Doctors Added:**")
        for idx, cm in enumerate(st.session_state[cm_list_key]):
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      st.subheader("4. Clinical and Diagnostic Details")
      diagnosis_text = st.text_area("Clinical Diagnosis", value="").strip().upper()

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      diagnostic_exams_text = st.text_area(
          "Diagnostic Examinations", value="", key=f"gnu_{form_key_slug}_diags"
      ).strip().upper()
      medications_text = st.text_area(
          "Medications", value="", key=f"gnu_{form_key_slug}_meds"
      ).strip().upper()
      special_endorsements_text = st.text_area(
          "Special Endorsements", value="", key=f"gnu_{form_key_slug}_ends"
      ).strip().upper()

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()
        existing_record = check_existing_patient_ai(
            gnu_title, last_name, first_name, curr_date_str
        )
        if existing_record:
          st.info(
              f"🤖 AI Checker: Patient {last_name}, {first_name} already exists"
              f" on {curr_date_str}. Additional department info has been"
              " merged into their record."
          )

        final_attending = (
            attending_physician if attending_physician else "N/A"
        )
        valid_cm = st.session_state.get(cm_list_key, [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm])
            if valid_cm
            else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm])
            if valid_cm
            else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "full_month"),
            "DATE": curr_date_str,
            "TIME": entry_time_str,
            "ROOM NO": room_no,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AGE": str(age),
            "DIAGNOSIS": sanitize_medical_text(diagnosis_text),
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "HOSPITALIZATION MODE": hosp_mode,
            "MODE OF PAYMENT": payment_selected,
            "PATIENT STATUS": patient_status,
            "PROCEDURES": sanitize_medical_text(gnu_selected_proc if gnu_selected_proc != "Select Procedure" else ""),
            "DIAGNOSTIC EXAMINATIONS": sanitize_medical_text(
                diagnostic_exams_text
            ),
            "MEDICATIONS": sanitize_medical_text(medications_text),
            "SPECIAL ENDORSEMENTS": sanitize_medical_text(
                special_endorsements_text
            ),
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet(gnu_title, row_data):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(f"Successfully saved to `{gnu_title}`!")
          st.session_state[cm_list_key] = []

  with tab_update:
    st.markdown(f"##### 🔄 Update Admitted Patient Orders (`{gnu_title}`)")
    dept_df_up = read_google_sheet(gnu_title)
    if not dept_df_up.empty and "LAST NAME" in dept_df_up.columns:
      active_patients = dept_df_up[
          ~dept_df_up.get(
              "PATIENT STATUS", pd.Series(["ACTIVE"] * len(dept_df_up))
          )
          .astype(str)
          .str.upper()
          .isin(["DISCHARGED"])
      ]
      if not active_patients.empty:
        active_patients["DISPLAY_NAME"] = (
            active_patients["LAST NAME"]
            + ", "
            + active_patients["FIRST NAME"]
            + " (Rm: "
            + active_patients.get("ROOM NO", "N/A")
            + ")"
        )
        selected_patient_display = st.selectbox(
            "Select Admitted Patient",
            sorted(active_patients["DISPLAY_NAME"].tolist()),
            key=f"sel_{form_key_slug}",
        )

        matched_row = active_patients[
            active_patients["DISPLAY_NAME"] == selected_patient_display
        ].iloc[0]
        matched_idx = active_patients[
            active_patients["DISPLAY_NAME"] == selected_patient_display
        ].index[0]

        chosen_cat_up_g = st.selectbox(
            "Select Anatomical / Surgical Category for Procedures",
            ["Select Category"] + sorted(list(ANNEX_B_CATEGORIZED_PROCEDURES.keys())),
            key=f"up_cat_g_{form_key_slug}"
        )
        up_procs_g = ""
        if chosen_cat_up_g and chosen_cat_up_g != "Select Category":
          sub_pg = sorted(ANNEX_B_CATEGORIZED_PROCEDURES[chosen_cat_up_g])
          up_procs_g = st.selectbox(
              f"Select Procedure under `{chosen_cat_up_g}`",
              ["Select Procedure"] + sub_pg,
              key=f"up_proc_g_{form_key_slug}_{chosen_cat_up_g}"
          )

        with st.form(f"update_form_{form_key_slug}"):
          st.markdown(
              f"**Patient:** `{selected_patient_display}` | **Current"
              f" Diagnosis:** `{matched_row.get('DIAGNOSIS', '')}`"
          )

          up_status = st.selectbox(
              "Update Patient Status",
              ["ACTIVE", "CAB", "DISCHARGED", "MGH"],
              index=0,
              key=f"st_{form_key_slug}",
          )

          up_diags = st.text_area(
              "New / Additional Diagnostic Examinations",
              value="",
              placeholder="Enter new diagnostic exams...",
              key=f"dg_{form_key_slug}",
          ).strip().upper()
          up_meds = st.text_area(
              "New / Additional Medications",
              value="",
              placeholder="Enter new medications/orders...",
              key=f"md_{form_key_slug}",
          ).strip().upper()
          up_ends = st.text_area(
              "Special Endorsements / Notes",
              value="",
              placeholder="Enter notes or updates...",
              key=f"en_{form_key_slug}",
          ).strip().upper()

          st.markdown("---")
          confirm_password_gnu = st.text_input(
              "🔒 Re-enter Your Account Password to Authorize Update",
              type="password",
              key=f"reauth_pwd_gnu_{form_key_slug}",
          )

          submit_update = st.form_submit_button("💾 Save Patient Orders Update")
          if submit_update:
            current_username = st.session_state.get("username", "").strip().lower()
            user_record = USER_DATABASE.get(current_username, {})
            stored_hash = user_record.get("password", "")

            if not confirm_password_gnu or hash_password(confirm_password_gnu) != stored_hash:
              st.error(
                  "🚨 Authorization Error: Incorrect account password. Update"
                  " aborted."
              )
              st.stop()

            now_ts = get_ph_time().strftime(
                f"[%m/%d/%Y %I:%M %p - {st.session_state['name']}]"
            )
            if up_status:
              dept_df_up.loc[matched_idx, "PATIENT STATUS"] = up_status
            if up_procs_g and up_procs_g != "Select Procedure":
              existing_p = (
                  str(dept_df_up.loc[matched_idx, "PROCEDURES"])
                  if "PROCEDURES" in dept_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_procs_g}"
              dept_df_up.loc[matched_idx, "PROCEDURES"] = (
                  f"{existing_p}\n{bullet_item}".strip()
                  if existing_p and existing_p != "NAN"
                  else bullet_item
              )
            if up_diags:
              existing_d = (
                  str(dept_df_up.loc[matched_idx, "DIAGNOSTIC EXAMINATIONS"])
                  if "DIAGNOSTIC EXAMINATIONS" in dept_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_diags}"
              dept_df_up.loc[matched_idx, "DIAGNOSTIC EXAMINATIONS"] = (
                  f"{existing_d}\n{bullet_item}".strip()
                  if existing_d and existing_d != "NAN"
                  else bullet_item
              )
            if up_meds:
              existing_m = (
                  str(dept_df_up.loc[matched_idx, "MEDICATIONS"])
                  if "MEDICATIONS" in dept_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_meds}"
              dept_df_up.loc[matched_idx, "MEDICATIONS"] = (
                  f"{existing_m}\n{bullet_item}".strip()
                  if existing_m and existing_m != "NAN"
                  else bullet_item
              )
            if up_ends:
              existing_e = (
                  str(dept_df_up.loc[matched_idx, "SPECIAL ENDORSEMENTS"])
                  if "SPECIAL ENDORSEMENTS" in dept_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_ends}"
              dept_df_up.loc[matched_idx, "SPECIAL ENDORSEMENTS"] = (
                  f"{existing_e}\n{bullet_item}".strip()
                  if existing_e and existing_e != "NAN"
                  else bullet_item
              )

            if update_google_sheet_from_df(gnu_title, dept_df_up):
              st.cache_data.clear()
              st.session_state["df_cache"] = {}
              st.success(
                  "Successfully updated patient medical orders and treatment"
                  " plan with timestamped bullet entries!"
              )
              st.rerun()
      else:
        st.info("No active admitted patients found in this unit.")
    else:
      st.info("No patient records available in this department yet.")

  with tab_roster:
    render_department_live_roster(gnu_title)

# ---------------------------------------------------------
# FORM 1: Emergency Care Complex (ECC)
# ---------------------------------------------------------
elif selected_sheet == "Emergency Care Complex (ECC)":
  st.header("🚑 Emergency Care Complex (Standalone Registration)")
  ph_now = get_ph_time()

  tab_reg, tab_update_inpatient, tab_roster = st.tabs([
      "📝 New ECC Procedure/Visit Registration",
      "🔄 Update Inpatient Orders (GNU / SCU)",
      "📋 Active Live Roster",
  ])

  with tab_reg:
    with st.form("ecc_form", clear_on_submit=True):
      st.subheader("1. Patient Demographics & Encounter Details")
      
      c_dt1, c_dt2, c_dt3 = st.columns([1.5, 2, 2])
      with c_dt1:
        entry_date = st.date_input("Date", ph_now.date())
      with c_dt2:
        entry_time_str = civilian_time_input_field("Time", key_suffix="ecc_time")
      with c_dt3:
        room_no = st.text_input("Room No.", value="").strip().upper()

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
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)

      st.subheader("2. Hospitalization Plan")
      c_h1, c_h2, c_h3, c_h4 = st.columns(4)
      with c_h1:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0
        )
      with c_h2:
        case_type = st.selectbox(
            "Case Type",
            [
                "Select Type",
                "HOUSE CASE (WALK-IN)",
                "PRIVATE CASE",
            ],
            index=0,
        )
      with c_h3:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with c_h4:
        admitted_to = st.selectbox("Admitted To", HOSPITAL_UNIT_AREAS, index=0)

      curr_date_str = entry_date.strftime("%m/%d/%Y")

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician Name", value="", key="ecc_att_input"
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key="ecc_spec_input",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault("cm_list_ecc", [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get("cm_list_ecc"):
        st.markdown("**Current Co-Management Doctors Added:**")
        for idx, cm in enumerate(st.session_state["cm_list_ecc"]):
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      st.subheader("4. Clinical and Diagnostic Details")
      diagnosis_text = st.text_area("Clinical Diagnosis", value="").strip().upper()

      disease_options = sorted([
          "ACUTE GASTROENTERITIS",
          "DENGUE FEVER",
          "HYPERTENSION",
          "GASTROESOPHAGEAL REFLUX DISEASE",
          "URINARY TRACT INFECTION",
          "BRONCHIAL ASTHMA",
          "DIABETES MELLITUS",
          "RESPIRATORY TRACT INECTION",
          "ELECTROLYTE IMBALANCE",
          "ACUTE TONSILLOPHARYNGITIS",
          "ANIMAL BITE",
          "VERTIGO",
          "HYPERSENSITIVITY REACTION",
          "INFECTED WOUND",
          "ACUTE CORONARY SYNDROME",
          "SYSTEMIC VIRAL ILLNESS",
          "FRACTURE",
          "OTHERS",
      ])
      disease_options = sorted([x for x in disease_options if x != "OTHERS"]) + ["OTHERS"]
      selected_diseases = st.multiselect("Disease Category", disease_options)

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      ecc_procedures = st.text_area("Procedures Performed", value="", key="ecc_procs").strip().upper()
      ecc_diagnostic_exams = st.text_area(
          "Diagnostic Examinations", value="", key="ecc_diags"
      ).strip().upper()
      ecc_medications = st.text_area("Medications", value="", key="ecc_meds").strip().upper()
      ecc_special_endorsements = st.text_area(
          "Special Endorsements", value="", key="ecc_ends"
      ).strip().upper()

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()

        final_attending = (
            attending_physician if attending_physician else "N/A"
        )
        valid_cm = st.session_state.get("cm_list_ecc", [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm])
            if valid_cm
            else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm])
            if valid_cm
            else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "full_month"),
            "DATE": curr_date_str,
            "TIME": entry_time_str,
            "ROOM NO": room_no,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AGE": str(age),
            "DIAGNOSIS": sanitize_medical_text(diagnosis_text),
            "DISEASE CATEGORY": (
                ", ".join(selected_diseases) if selected_diseases else "NONE"
            ),
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "HOSPITALIZATION MODE": hosp_mode,
            "CASE TYPE": case_type,
            "MODE OF PAYMENT": payment_selected,
            "ADMITTED TO": admitted_to,
            "PROCEDURES": sanitize_medical_text(ecc_procedures),
            "DIAGNOSTIC EXAMINATIONS": sanitize_medical_text(
                ecc_diagnostic_exams
            ),
            "MEDICATIONS": sanitize_medical_text(ecc_medications),
            "SPECIAL ENDORSEMENTS": sanitize_medical_text(
                ecc_special_endorsements
            ),
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet(
            "Emergency Care Complex (ECC)", row_data
        ):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              "Successfully saved to ECC register!"
          )
          st.session_state["cm_list_ecc"] = []

  with tab_update_inpatient:
    render_inpatient_order_updater_form("ECC")

  with tab_roster:
    render_department_live_roster("Emergency Care Complex (ECC)")

# ---------------------------------------------------------
# FORM 2: Endoscopy Unit (ENDO)
# ---------------------------------------------------------
elif selected_sheet == "Endoscopy Unit (ENDO)":
  st.header("🔬 Endoscopy Unit (Standalone Registration)")
  ph_now = get_ph_time()

  tab_reg, tab_update_inpatient, tab_roster = st.tabs([
      "📝 New Endoscopy Procedure Registration",
      "🔄 Update Inpatient Orders (GNU / SCU)",
      "📋 Active Live Roster",
  ])

  with tab_reg:
    st.markdown("##### 🔍 PhilHealth RVS Code Lookup & Master Directory")
    search_rvs_endo = st.text_input("Search / Enter Specific RVS Code Directly", value="", key="search_rvs_endo_top").strip().upper()
    endo_selected_proc = ""
    chosen_cat_endo = "NONE"
    matched_rvs_list = []
    if search_rvs_endo:
      for cat_k, p_list in ANNEX_B_CATEGORIZED_PROCEDURES.items():
        for p_item in p_list:
          if search_rvs_endo in p_item:
            matched_rvs_list.append(f"[{cat_k}] {p_item}")
      if matched_rvs_list:
        selected_searched_endo = st.selectbox("Matching RVS Codes Found", ["Select Match"] + matched_rvs_list, key="sel_match_endo_top")
        if selected_searched_endo and selected_searched_endo != "Select Match":
          endo_selected_proc = selected_searched_endo
      else:
        endo_selected_proc = f"{search_rvs_endo} - CUSTOM RVS ENTRY"
    else:
      chosen_cat_endo = st.selectbox(
          "Select Anatomical / Surgical Category",
          ["Select Category"] + sorted(list(ANNEX_B_CATEGORIZED_PROCEDURES.keys())),
          key="endo_cat_top"
      )
      if chosen_cat_endo and chosen_cat_endo != "Select Category":
        sub_endo = sorted(ANNEX_B_CATEGORIZED_PROCEDURES[chosen_cat_endo])
        endo_selected_proc = st.selectbox(
            f"PhilHealth Case Rate (RVS Code) under `{chosen_cat_endo}`",
            ["Select Procedure"] + sub_endo,
            key=f"endo_proc_sel_{chosen_cat_endo}"
        )

    with st.form("endo_form", clear_on_submit=True):
      st.subheader("1. Patient Demographics")
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
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)

      c_d1, c_d2, c_d3 = st.columns(3)
      with c_d1:
        entry_date = st.date_input("Procedure Date", ph_now.date())
      with c_d2:
        sched_time_str = civilian_time_input_field(
            "Scheduled Time", key_suffix="endo_sched"
        )
      with c_d3:
        actual_time_str = civilian_time_input_field(
            "Actual Time", key_suffix="endo_actual"
        )

      st.subheader("2. Hospitalization Plan")
      ch1, ch2, ch3 = st.columns(3)
      with ch1:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0
        )
      with ch2:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with ch3:
        patient_status = st.selectbox(
            "Patient Status", ["ACTIVE", "DISCHARGED", "MAY GO HOME"], index=0
        )

      curr_date_str = entry_date.strftime("%m/%d/%Y")

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician Name", value="", key="endo_att_input"
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Attending Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key="endo_spec_input",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault("cm_list_endo", [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get("cm_list_endo"):
        st.markdown("**Current Co-Management Doctors Added:**")
        for cm in st.session_state["cm_list_endo"]:
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      surgeon = st.text_input(
          "Surgeon / Endoscopist / Proceduralist", value=""
      ).strip().upper()
      surgeon_spec = st.selectbox(
          "Surgeon / Proceduralist Specialization",
          SPECIALTY_DROPDOWN_OPTIONS,
          index=0,
      )
      anesthesiologist = st.text_input("Anesthesiologist Name", value="").strip().upper()
      anes_spec = st.selectbox(
          "Anesthesiologist Specialization",
          SPECIALTY_DROPDOWN_OPTIONS,
          index=0,
      )

      st.subheader("4. Clinical and Diagnostic Details")
      cd1, cd2 = st.columns(2)
      with cd1:
        diagnosis_text = st.text_input("Clinical Diagnosis", value="").strip().upper()
      with cd2:
        procedure_text = st.text_input("Procedure Name", value="").strip().upper()

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      c_p1, c_p2 = st.columns(2)
      with c_p1:
        endo_pkg_bundle = st.selectbox(
            "Hospital Package Bundle",
            HOSPITAL_PACKAGE_BUNDLES,
            index=0,
            key="endo_pkg_bundle"
        )
      with c_p2:
        procedure_complexity = st.selectbox(
            "Procedure Complexity",
            ["Select Complexity", "Diagnostics", "Therapeutics", "Diagnostics & Therapeutics", "Major", "Medium", "Minor"],
            index=0,
            key="endo_proc_complexity"
        )

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()

        final_attending = attending_physician if attending_physician else "N/A"
        valid_cm = st.session_state.get("cm_list_endo", [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm]) if valid_cm else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm]) if valid_cm else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "mixed"),
            "DATE": curr_date_str,
            "SCHEDULED TIME": sched_time_str,
            "ACTUAL TIME": actual_time_str,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AGE": age,
            "DIAGNOSIS": sanitize_medical_text(diagnosis_text),
            "PROCEDURE": sanitize_medical_text(procedure_text),
            "PROCEDURE CATEGORY": chosen_cat_endo if chosen_cat_endo != "Select Category" else "NONE",
            "HOSPITAL PACKAGE BUNDLE": endo_pkg_bundle,
            "PHILHEALTH CASE RATE (RVS CODE)": endo_selected_proc if endo_selected_proc != "Select Procedure" else "NONE",
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "SURGEON / PROCEDURALIST": surgeon if surgeon else "N/A",
            "SURGEON SPECIALIZATION": surgeon_spec if surgeon else "N/A",
            "ANESTHESIOLOGIST": (
                anesthesiologist if anesthesiologist else "N/A"
            ),
            "ANESTHESIOLOGIST SPECIALIZATION": (
                anes_spec if anesthesiologist else "N/A"
            ),
            "PROCEDURE COMPLEXITY": procedure_complexity,
            "HOSPITALIZATION MODE": hosp_mode,
            "MODE OF PAYMENT": payment_selected,
            "PATIENT STATUS": patient_status,
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet("Endoscopy Unit (ENDO)", row_data):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              "Successfully saved to Endoscopy register!"
          )
          st.session_state["cm_list_endo"] = []

  with tab_update_inpatient:
    render_inpatient_order_updater_form("ENDO")

  with tab_roster:
    render_department_live_roster("Endoscopy Unit (ENDO)")

# ---------------------------------------------------------
# FORM 3: Hemodialysis Unit (HDU)
# ---------------------------------------------------------
elif selected_sheet == "Hemodialysis Unit (HDU)":
  hdu_icon_html = get_custom_icon_html("medical_icon.png", width=38)
  st.markdown(
      f"<h2>{hdu_icon_html} Hemodialysis Unit Patient Registration & Update</h2>",
      unsafe_allow_html=True,
  )
  ph_now = get_ph_time()

  tab_reg, tab_update, tab_roster = st.tabs(
      ["📝 New Session Registration", "🔄 Update Admitted Patient Orders", "📋 Active Live Roster"]
  )

  with tab_reg:
    with st.form("hdu_form", clear_on_submit=True):
      st.subheader("1. Patient Demographics")
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
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)

      c_d1, c_d2 = st.columns([1, 1])
      with c_d1:
        entry_date = st.date_input("Dialysis Date", datetime.today())
      with c_d2:
        shift_set = st.selectbox(
            "Dialysis Shift Slot",
            ["Select Slot", "1ST SET", "2ND SET", "3RD SET", "ON-CALL"],
            index=0,
        )

      curr_date_str = entry_date.strftime("%B %d, %Y")

      st.subheader("2. Hospitalization Plan")
      c8, c9, c10, c11 = st.columns(4)
      with c8:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "Outpatient", "Inpatient"], index=0
        )
      with c9:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with c10:
        patient_status = st.selectbox(
            "Patient Status", ["Active", "May Go Home", "Discharged"], index=0
        )
      with c11:
        pass

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician", value="", key="hdu_att_input"
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Attending Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key="hdu_spec_input",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      cm_list_key = "cm_list_hdu"
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault(cm_list_key, [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get(cm_list_key):
        st.markdown("**Current Co-Management Doctors Added:**")
        for cm in st.session_state[cm_list_key]:
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      st.subheader("4. Clinical and Diagnostic Details")
      diagnosis = st.text_input("Diagnosis", value="").strip().upper()

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      hdu_procedures = st.text_area("Procedures", value="", key="hdu_procs").strip().upper()
      hdu_diagnostic_exams = st.text_area(
          "Diagnostic Examinations", value="", key="hdu_diags"
      ).strip().upper()
      hdu_medications = st.text_area("Medications", value="", key="hdu_meds").strip().upper()
      hdu_special_endorsements = st.text_area(
          "Special Endorsements", value="", key="hdu_ends"
      ).strip().upper()

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()

        epoch = datetime(1899, 12, 30)
        selected_dt = datetime.combine(entry_date, datetime.min.time())
        if selected_dt >= epoch:
          true_date = str((selected_dt - epoch).days)
        else:
          true_date = "0"

        final_attending = (
            attending_physician if attending_physician else "N/A"
        )
        valid_cm = st.session_state.get(cm_list_key, [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm])
            if valid_cm
            else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm])
            if valid_cm
            else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "numeric_prefix"),
            "DATE": curr_date_str,
            "TRUE DATE": true_date,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AGE": str(age),
            "DIAGNOSIS": sanitize_medical_text(diagnosis),
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "DIALYSIS SHIFT SLOT": shift_set,
            "HOSPITALIZATION MODE": hosp_mode,
            "MODE OF PAYMENT": payment_selected,
            "PATIENT STATUS": patient_status,
            "PROCEDURES": sanitize_medical_text(hdu_procedures),
            "DIAGNOSTIC EXAMINATIONS": sanitize_medical_text(
                hdu_diagnostic_exams
            ),
            "MEDICATIONS": sanitize_medical_text(hdu_medications),
            "SPECIAL ENDORSEMENTS": sanitize_medical_text(
                hdu_special_endorsements
            ),
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet("Hemodialysis Unit (HDU)", row_data):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              "Successfully saved to `Hemodialysis Unit (HDU)`!"
          )
          st.session_state[cm_list_key] = []

  with tab_update:
    st.markdown(
        "##### 🔄 Update Admitted Patient Orders (`Hemodialysis Unit (HDU)`)"
    )
    hdu_df_up = read_google_sheet("Hemodialysis Unit (HDU)")
    if not hdu_df_up.empty and "LAST NAME" in hdu_df_up.columns:
      hdu_active = hdu_df_up[
          ~hdu_df_up.get(
              "PATIENT STATUS", pd.Series(["ACTIVE"] * len(hdu_df_up))
          )
          .astype(str)
          .str.upper()
          .isin(["DISCHARGED"])
      ]
      if not hdu_active.empty:
        hdu_active["DISPLAY_NAME"] = (
            hdu_active["LAST NAME"]
            + ", "
            + hdu_active["FIRST NAME"]
            + " (Slot: "
            + hdu_active.get("DIALYSIS SHIFT SLOT", "N/A")
            + ")"
        )
        selected_hdu_display = st.selectbox(
            "Select Patient in HDU",
            sorted(hdu_active["DISPLAY_NAME"].tolist()),
            key="sel_hdu_up",
        )

        matched_hdu_row = hdu_active[
            hdu_active["DISPLAY_NAME"] == selected_hdu_display
        ].iloc[0]
        matched_hdu_idx = hdu_active[
            hdu_active["DISPLAY_NAME"] == selected_hdu_display
        ].index[0]

        with st.form("update_form_hdu"):
          st.markdown(
              f"**Patient:** `{selected_hdu_display}` | **Current"
              f" Diagnosis:** `{matched_hdu_row.get('DIAGNOSIS', '')}`"
          )

          up_procs_hdu = st.text_area(
              "New / Additional Procedures",
              value="",
              key="up_p_hdu",
          ).strip().upper()
          up_diags_hdu = st.text_area(
              "New / Additional Diagnostic Examinations",
              value="",
              key="up_d_hdu",
          ).strip().upper()
          up_meds_hdu = st.text_area(
              "New / Additional Medications", value="", key="up_m_hdu"
          ).strip().upper()
          up_ends_hdu = st.text_area(
              "Special Endorsements / Notes", value="", key="up_e_hdu"
          ).strip().upper()

          st.markdown("---")
          confirm_password_hdu = st.text_input(
              "🔒 Re-enter Your Account Password to Authorize Update",
              type="password",
              key="reauth_pwd_hdu_form",
          )

          submit_update_hdu = st.form_submit_button(
              "💾 Save HDU Patient Orders Update"
          )
          if submit_update_hdu:
            current_username = st.session_state.get("username", "").strip().lower()
            user_record = USER_DATABASE.get(current_username, {})
            stored_hash = user_record.get("password", "")

            if not confirm_password_hdu or hash_password(confirm_password_hdu) != stored_hash:
              st.error(
                  "🚨 Authorization Error: Incorrect account password. Update"
                  " aborted."
              )
              st.stop()

            now_ts = get_ph_time().strftime(
                f"[%m/%d/%Y %I:%M %p - {st.session_state['name']}]"
            )
            if up_procs_hdu:
              ex_p = (
                  str(hdu_df_up.loc[matched_hdu_idx, "PROCEDURES"])
                  if "PROCEDURES" in hdu_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_procs_hdu}"
              hdu_df_up.loc[matched_hdu_idx, "PROCEDURES"] = (
                  f"{ex_p}\n{bullet_item}".strip()
                  if ex_p and ex_p != "NAN"
                  else bullet_item
              )
            if up_diags_hdu:
              ex_d = (
                  str(hdu_df_up.loc[matched_hdu_idx, "DIAGNOSTIC EXAMINATIONS"])
                  if "DIAGNOSTIC EXAMINATIONS" in hdu_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_diags_hdu}"
              hdu_df_up.loc[matched_hdu_idx, "DIAGNOSTIC EXAMINATIONS"] = (
                  f"{ex_d}\n{bullet_item}".strip()
                  if ex_d and ex_d != "NAN"
                  else bullet_item
              )
            if up_meds_hdu:
              ex_m = (
                  str(hdu_df_up.loc[matched_hdu_idx, "MEDICATIONS"])
                  if "MEDICATIONS" in hdu_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_meds_hdu}"
              hdu_df_up.loc[matched_hdu_idx, "MEDICATIONS"] = (
                  f"{ex_m}\n{bullet_item}".strip()
                  if ex_m and ex_m != "NAN"
                  else bullet_item
              )
            if up_ends_hdu:
              ex_e = (
                  str(hdu_df_up.loc[matched_hdu_idx, "SPECIAL ENDORSEMENTS"])
                  if "SPECIAL ENDORSEMENTS" in hdu_df_up.columns
                  else ""
              )
              bullet_item = f"• {now_ts} {up_ends_hdu}"
              hdu_df_up.loc[matched_hdu_idx, "SPECIAL ENDORSEMENTS"] = (
                  f"{ex_e}\n{bullet_item}".strip()
                  if ex_e and ex_e != "NAN"
                  else bullet_item
              )

            if update_google_sheet_from_df("Hemodialysis Unit (HDU)", hdu_df_up):
              st.cache_data.clear()
              st.session_state["df_cache"] = {}
              st.success("Successfully updated HDU patient orders with timestamped bullet entries!")
              st.rerun()
      else:
        st.info("No active patient records found in HDU.")
    else:
      st.info("No records in HDU yet.")

  with tab_roster:
    render_department_live_roster("Hemodialysis Unit (HDU)")

# ---------------------------------------------------------
# FORM 4: OBGYNE Care Complex (LRDR-OB Surgery)
# ---------------------------------------------------------
elif selected_sheet == "OBGYNE Care Complex (LRDR-OB Surgery)":
  ob_icon_html = get_custom_icon_html("pregnant_icon.png", width=38)
  st.markdown(
      f"<h2>{ob_icon_html} OBGYNE Care Complex (Standalone Registration)</h2>",
      unsafe_allow_html=True,
  )
  ph_now = get_ph_time()

  tab_reg, tab_update_inpatient, tab_roster = st.tabs([
      "📝 New OBGYNE Procedure/Surgery Registration",
      "🔄 Update Inpatient Orders (GNU / SCU)",
      "📋 Active Live Roster",
  ])

  with tab_reg:
    st.markdown("##### 🔍 PhilHealth RVS Code Lookup & Master Directory")
    search_rvs_ob = st.text_input("Search / Enter Specific RVS Code Directly", value="", key="search_rvs_ob_top").strip().upper()
    ob_selected_proc = ""
    chosen_cat_ob = "NONE"
    matched_rvs_ob = []
    if search_rvs_ob:
      for cat_k, p_list in ANNEX_B_CATEGORIZED_PROCEDURES.items():
        for p_item in p_list:
          if search_rvs_ob in p_item:
            matched_rvs_ob.append(f"[{cat_k}] {p_item}")
      if matched_rvs_ob:
        selected_searched_ob = st.selectbox("Matching RVS Codes Found", ["Select Match"] + matched_rvs_ob, key="sel_match_ob_top")
        if selected_searched_ob and selected_searched_ob != "Select Match":
          ob_selected_proc = selected_searched_ob
      else:
        ob_selected_proc = f"{search_rvs_ob} - CUSTOM RVS ENTRY"
    else:
      chosen_cat_ob = st.selectbox(
          "Select Anatomical / Surgical Category",
          ["Select Category"] + sorted(list(ANNEX_B_CATEGORIZED_PROCEDURES.keys())),
          key="ob_cat_top"
      )
      if chosen_cat_ob and chosen_cat_ob != "Select Category":
        sub_ob = sorted(ANNEX_B_CATEGORIZED_PROCEDURES[chosen_cat_ob])
        ob_selected_proc = st.selectbox(
            f"PhilHealth Case Rate (RVS Code) under `{chosen_cat_ob}`",
            ["Select Procedure"] + sub_ob,
            key=f"ob_proc_sel_{chosen_cat_ob}"
        )

    with st.form("obgyne_form", clear_on_submit=True):
      st.subheader("1. Patient Demographics")
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
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)

      c_d1, c_d2, c_d3 = st.columns(3)
      with c_d1:
        entry_date = st.date_input("Procedure Date", ph_now.date())
      with c_d2:
        sched_time_str = civilian_time_input_field(
            "Scheduled Time", key_suffix="ob_sched"
        )
      with c_d3:
        actual_time_str = civilian_time_input_field(
            "Actual Time", key_suffix="ob_actual"
        )

      st.subheader("2. Hospitalization Plan")
      ca_h, cb_h, cc_h = st.columns(3)
      with ca_h:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0
        )
      with cb_h:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with cc_h:
        patient_status = st.selectbox(
            "Patient Status", ["Active", "May Go Home", "Discharged"], index=0
        )

      curr_date_str = entry_date.strftime("%m/%d/%Y")

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician Name", value="", key="ob_att_input"
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Attending Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key="ob_spec_input",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      cm_list_key = "cm_list_ob"
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault(cm_list_key, [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get(cm_list_key):
        st.markdown("**Current Co-Management Doctors Added:**")
        for cm in st.session_state[cm_list_key]:
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      surgeon = st.text_input(
          "Surgeon / OBGYNE Primary Operator", value=""
      ).strip().upper()
      surgeon_spec = st.selectbox(
          "Surgeon Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0
      )
      anesthesiologist = st.text_input("Anesthesiologist Name", value="").strip().upper()
      anes_spec = st.selectbox(
          "Anesthesiologist Specialization",
          SPECIALTY_DROPDOWN_OPTIONS,
          index=0,
      )

      st.subheader("4. Clinical and Diagnostic Details")
      cd1, cd2 = st.columns(2)
      with cd1:
        pre_op_diagnosis = st.text_area("Pre-Op Diagnosis", value="").strip().upper()
      with cd2:
        post_op_diagnosis = st.text_area("Post-Op Diagnosis", value="").strip().upper()

      cp1, cp2 = st.columns(2)
      with cp1:
        procedure_name = st.text_input("Procedure Name", value="").strip().upper()
      with cp2:
        surgical_procedure = st.text_area(
            "Surgical Procedure", value=""
        ).strip().upper()

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      c_p1, c_p2 = st.columns(2)
      with c_p1:
        ob_pkg_bundle = st.selectbox(
            "Hospital Package Bundle",
            HOSPITAL_PACKAGE_BUNDLES,
            index=0,
            key="ob_pkg_bundle"
        )
      with c_p2:
        procedure_complexity = st.selectbox(
            "Procedure Complexity",
            ["Select Complexity", "Diagnostics", "Therapeutics", "Diagnostics & Therapeutics", "Major", "Medium", "Minor"],
            index=0,
            key="ob_proc_complexity"
        )

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()

        final_attending = attending_physician if attending_physician else "N/A"
        valid_cm = st.session_state.get(cm_list_key, [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm]) if valid_cm else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm]) if valid_cm else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "numeric_prefix"),
            "DATE": curr_date_str,
            "SCHEDULED TIME": sched_time_str,
            "ACTUAL TIME": actual_time_str,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AGE": float(age),
            "PRE-OP DIAGNOSIS": sanitize_medical_text(pre_op_diagnosis),
            "POST-OP DIAGNOSIS": sanitize_medical_text(post_op_diagnosis),
            "PROCEDURE NAME": sanitize_medical_text(procedure_name),
            "SURGICAL PROCEDURE": sanitize_medical_text(surgical_procedure),
            "PROCEDURE CATEGORY": chosen_cat_ob if chosen_cat_ob != "Select Category" else "NONE",
            "HOSPITAL PACKAGE BUNDLE": ob_pkg_bundle,
            "PHILHEALTH CASE RATE (RVS CODE)": ob_selected_proc if ob_selected_proc != "Select Procedure" else "NONE",
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "SURGEON / OBGYNE": surgeon if surgeon else "N/A",
            "SURGEON SPECIALIZATION": surgeon_spec if surgeon else "N/A",
            "ANESTHESIOLOGIST": (
                anesthesiologist if anesthesiologist else "N/A"
            ),
            "ANESTHESIOLOGIST SPECIALIZATION": (
                anes_spec if anesthesiologist else "N/A"
            ),
            "PROCEDURE COMPLEXITY": procedure_complexity,
            "HOSPITALIZATION MODE": hosp_mode,
            "MODE OF PAYMENT": payment_selected,
            "PATIENT STATUS": patient_status,
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet(
            "OBGYNE Care Complex (LRDR-OB Surgery)", row_data
        ):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              "Successfully saved to OBGYNE register!"
          )
          st.session_state[cm_list_key] = []

  with tab_update_inpatient:
    render_inpatient_order_updater_form("OBGYNE")

  with tab_roster:
    render_department_live_roster("OBGYNE Care Complex (LRDR-OB Surgery)")

# ---------------------------------------------------------
# FORM 5: Surgical Care Complex (OR Main)
# ---------------------------------------------------------
elif selected_sheet == "Surgical Care Complex (OR Main)":
  surgery_icon_html = get_custom_icon_html("surgery_icon.png", width=38)
  st.markdown(
      f"<h2>{surgery_icon_html} Surgical Care Complex (Standalone Registration)</h2>",
      unsafe_allow_html=True,
  )
  ph_now = get_ph_time()

  tab_reg, tab_update_inpatient, tab_roster = st.tabs([
      "📝 New Surgical Procedure/OR Registration",
      "🔄 Update Inpatient Orders (GNU / SCU)",
      "📋 Active Live Roster",
  ])

  with tab_reg:
    st.markdown("##### 🔍 PhilHealth RVS Code Lookup & Master Directory")
    search_rvs_scc = st.text_input("Search / Enter Specific RVS Code Directly", value="", key="search_rvs_scc_top").strip().upper()
    scc_selected_proc = ""
    chosen_cat_scc = "NONE"
    matched_rvs_scc = []
    if search_rvs_scc:
      for cat_k, p_list in ANNEX_B_CATEGORIZED_PROCEDURES.items():
        for p_item in p_list:
          if search_rvs_scc in p_item:
            matched_rvs_scc.append(f"[{cat_k}] {p_item}")
      if matched_rvs_scc:
        selected_searched_scc = st.selectbox("Matching RVS Codes Found", ["Select Match"] + matched_rvs_scc, key="sel_match_scc_top")
        if selected_searched_scc and selected_searched_scc != "Select Match":
          scc_selected_proc = selected_searched_scc
      else:
        scc_selected_proc = f"{search_rvs_scc} - CUSTOM RVS ENTRY"
    else:
      chosen_cat_scc = st.selectbox(
          "Select Anatomical / Surgical Category",
          ["Select Category"] + sorted(list(ANNEX_B_CATEGORIZED_PROCEDURES.keys())),
          key="scc_cat_top"
      )
      if chosen_cat_scc and chosen_cat_scc != "Select Category":
        sub_scc = sorted(ANNEX_B_CATEGORIZED_PROCEDURES[chosen_cat_scc])
        scc_selected_proc = st.selectbox(
            f"PhilHealth Case Rate (RVS Code) under `{chosen_cat_scc}`",
            ["Select Procedure"] + sub_scc,
            key=f"scc_proc_sel_{chosen_cat_scc}"
        )

    with st.form("scc_form", clear_on_submit=True):
      st.subheader("1. Patient Demographics")
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
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)

      c_d1, c_d2, c_d3 = st.columns(3)
      with c_d1:
        entry_date = st.date_input("Surgery Date", ph_now.date())
      with c_d2:
        sched_time_str = civilian_time_input_field(
            "Scheduled Time", key_suffix="scc_sched"
        )
      with c_d3:
        actual_time_str = civilian_time_input_field(
            "Actual Time", key_suffix="scc_actual"
        )

      st.subheader("2. Hospitalization Plan")
      ca_h, cb_h, cc_h = st.columns(3)
      with ca_h:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0
        )
      with cb_h:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with cc_h:
        patient_status = st.selectbox(
            "Patient Status", ["Active", "May Go Home", "Discharged"], index=0
        )

      curr_date_str = entry_date.strftime("%m/%d/%Y")

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician Name", value="", key="scc_att_input"
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key="scc_spec_input",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      cm_list_key = "cm_list_scc"
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault(cm_list_key, [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get(cm_list_key):
        st.markdown("**Current Co-Management Doctors Added:**")
        for cm in st.session_state[cm_list_key]:
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      surgeon = st.text_input("Primary Surgeon", value="").strip().upper()
      surgeon_spec = st.selectbox(
          "Surgeon Specialization", SPECIALTY_DROPDOWN_OPTIONS, index=0
      )
      anesthesiologist = st.text_input("Anesthesiologist Name", value="").strip().upper()
      anes_spec = st.selectbox(
          "Anesthesiologist Specialization",
          SPECIALTY_DROPDOWN_OPTIONS,
          index=0,
      )

      st.subheader("4. Clinical and Diagnostic Details")
      cd1, cd2 = st.columns(2)
      with cd1:
        pre_op_diagnosis = st.text_area("Pre-Op Diagnosis", value="").strip().upper()
      with cd2:
        post_op_diagnosis = st.text_area(
            "Post-Op Diagnosis", value=""
        ).strip().upper()

      procedure = st.text_area("Surgical Procedure", value="").strip().upper()

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      c_p1, c_p2 = st.columns(2)
      with c_p1:
        scc_pkg_bundle = st.selectbox(
            "Hospital Package Bundle",
            HOSPITAL_PACKAGE_BUNDLES,
            index=0,
            key="scc_pkg_bundle"
        )
      with c_p2:
        procedure_complexity = st.selectbox(
            "Procedure Complexity",
            ["Select Complexity", "Diagnostics", "Therapeutics", "Diagnostics & Therapeutics", "Major", "Medium", "Minor"],
            index=0,
            key="scc_proc_complexity"
        )

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()

        final_attending = attending_physician if attending_physician else "N/A"
        valid_cm = st.session_state.get(cm_list_key, [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm]) if valid_cm else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm]) if valid_cm else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "numeric_prefix"),
            "DATE": curr_date_str,
            "SCHEDULED TIME": sched_time_str,
            "ACTUAL TIME": actual_time_str,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AGE": float(age),
            "PRE-OP DIAGNOSIS": sanitize_medical_text(pre_op_diagnosis),
            "POST-OP DIAGNOSIS": sanitize_medical_text(post_op_diagnosis),
            "PROCEDURE": sanitize_medical_text(procedure),
            "PROCEDURE CATEGORY": chosen_cat_scc if chosen_cat_scc != "Select Category" else "NONE",
            "HOSPITAL PACKAGE BUNDLE": scc_pkg_bundle,
            "PHILHEALTH CASE RATE (RVS CODE)": scc_selected_proc if scc_selected_proc != "Select Procedure" else "NONE",
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "PRIMARY SURGEON": surgeon if surgeon else "N/A",
            "SURGEON SPECIALIZATION": surgeon_spec if surgeon else "N/A",
            "ANESTHESIOLOGIST": (
                anesthesiologist if anesthesiologist else "N/A"
            ),
            "ANESTHESIOLOGIST SPECIALIZATION": (
                anes_spec if anesthesiologist else "N/A"
            ),
            "PROCEDURE COMPLEXITY": procedure_complexity,
            "HOSPITALIZATION MODE": hosp_mode,
            "MODE OF PAYMENT": payment_selected,
            "PATIENT STATUS": patient_status,
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet(
            "Surgical Care Complex (OR Main)", row_data
        ):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              "Successfully saved to Surgical Care Complex register!"
          )
          st.session_state[cm_list_key] = []

  with tab_update_inpatient:
    render_inpatient_order_updater_form("SCC")

  with tab_roster:
    render_department_live_roster("Surgical Care Complex (OR Main)")

# ---------------------------------------------------------
# FORM 6: Special Care Complex (NICU-PICU-NSU/PCN-Outborn)
# ---------------------------------------------------------
elif selected_sheet == "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)":
  baby_icon_html = get_custom_icon_html("baby_feet_icon.png", width=38)
  st.markdown(
      f"<h2>{baby_icon_html} Special Care Unit Patient Registration</h2>",
      unsafe_allow_html=True,
  )
  ph_now = get_ph_time()

  tab_scu_reg, tab_scu_roster = st.tabs([
      "📝 New Admission Registration",
      "📋 Active Live Roster",
  ])

  with tab_scu_reg:
    st.info("ℹ️ **Rule Notice:** If registered in ECC as an inpatient transfer to this Special Care unit, standard re-registration is bypassed; use unit order updates or view via live roster.")

    with st.form("scu_form", clear_on_submit=True):
      st.subheader("1. Patient Demographics")
      c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 1, 1.5])
      with c1:
        last_name = st.text_input("Last Name", value="").strip().upper()
      with c2:
        first_name = st.text_input("First Name", value="").strip().upper()
      with c3:
        middle_name = st.text_input("Middle Name", value="").strip().upper()
      with c4:
        sex_options = ["Select Sex", "FEMALE", "MALE", "OTHERS"]
        sex = st.selectbox("Sex", sex_options, index=0)
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

      st.subheader("2. Hospitalization Plan")
      c10, c11, c12, c13, c14, c15 = st.columns(6)
      with c10:
        admitted_from = st.selectbox("Admitted From", HOSPITAL_UNIT_AREAS, index=0)
      with c11:
        scu_areas = ["NICU", "OUTBORN", "PCN", "PICU", "ROOM-IN", "NSU"]
        scu_areas = ["Select Area"] + sorted([x for x in scu_areas if x != "Select Area"])
        admitted_to = st.selectbox(
            "Admitted To",
            scu_areas,
            index=0,
        )
      with c12:
        transferred_to = st.selectbox("Transferred To", HOSPITAL_UNIT_AREAS, index=0)
      with c13:
        hosp_mode = st.selectbox(
            "Hospitalization Mode", ["Select Mode", "INPATIENT", "OUTPATIENT"], index=0
        )
      with c14:
        payment_options = ["Select Payment", "HMO", "PHIC", "SELF-PAY"]
        payment_selected = st.selectbox(
            "Mode of Payment",
            payment_options,
            index=0,
        )
      with c15:
        patient_status = st.selectbox(
            "Patient Status", ["ACTIVE", "CAB", "DISCHARGED", "MGH"], index=0
        )

      st.subheader("3. Medical / Surgical Care Team")
      c_doc1, c_doc2 = st.columns([2, 2])
      with c_doc1:
        attending_physician = st.text_input(
            "Attending Physician Name", value="", key="scu_att_input"
        ).strip().upper()
      with c_doc2:
        attending_spec = st.selectbox(
            "Specialization",
            SPECIALTY_DROPDOWN_OPTIONS,
            index=0,
            key="scu_spec_input",
        )

      tag_as_cm = st.form_submit_button("Tag as Co-Management")
      cm_list_key = "cm_list_scu"
      if tag_as_cm and attending_physician:
        doc_name_up = attending_physician.strip().upper()
        existing_cms = st.session_state.setdefault(cm_list_key, [])
        if not any(
            cm["name"] == doc_name_up and cm["spec"] == attending_spec
            for cm in existing_cms
        ):
          existing_cms.append({"name": doc_name_up, "spec": attending_spec})

      if st.session_state.get(cm_list_key):
        st.markdown("**Current Co-Management Doctors Added:**")
        for cm in st.session_state[cm_list_key]:
          st.write(f"- Dr. {cm['name']} ({cm['spec']})")

      st.subheader("4. Clinical and Diagnostic Details")
      diagnosis = st.text_area("Diagnosis Text", value="").strip().upper()
      diag_flags = st.multiselect(
          "Diagnosis Category", sorted(["PNEUMONIA", "SEPSIS", "PCAP", "SURGERY", "OTHERS"])
      )

      st.subheader("5. Diagnostics Procedures and Treatment Plans")
      scu_procedures = st.text_area("Procedures", value="", key="scu_procs").strip().upper()
      scu_diagnostic_exams = st.text_area(
          "Diagnostic Examinations", value="", key="scu_diags"
      ).strip().upper()
      scu_medications = st.text_area("Medications", value="", key="scu_meds").strip().upper()
      scu_special_endorsements = st.text_area(
          "Special Endorsements", value="", key="scu_ends"
      ).strip().upper()

      submitted = st.form_submit_button("Submit Record")
      if submitted:
        if (
            not last_name
            or not first_name
            or str(last_name).strip() == ""
            or str(first_name).strip() == ""
        ):
          st.error(
              "⚠️ Validation Error: Last Name and First Name are required fields."
          )
          st.stop()
        existing_record = check_existing_patient_ai(
            "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)",
            last_name,
            first_name,
            curr_date_str,
        )
        if existing_record:
          st.info(
              f"🤖 AI Checker: Patient {last_name}, {first_name} already exists"
              f" on {curr_date_str}. Additional department info has been merged"
              " into their record."
          )

        age_str_parts = []
        if age_y > 0:
          age_str_parts.append(f"{age_y} Yrs")
        if age_m > 0:
          age_str_parts.append(f"{age_m} Mos")
        if age_d > 0:
          age_str_parts.append(f"{age_d} Days")
        age_formatted = (
            ", ".join(age_str_parts) if age_str_parts else "Neonate / Infant"
        )

        final_attending = attending_physician if attending_physician else "N/A"
        valid_cm = st.session_state.get(cm_list_key, [])
        cm_names_str = (
            "; ".join([item["name"] for item in valid_cm]) if valid_cm else "N/A"
        )
        cm_specs_str = (
            "; ".join([item["spec"] for item in valid_cm]) if valid_cm else "N/A"
        )

        row_data = {
            "MONTH": get_month_str(entry_date, "numeric_prefix"),
            "DATE": curr_date_str,
            "LAST NAME": sanitize_medical_text(last_name),
            "FIRST NAME": sanitize_medical_text(first_name),
            "MIDDLE NAME": sanitize_medical_text(middle_name),
            "SEX": sex,
            "AOG": aog if aog else "N/A",
            "AGE": age_formatted,
            "DIAGNOSIS": sanitize_medical_text(diagnosis),
            "DIAGNOSIS CATEGORY": (
                ", ".join(diag_flags) if diag_flags else "NONE"
            ),
            "ADMITTED FROM": admitted_from,
            "ADMITTED TO": admitted_to,
            "TRANSFERRED TO": transferred_to,
            "ATTENDING PHYSICIAN": final_attending,
            "ATTENDING SPECIALIZATION": attending_spec,
            "CO-MANAGEMENT PHYSICIAN": cm_names_str,
            "CO-MANAGEMENT SPECIALIZATION": cm_specs_str,
            "HOSPITALIZATION MODE": hosp_mode,
            "MODE OF PAYMENT": payment_selected,
            "PATIENT STATUS": patient_status,
            "PROCEDURES": sanitize_medical_text(scu_procedures),
            "DIAGNOSTIC EXAMINATIONS": sanitize_medical_text(
                scu_diagnostic_exams
            ),
            "MEDICATIONS": sanitize_medical_text(scu_medications),
            "SPECIAL ENDORSEMENTS": sanitize_medical_text(
                scu_special_endorsements
            ),
            "CASE COUNT": 1,
            "SEEDED_TRIAL": "NO",
        }

        if append_record_to_google_sheet(
            "Special Care Complex (NICU-PICU-NSU/PCN-Outborn)", row_data
        ):
          st.cache_data.clear()
          st.session_state["df_cache"] = {}
          st.success(
              "Successfully saved to Special Care Complex!"
          )
          st.session_state[cm_list_key] = []

  with tab_scu_roster:
    render_department_live_roster("Special Care Complex (NICU-PICU-NSU/PCN-Outborn)")