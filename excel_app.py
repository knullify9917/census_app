import streamlit as st
import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------
# FILE CONFIGURATION & STYLING DEFAULTS
# ---------------------------------------------------------
EXCEL_FILE = "MTCMC_CENSUS_MASTERFILES_SYSTEM.xlsx"

REGULAR_FONT = Font(name="Calibri", size=10)
BOLD_FONT = Font(name="Calibri", size=10, bold=True)
THIN_BORDER = Border(
    left=Side(style='thin', color='D9D9D9'),
    right=Side(style='thin', color='D9D9D9'),
    top=Side(style='thin', color='D9D9D9'),
    bottom=Side(style='thin', color='D9D9D9')
)

st.set_page_config(
    page_title="MTCMC Direct Excel Data Entry System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# HELPER FUNCTIONS FOR DIRECT EXCEL WRITING
# ---------------------------------------------------------
def get_month_str(date_obj, fmt_style="numeric_prefix"):
    if not date_obj:
        return ""
    month_num = date_obj.month
    month_name = date_obj.strftime("%B").upper()
    if fmt_style == "numeric_prefix":  # e.g., "7.JULY"
        return f"{month_num}.{month_name}"
    elif fmt_style == "full_month":    # e.g., "August"
        return date_obj.strftime("%B")
    elif fmt_style == "mixed":         # e.g., "7.July "
        return f"{month_num}.{date_obj.strftime('%B')} "
    return month_name

def append_record_to_excel(sheet_name, row_dict):
    """Appends a row directly to the specified Excel worksheet with matching cell styles."""
    if not os.path.exists(EXCEL_FILE):
        st.error(f"Excel file '{EXCEL_FILE}' not found. Please verify the file path.")
        return False

    wb = openpyxl.load_workbook(EXCEL_FILE)
    if sheet_name not in wb.sheetnames:
        st.error(f"Sheet '{sheet_name}' not found in Excel workbook.")
        return False

    ws = wb[sheet_name]
    header_row = 4
    headers = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]

    # Determine next available data row
    target_row = ws.max_row + 1

    for c_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=target_row, column=c_idx)
        val = row_dict.get(col_name, "")
        cell.value = "" if (val is None or pd.isna(val)) else val
        
        # Apply visual styling matching masterfile template
        cell.font = REGULAR_FONT
        cell.border = THIN_BORDER
        
        if isinstance(val, (int, float)):
            cell.alignment = Alignment(horizontal='center' if val == 1 else 'right', vertical='center')
        elif isinstance(val, bool):
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(horizontal='left', vertical='center')

    # Automatically increment summary count in 'Dashboard & Summary' tab
    if "Dashboard & Summary" in wb.sheetnames:
        ws_summary = wb["Dashboard & Summary"]
        for r in range(5, ws_summary.max_row + 1):
            if ws_summary.cell(row=r, column=1).value == sheet_name:
                curr_count = ws_summary.cell(row=r, column=2).value or 0
                ws_summary.cell(row=r, column=2, value=curr_count + 1)
                break

    wb.save(EXCEL_FILE)
    return True

def read_excel_sheet(sheet_name):
    """Reads a sheet from the Excel file starting at header row 4 for display."""
    if os.path.exists(EXCEL_FILE):
        return pd.read_excel(EXCEL_FILE, sheet_name=sheet_name, skiprows=3)
    return pd.DataFrame()

# ---------------------------------------------------------
# NAVIGATION & UI LAYOUT
# ---------------------------------------------------------
st.title("📊 MTCMC Direct Excel Data Entry Application")
st.markdown("This application writes patient census data **directly into sheets within `MTCMC_CENSUS_MASTERFILES_SYSTEM.xlsx`** using openpyxl.")

MODULES = [
    "ECC TOP DISEASES",
    "ENDO",
    "HDU",
    "OBGYNE CASES",
    "SCC CASES",
    "SCU CASES"
]

selected_sheet = st.sidebar.selectbox("Select Target Excel Sheet", MODULES)

# Download workbook button in sidebar
if os.path.exists(EXCEL_FILE):
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="💾 Download Updated Excel Workbook",
            data=f,
            file_name=EXCEL_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ---------------------------------------------------------
