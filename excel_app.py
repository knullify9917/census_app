import streamlit as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------
# 1. MUST BE FIRST STREAMLIT COMMAND
# ---------------------------------------------------------
st.set_page_config(
    page_title="MTCMC Direct Excel Data Entry System",
    layout="wide",
    initial_sidebar_state="expanded"
)

EXCEL_FILE = "MTCMC_CENSUS_MASTERFILES_SYSTEM.xlsx"

REGULAR_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
HEADER_FONT = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
HEADER_FILL = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
THIN_BORDER = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

SHEET_HEADERS = {
    "ECC TOP DISEASES": ['MONTH', 'DATE', 'TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'ACUTE GASTROENTERITIS', 'DENGUE FEVER', 'HYPERTENSION', 'GASTROESOPHAGEAL REFLUX DISEASE', 'URINARY TRACT INFECTION', 'BRONCHIAL ASTHMA', 'DIABETES MELLITUS', 'RESPIRATORY TRACT INECTION', 'ELECTROLYTE IMBALANCE', 'ACUTE TONSILLOPHARYNGITIS', 'ANIMAL BITE', 'VERTIGO', 'HYPERSENSITIVITY REACTION', 'INFECTED WOUND', 'ACUTE CORONARY SYNDROME', 'SYSTEMIC VIRAL ILLNESS', 'FRACTURE', 'OTHER CASES', 'PHYSICIAN', 'NEUROLOGY', 'IM & CARDIO', 'PULMO', 'GENERAL SURGERY', 'ORTHOPEDICS', 'NEPHROLOGY', 'UROLOGY', 'TCVS', 'OBGYNE', 'PEDIATRICS', 'FAMILY MED', 'IPD', 'OPD', 'ICU', 'PICU', 'CASE COUNT'],
    "ENDO": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'PHYSICIAN', 'GASTROENTEROLOGIST', 'ENT', 'PULMONOLOGIST', 'ANESTHESIOLOGIST', 'ANESTHESIA', 'GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES', 'THERAPEUTIC', 'DIAGNOSTICS', 'IPD', 'OPD', 'HMO', 'PHIC', 'SELF-PAY', 'CASE COUNT'],
    "HDU": ['MONTH', 'DATE', 'TRUE DATE', 'PATIENT', 'DIAGNOSIS', '1ST SET', '2ND SET', '3RD SET', 'ONCALL', 'OPD', 'IPD', 'PHYSICIAN', 'NEPHROLOGY', 'CASE COUNT'],
    "OBGYNE CASES": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'CS PRIMARY', 'CS', 'NSD', 'D&C', 'HYSTERECTOMY', 'EXLAP', 'OTHER PROCEDURES', 'NST', 'SURGEON', 'OBGYNE', 'ANESTHESIOLOGIST', 'ANESTHESIA', 'IPD', 'OPD', 'MAJOR', 'MINOR', 'DIAGNOSTIC', 'KIT', 'HMO', 'SELF-PAY', 'CASE COUNT'],
    "SCC CASES": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'EXCISION BIOPSY', 'INCISION AND DRAINAGE', 'WOUND SUTURING & CLOSING AND CHANGE OF DRESSING', 'PLEURAL CATH INSERTION', 'COLOSTOMY', 'DEBRIDEMENT', 'ANAL BIOPSY', 'CORE NEEDLE BIOPSY', 'THYROIDECTOMY', 'PAROTIDECTOMY', 'MASTECTOMY', 'CHOLECYSTECTOMY', 'APPENDECTOMY', 'TONSILLECTOMY', 'HERNIORRHAPY', 'CHANGE OF TRACHEOSTOMY', 'LAPAROTOMY', 'GASTROSTOMY TUBE INSERTION', 'OPTHA SURGERY', 'PLASTIC SURGERY', 'SPINE SURGERY', 'CRANIOTOMY', 'MASTOIDECTOMY', 'TYMPANOPLASTY', 'MAXILLECTOMY', 'ORTHO SURGERY', 'MICROLARYNGEAL SURGERY', 'HYSTEROSCOPY', 'ULTRASOUND GUIDED', 'MIS', 'AVF', 'IJ CATH', 'PERM CATH/ FEMORAL CATH', 'PROCTOSCOPY', 'CHOLEDOSCOPY', 'DENTAL PROCEDURES', 'OTHER PROCEDURES', 'SURGEON', 'GENERAL SURGERY', 'OPHTHALMOLOGY', 'NEUROSURGERY', 'INTERVENTIONAL RADIOLOGY', 'ORTHOPEDICS', 'EENT', 'COLORECTAL', 'UROLOGY', 'DENTAL SURGERY', 'TCVS', 'PEDIATRIC SURGERY', 'OBGYNE', 'ANESTHESIOLOGIST', 'ANESTHESIA', 'IPD', 'OPD', 'MAJOR', 'MEDIUM', 'MINOR', 'DIAGNOSTICS', 'KIT', 'HMO', 'PHIC', 'SELF-PAY', 'CASE COUNT'],
    "SCU CASES": ['MONTH', 'DATE', 'PATIENT', 'AOG', 'AGE (YEAR)', 'AGE (MONTH)', 'AGE (DAY)', 'MALE', 'FEMALE', 'DIAGNOSIS', 'PNEUMONIA', 'SEPSIS', 'PCAP', 'SURGERY', 'ER', 'GNU', 'NICU', 'PICU', 'OUTBORN', 'NSU', 'ATTENDING PHYSICIAN', 'PEDIATRICS', 'NEONATOLOGY', 'PULMONOLOGY', 'HEMETOLOGY / ONCOLOGY', 'NEUROSURGERY', 'GENERAL SURGERY', 'CASE COUNT']
}