# FORM 1: ECC TOP DISEASES
# ---------------------------------------------------------
if selected_sheet == "ECC TOP DISEASES":
    st.header("Emergency Care Center (ECC) — Target Sheet: `ECC TOP DISEASES`")
    
    with st.form("ecc_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_date = st.date_input("Date", datetime.today())
            entry_time = st.time_input("Time", datetime.now().time())
            patient_name = st.text_input("Patient Full Name")
        with c2:
            age = st.number_input("Age", min_value=0, max_value=120, value=25)
            physician = st.text_input("Attending Physician Name")
            specialty = st.selectbox("Physician Specialty", [
                "None", "NEUROLOGY", "IM & CARDIO", "PULMO", "GENERAL SURGERY", 
                "ORTHOPEDICS", "NEPHROLOGY", "UROLOGY", "TCVS", "OBGYNE", "PEDIATRICS", "FAMILY MED"
            ])
        with c3:
            location = st.selectbox("Care Location", ["OPD", "IPD", "ICU", "PICU"])
            diagnosis_text = st.text_area("Clinical Diagnosis")

        disease_options = [
            'ACUTE GASTROENTERITIS', 'DENGUE FEVER', 'HYPERTENSION', 'GASTROESOPHAGEAL REFLUX DISEASE',
            'URINARY TRACT INFECTION', 'BRONCHIAL ASTHMA', 'DIABETES MELLITUS', 'RESPIRATORY TRACT INECTION',
            'ELECTROLYTE IMBALANCE', 'ACUTE TONSILLOPHARYNGITIS', 'ANIMAL BITE', 'VERTIGO',
            'HYPERSENSITIVITY REACTION', 'INFECTED WOUND', 'ACUTE CORONARY SYNDROME', 'SYSTEMIC VIRAL ILLNESS',
            'FRACTURE', 'OTHER CASES'
        ]
        selected_diseases = st.multiselect("Select Disease Category Flags", disease_options)

        submitted = st.form_submit_button("Write Record to Excel Sheet")
        if submitted:
            row_data = {
                'MONTH': get_month_str(entry_date, "full_month"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'TIME': entry_time.strftime("%I:%M:%S %p"),
                'PATIENT': patient_name,
                'AGE': str(age),
                'DIAGNOSIS': diagnosis_text,
                'PHYSICIAN': physician,
                'IPD': (location == "IPD"),
                'OPD': (location == "OPD"),
                'ICU': (location == "ICU"),
                'PICU': (location == "PICU"),
                'CASE COUNT': 1.0
            }
            for d in selected_diseases:
                row_data[d] = 1.0
            if specialty != "None":
                row_data[specialty] = 1.0

            if append_record_to_excel("ECC TOP DISEASES", row_data):
                st.success("Successfully written to `ECC TOP DISEASES` worksheet!")

# ---------------------------------------------------------
# FORM 2: ENDO
# ---------------------------------------------------------
elif selected_sheet == "ENDO":
    st.header("Endoscopy Unit — Target Sheet: `ENDO`")
    
    with st.form("endo_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_date = st.date_input("Procedure Date", datetime.today())
            sched_time = st.time_input("Scheduled Time", datetime.now().time())
            actual_time = st.time_input("Actual Time", datetime.now().time())
            patient_name = st.text_input("Patient Name (Last, First M.I.)")
        with c2:
            age = st.number_input("Age", min_value=0, max_value=120, value=40)
            diagnosis_text = st.text_input("Diagnosis")
            procedure_text = st.text_input("Procedure Name")
            physician = st.text_input("Attending Physician")
        with c3:
            gastro = st.text_input("Gastroenterologist")
            ent = st.text_input("ENT Specialist")
            anesthesiologist = st.text_input("Anesthesiologist")

        proc_cols = ['GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES']
        selected_procs = st.multiselect("Select Procedure Flags", proc_cols)
        
        ca, cb, cc = st.columns(3)
        with ca: proc_type = st.radio("Nature", ["DIAGNOSTICS", "THERAPEUTIC"])
        with cb: setting = st.radio("Setting", ["OPD", "IPD"])
        with cc: payment = st.radio("Payment Method", ["HMO", "PHIC", "SELF-PAY"])

        submitted = st.form_submit_button("Write Record to Excel Sheet")
        if submitted:
            row_data = {
                'MONTH': get_month_str(entry_date, "mixed"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'SCHEDULED TIME': sched_time.strftime("%I:%M:%S %p"),
                'ACTUAL TIME': actual_time.strftime("%I:%M:%S %p"),
                'PATIENT': patient_name,
                'AGE': age,
                'DIAGNOSIS': diagnosis_text,
                'PROCEDURE': procedure_text,
                'PHYSICIAN': physician,
                'CASE COUNT': 1
            }
            if gastro: row_data['GASTROENTEROLOGIST'] = "Gastroenterologist"
            if ent: row_data['ENT'] = "ENT"
            if anesthesiologist:
                row_data['ANESTHESIOLOGIST'] = anesthesiologist
                row_data['ANESTHESIA'] = "Anesthesia"
            for p in selected_procs: row_data[p] = 1.0
            row_data[proc_type] = 1.0
            row_data[setting] = 1.0
            row_data[payment] = 1.0

            if append_record_to_excel("ENDO", row_data):
                st.success("Successfully written to `ENDO` worksheet!")

# ---------------------------------------------------------
# FORM 3: HDU
# ---------------------------------------------------------
elif selected_sheet == "HDU":
    st.header("Hemodialysis Unit — Target Sheet: `HDU`")
    
    with st.form("hdu_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Dialysis Date", datetime.today())
            patient_name = st.text_input("Patient Name (LAST, FIRST)")
            diagnosis = st.text_input("Diagnosis", value="CKD")
        with c2:
            physician = st.text_input("Nephrologist", value="DR. ALEJANDRO SESE JR.")
            shift_set = st.selectbox("Dialysis Shift Slot", ["1ST SET", "2ND SET", "3RD SET", "ONCALL"])
            patient_type = st.radio("Patient Type", ["OPD", "IPD"])

        submitted = st.form_submit_button("Write Record to Excel Sheet")
        if submitted:
            epoch = datetime(1899, 12, 30)
            true_date = str((datetime.combine(entry_date, datetime.min.time()) - epoch).days)
            
            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%B %d, %Y"),
                'TRUE DATE': true_date,
                'PATIENT': patient_name,
                'DIAGNOSIS': diagnosis,
                'PHYSICIAN': physician,
                'NEPHROLOGY': "NEPHROLOGY",
                shift_set: "1" if shift_set == "1ST SET" else 1.0,
                patient_type: 1.0,
                'CASE COUNT': 1.0
            }

            if append_record_to_excel("HDU", row_data):
                st.success("Successfully written to `HDU` worksheet!")

# ---------------------------------------------------------
# FORM 4: OBGYNE CASES
# ---------------------------------------------------------
elif selected_sheet == "OBGYNE CASES":
    st.header("OBGYNE Cases — Target Sheet: `OBGYNE CASES`")
    
    with st.form("obgyne_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_date = st.date_input("Procedure Date", datetime.today())
            sched_time = st.time_input("Scheduled Time", datetime.now().time())
            actual_time = st.time_input("Actual Time", datetime.now().time())
            patient_name = st.text_input("Patient Name")
        with c2:
            age = st.number_input("Age", min_value=10, max_value=100, value=30)
            diagnosis = st.text_area("OBGYNE Diagnosis")
            procedure = st.text_input("Procedure Name")
        with c3:
            surgeon = st.text_input("Surgeon / OBGYNE")
            anesthesiologist = st.text_input("Anesthesiologist")

        ca, cb, cc = st.columns(3)
        with ca:
            ob_procs = st.multiselect("Procedure Breakdown", ["CS PRIMARY", "CS", "NSD", "D&C", "HYSTERECTOMY", "EXLAP", "OTHER PROCEDURES", "NST"])
        with cb:
            complexity = st.selectbox("Complexity Tier", ["MAJOR", "MINOR", "DIAGNOSTIC"])
            setting = st.radio("Care Setting", ["IPD", "OPD"])
        with cc:
            kit_used = st.checkbox("Kit Used", value=True)
            payment = st.radio("Payment Channel", ["SELF-PAY", "HMO"])

        submitted = st.form_submit_button("Write Record to Excel Sheet")
        if submitted:
            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'SCHEDULED TIME': sched_time.strftime("%I:%M:%S %p"),
                'ACTUAL TIME': actual_time.strftime("%I:%M:%S %p"),
                'PATIENT': patient_name,
                'AGE': float(age),
                'DIAGNOSIS': diagnosis,
                'PROCEDURE': procedure,
                'SURGEON': surgeon,
                'OBGYNE': "OBGYNE",
                complexity: 1.0,
                setting: 1.0,
                payment: 1.0,
                'CASE COUNT': 1.0
            }
            if anesthesiologist:
                row_data['ANESTHESIOLOGIST'] = anesthesiologist
                row_data['ANESTHESIA'] = "ANESTHESIA"
            if kit_used: row_data['KIT'] = 1.0
            for flag in ob_procs: row_data[flag] = 1.0

            if append_record_to_excel("OBGYNE CASES", row_data):
                st.success("Successfully written to `OBGYNE CASES` worksheet!")

# ---------------------------------------------------------
# FORM 5: SCC CASES
# ---------------------------------------------------------
elif selected_sheet == "SCC CASES":
    st.header("Surgical Care Center — Target Sheet: `SCC CASES`")
    
    with st.form("scc_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_date = st.date_input("Surgery Date", datetime.today())
            sched_time = st.time_input("Scheduled Time", datetime.now().time())
            actual_time = st.time_input("Actual Time", datetime.now().time())
            patient_name = st.text_input("Patient Name")
        with c2:
            age = st.number_input("Age", min_value=0, max_value=120, value=35)
            diagnosis = st.text_area("Pre/Post-Op Diagnosis")
            procedure = st.text_area("Surgical Procedure")
        with c3:
            surgeon = st.text_input("Primary Surgeon")
            specialty = st.selectbox("Surgical Department", [
                'GENERAL SURGERY', 'OPHTHALMOLOGY', 'NEUROSURGERY', 'INTERVENTIONAL RADIOLOGY', 
                'ORTHOPEDICS', 'EENT', 'COLORECTAL', 'UROLOGY', 'DENTAL SURGERY', 'TCVS', 
                'PEDIATRIC SURGERY', 'OBGYNE'
            ])
            anesthesiologist = st.text_input("Anesthesiologist")

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

        ca, cb, cc = st.columns(3)
        with ca: complexity = st.selectbox("Complexity Tier", ["MAJOR", "MEDIUM", "MINOR", "DIAGNOSTICS"])
        with cb: setting = st.radio("Patient Setting", ["OPD", "IPD"])
        with cc: billing = st.multiselect("Billing Channels", ["PHIC", "HMO", "SELF-PAY", "KIT"])

        submitted = st.form_submit_button("Write Record to Excel Sheet")
        if submitted:
            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'SCHEDULED TIME': sched_time.strftime("%I:%M:%S %p"),
                'ACTUAL TIME': actual_time.strftime("%I:%M:%S %p"),
                'PATIENT': patient_name,
                'AGE': float(age),
                'DIAGNOSIS': diagnosis,
                'PROCEDURE': procedure,
                'SURGEON': surgeon,
                specialty: specialty,
                complexity: 1.0,
                setting: 1.0,
                'CASE COUNT': 1.0
            }
            if anesthesiologist:
                row_data['ANESTHESIOLOGIST'] = anesthesiologist
                row_data['ANESTHESIA'] = "ANESTHESIA"
            for p in selected_scc_procs: row_data[p] = 1.0
            for b in billing: row_data[b] = 1.0

            if append_record_to_excel("SCC CASES", row_data):
                st.success("Successfully written to `SCC CASES` worksheet!")

# ---------------------------------------------------------
# FORM 6: SCU CASES
# ---------------------------------------------------------
elif selected_sheet == "SCU CASES":
    st.header("Special Care Unit — Target Sheet: `SCU CASES`")
    
    with st.form("scu_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_date = st.date_input("Admission Date", datetime.today())
            patient_name = st.text_input("Patient Name (e.g., BABY BOY ...)")
            gender = st.radio("Gender", ["MALE", "FEMALE"])
            aog = st.text_input("Age of Gestation (AOG)", value="38 WEEKS")
        with c2:
            age_y = st.number_input("Age (Years)", min_value=0, max_value=18, value=0)
            age_m = st.number_input("Age (Months)", min_value=0, max_value=11, value=0)
            age_d = st.number_input("Age (Days)", min_value=0, max_value=31, value=0)
            physician = st.text_input("Attending Physician")
        with c3:
            diagnosis = st.text_area("Diagnosis Text")
            scu_unit = st.selectbox("SCU Unit", ["NICU", "PICU", "GNU", "ER", "NSU", "OUTBORN"])
            subspecialties = st.multiselect("Subspecialties", [
                "PEDIATRICS", "NEONATOLOGY", "PULMONOLOGY", 
                "HEMETOLOGY / ONCOLOGY", "NEUROSURGERY", "GENERAL SURGERY"
            ], default=["PEDIATRICS"])

        diag_flags = st.multiselect("Diagnostic Flags", ["PNEUMONIA", "SEPSIS", "PCAP", "SURGERY"])

        submitted = st.form_submit_button("Write Record to Excel Sheet")
        if submitted:
            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'PATIENT': patient_name,
                'AOG': aog if aog else None,
                'DIAGNOSIS': diagnosis,
                'ATTENDING PHYSICIAN': physician,
                scu_unit: 1.0,
                'CASE COUNT': 1
            }
            if age_y > 0: row_data['AGE (YEAR)'] = float(age_y)
            if age_m > 0: row_data['AGE (MONTH)'] = float(age_m)
            if age_d > 0: row_data['AGE (DAY)'] = float(age_d)
            
            if gender == "MALE": row_data['MALE'] = 1
            else: row_data['FEMALE'] = 1.0
            
            for d in diag_flags: row_data[d] = 1.0
            for s in subspecialties: row_data[s] = s

            if append_record_to_excel("SCU CASES", row_data):
                st.success("Successfully written to `SCU CASES` worksheet!")

# ---------------------------------------------------------
# REAL-TIME EXCEL SHEET DATA PREVIEW
# ---------------------------------------------------------
st.markdown("---")
st.subheader(f"Live Preview of Worksheet: `{selected_sheet}`")

sheet_df = read_excel_sheet(selected_sheet)
if not sheet_df.empty:
    st.dataframe(sheet_df.tail(10), use_container_width=True)
    st.info(f"Total Rows in Worksheet `{selected_sheet}`: {len(sheet_df)}")
else:
    st.warning(f"Worksheet `{selected_sheet}` is currently empty or unavailable.")