def ensure_excel_and_sheets_exist():
    if not os.path.exists(EXCEL_FILE):
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
    else:
        wb = openpyxl.load_workbook(EXCEL_FILE)

    modified = False
    if "Dashboard & Summary" not in wb.sheetnames:
        ws_sum = wb.create_sheet(title="Dashboard & Summary", index=0)
        ws_sum.cell(row=1, column=1, value="METRO TERESA MEDICAL CENTER (MTCMC)").font = BOLD_FONT
        headers = ['Department / Module', 'Total Census Records', 'Active Column Count', 'Source Masterfile']
        for c, h in enumerate(headers, 1):
            cell = ws_sum.cell(row=4, column=c, value=h)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
        modified = True

    for s_name, cols in SHEET_HEADERS.items():
        if s_name not in wb.sheetnames:
            ws = wb.create_sheet(title=s_name)
            ws.views.sheetView[0].showGridLines = True
            ws.cell(row=1, column=1, value=f"MTCMC CLINICAL CENSUS - {s_name} MASTERFILE").font = BOLD_FONT
            for c_idx, col_name in enumerate(cols, start=1):
                cell = ws.cell(row=4, column=c_idx, value=col_name)
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = Alignment(horizontal='center', vertical='center')
                cell.border = THIN_BORDER
            ws.freeze_panes = "A5"
            modified = True

    if modified:
        wb.save(EXCEL_FILE)

def read_excel_sheet(sheet_name):
    ensure_excel_and_sheets_exist()
    try:
        xl = pd.ExcelFile(EXCEL_FILE, engine='openpyxl')
        if sheet_name in xl.sheet_names:
            return pd.read_excel(xl, sheet_name=sheet_name, skiprows=3)
    except Exception as e:
        st.warning(f"Note: Could not load sheet '{sheet_name}'.")
    return pd.DataFrame()

# Initialize Excel Structure
ensure_excel_and_sheets_exist()

# UI Layout
st.title("📊 MTCMC Direct Excel Data Entry Application")
st.markdown("Use the **left sidebar** to select a department worksheet.")

MODULES = ["ECC TOP DISEASES", "ENDO", "HDU", "OBGYNE CASES", "SCC CASES", "SCU CASES"]
selected_sheet = st.sidebar.selectbox("Select Target Excel Sheet", MODULES)

st.subheader(f"Active Department Worksheet: `{selected_sheet}`")

sheet_df = read_excel_sheet(selected_sheet)
if not sheet_df.empty:
    st.dataframe(sheet_df.tail(10), use_container_width=True)
    st.info(f"Total Rows in Sheet `{selected_sheet}`: {len(sheet_df)}")
else:
    st.info(f"Sheet `{selected_sheet}` is currently empty and ready for data entry.")