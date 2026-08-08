import streamlit as st
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from datetime import datetime
import pandas as pd
import os

# ---------------------------------------------------------
# 1. PAGE CONFIGURATION
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

# ---------------------------------------------------------
# 2. UNIFIED SPECIALTIES SORTED BY FIELD OF MEDICINE THEN ALPHABETICALLY
# ---------------------------------------------------------
SPECIALTIES_BY_FIELD = {
    "Anesthesiology & Pain Medicine": [
        "ANESTHESIOLOGY"
    ],
    "Dental & Oral Surgery": [
        "DENTAL SURGERY"
    ],
    "Diagnostic & Interventional Medicine": [
        "INTERVENTIONAL RADIOLOGY"
    ],
    "Internal Medicine & Subspecialties": [
        "GASTROENTEROLOGY",
        "HEMATOLOGY / ONCOLOGY",
        "INTERNAL MEDICINE & CARDIOLOGY",
        "NEPHROLOGY",
        "NEUROLOGY",
        "PULMONOLOGY"
    ],
    "Obstetrics & Gynecology": [
        "OBSTETRICS & GYNECOLOGY (OBGYNE)"
    ],
    "Pediatrics & Neonatology": [
        "NEONATOLOGY",
        "PEDIATRICS"
    ],
    "Primary Care & Community Medicine": [
        "FAMILY MEDICINE"
    ],
    "Surgical Specialties": [
        "COLORECTAL SURGERY",
        "EENT / ENT",
        "GENERAL SURGERY",
        "NEUROSURGERY",
        "OPHTHALMOLOGY",
        "ORTHOPEDICS",
        "PEDIATRIC SURGERY",
        "THORACIC & CARDIOVASCULAR SURGERY (TCVS)",
        "UROLOGY"
    ]
}

# Build sorted lists for Streamlit dropdowns
SPECIALTY_DROPDOWN_OPTIONS = ["None / Unspecified"]
SPECIALTY_NAME_MAP = {}

for field in sorted(SPECIALTIES_BY_FIELD.keys()):
    for spec in sorted(SPECIALTIES_BY_FIELD[field]):
        label = f"[{field}] {spec}"
        SPECIALTY_DROPDOWN_OPTIONS.append(label)
        SPECIALTY_NAME_MAP[label] = spec

SHEET_HEADERS = {
    "ECC TOP DISEASES": ['MONTH', 'DATE', 'TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'ACUTE GASTROENTERITIS', 'DENGUE FEVER', 'HYPERTENSION', 'GASTROESOPHAGEAL REFLUX DISEASE', 'URINARY TRACT INFECTION', 'BRONCHIAL ASTHMA', 'DIABETES MELLITUS', 'RESPIRATORY TRACT INECTION', 'ELECTROLYTE IMBALANCE', 'ACUTE TONSILLOPHARYNGITIS', 'ANIMAL BITE', 'VERTIGO', 'HYPERSENSITIVITY REACTION', 'INFECTED WOUND', 'ACUTE CORONARY SYNDROME', 'SYSTEMIC VIRAL ILLNESS', 'FRACTURE', 'OTHER CASES', 'PHYSICIAN', 'NEUROLOGY', 'IM & CARDIO', 'PULMO', 'GENERAL SURGERY', 'ORTHOPEDICS', 'NEPHROLOGY', 'UROLOGY', 'TCVS', 'OBGYNE', 'PEDIATRICS', 'FAMILY MED', 'IPD', 'OPD', 'ICU', 'PICU', 'CASE COUNT'],
    "ENDO": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'PHYSICIAN', 'GASTROENTEROLOGIST', 'ENT', 'PULMONOLOGIST', 'ANESTHESIOLOGIST', 'ANESTHESIA', 'GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES', 'THERAPEUTIC', 'DIAGNOSTICS', 'IPD', 'OPD', 'HMO', 'PHIC', 'SELF-PAY', 'CASE COUNT'],
    "HDU": ['MONTH', 'DATE', 'TRUE DATE', 'PATIENT', 'DIAGNOSIS', '1ST SET', '2ND SET', '3RD SET', 'ONCALL', 'OPD', 'IPD', 'PHYSICIAN', 'NEPHROLOGY', 'CASE COUNT'],
    "OBGYNE CASES": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'CS PRIMARY', 'CS', 'NSD', 'D&C', 'HYSTERECTOMY', 'EXLAP', 'OTHER PROCEDURES', 'NST', 'SURGEON', 'OBGYNE', 'ANESTHESIOLOGIST', 'ANESTHESIA', 'IPD', 'OPD', 'MAJOR', 'MINOR', 'DIAGNOSTIC', 'KIT', 'HMO', 'SELF-PAY', 'CASE COUNT'],
    "SCC CASES": ['MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'PATIENT', 'AGE', 'DIAGNOSIS', 'PROCEDURE', 'EXCISION BIOPSY', 'INCISION AND DRAINAGE', 'WOUND SUTURING & CLOSING AND CHANGE OF DRESSING', 'PLEURAL CATH INSERTION', 'COLOSTOMY', 'DEBRIDEMENT', 'ANAL BIOPSY', 'CORE NEEDLE BIOPSY', 'THYROIDECTOMY', 'PAROTIDECTOMY', 'MASTECTOMY', 'CHOLECYSTECTOMY', 'APPENDECTOMY', 'TONSILLECTOMY', 'HERNIORRHAPY', 'CHANGE OF TRACHEOSTOMY', 'LAPAROTOMY', 'GASTROSTOMY TUBE INSERTION', 'OPTHA SURGERY', 'PLASTIC SURGERY', 'SPINE SURGERY', 'CRANIOTOMY', 'MASTOIDECTOMY', 'TYMPANOPLASTY', 'MAXILLECTOMY', 'ORTHO SURGERY', 'MICROLARYNGEAL SURGERY', 'HYSTEROSCOPY', 'ULTRASOUND GUIDED', 'MIS', 'AVF', 'IJ CATH', 'PERM CATH/ FEMORAL CATH', 'PROCTOSCOPY', 'CHOLEDOSCOPY', 'DENTAL PROCEDURES', 'OTHER PROCEDURES', 'SURGEON', 'GENERAL SURGERY', 'OPHTHALMOLOGY', 'NEUROSURGERY', 'INTERVENTIONAL RADIOLOGY', 'ORTHOPEDICS', 'EENT', 'COLORECTAL', 'UROLOGY', 'DENTAL SURGERY', 'TCVS', 'PEDIATRIC SURGERY', 'OBGYNE', 'ANESTHESIOLOGIST', 'ANESTHESIA', 'IPD', 'OPD', 'MAJOR', 'MEDIUM', 'MINOR', 'DIAGNOSTICS', 'KIT', 'HMO', 'PHIC', 'SELF-PAY', 'CASE COUNT'],
    "SCU CASES": ['MONTH', 'DATE', 'PATIENT', 'AOG', 'AGE (YEAR)', 'AGE (MONTH)', 'AGE (DAY)', 'MALE', 'FEMALE', 'DIAGNOSIS', 'PNEUMONIA', 'SEPSIS', 'PCAP', 'SURGERY', 'ER', 'GNU', 'NICU', 'PICU', 'OUTBORN', 'NSU', 'ATTENDING PHYSICIAN', 'PEDIATRICS', 'NEONATOLOGY', 'PULMONOLOGY', 'HEMETOLOGY / ONCOLOGY', 'NEUROSURGERY', 'GENERAL SURGERY', 'CASE COUNT']
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

def append_record_to_excel(sheet_name, row_dict):
    ensure_excel_and_sheets_exist()
    wb = openpyxl.load_workbook(EXCEL_FILE)
    if sheet_name not in wb.sheetnames:
        return False

    ws = wb[sheet_name]
    header_row = 4
    headers = [ws.cell(row=header_row, column=c).value for c in range(1, ws.max_column + 1)]

    target_row = ws.max_row + 1

    for c_idx, col_name in enumerate(headers, start=1):
        cell = ws.cell(row=target_row, column=c_idx)
        val = row_dict.get(col_name, "")
        cell.value = "" if (val is None or pd.isna(val)) else val
        cell.font = REGULAR_FONT
        cell.border = THIN_BORDER
        if isinstance(val, (int, float)):
            cell.alignment = Alignment(horizontal='center' if val == 1 else 'right', vertical='center')
        elif isinstance(val, bool):
            cell.alignment = Alignment(horizontal='center', vertical='center')
        else:
            cell.alignment = Alignment(horizontal='left', vertical='center')

    # Update Summary Count
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
    ensure_excel_and_sheets_exist()
    try:
        xl = pd.ExcelFile(EXCEL_FILE, engine='openpyxl')
        if sheet_name in xl.sheet_names:
            return pd.read_excel(xl, sheet_name=sheet_name, skiprows=3)
    except Exception as e:
        st.warning(f"Note: Could not load sheet '{sheet_name}'.")
    return pd.DataFrame()

# Initialize file on startup
ensure_excel_and_sheets_exist()

# App Header
st.title("📊 MTCMC Direct Excel Data Entry Application")
st.markdown("Enter patient census data into the input form below. Records are written directly to **`MTCMC_CENSUS_MASTERFILES_SYSTEM.xlsx`**.")

MODULES = ["ECC TOP DISEASES", "ENDO", "HDU", "OBGYNE CASES", "SCC CASES", "SCU CASES"]
selected_sheet = st.sidebar.selectbox("Select Target Excel Sheet", MODULES)

# Sidebar Download Option
if os.path.exists(EXCEL_FILE):
    with open(EXCEL_FILE, "rb") as f:
        st.sidebar.download_button(
            label="💾 Download Excel Workbook",
            data=f,
            file_name=EXCEL_FILE,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.markdown("---")

# ---------------------------------------------------------
# FORM 1: ECC TOP DISEASES
# ---------------------------------------------------------
if selected_sheet == "ECC TOP DISEASES":
    st.header("Emergency Care Center (ECC) Data Entry Form")
    with st.form("ecc_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            entry_date = st.date_input("Date", datetime.today())
            entry_time = st.time_input("Time", datetime.now().time())
            patient_name = st.text_input("Patient Full Name")
        with c2:
            age = st.number_input("Age", min_value=0, max_value=120, value=25)
            physician = st.text_input("Attending Physician Name")
            specialty_sel = st.selectbox("Physician Specialty (Sorted by Field of Medicine)", SPECIALTY_DROPDOWN_OPTIONS)
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

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
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

            # Map specialty to ECC column names
            spec_name = SPECIALTY_NAME_MAP.get(specialty_sel, "")
            ecc_map = {
                "NEUROLOGY": "NEUROLOGY",
                "INTERNAL MEDICINE & CARDIOLOGY": "IM & CARDIO",
                "PULMONOLOGY": "PULMO",
                "GENERAL SURGERY": "GENERAL SURGERY",
                "ORTHOPEDICS": "ORTHOPEDICS",
                "NEPHROLOGY": "NEPHROLOGY",
                "UROLOGY": "UROLOGY",
                "THORACIC & CARDIOVASCULAR SURGERY (TCVS)": "TCVS",
                "OBSTETRICS & GYNECOLOGY (OBGYNE)": "OBGYNE",
                "PEDIATRICS": "PEDIATRICS",
                "FAMILY MEDICINE": "FAMILY MED"
            }
            if spec_name in ecc_map:
                row_data[ecc_map[spec_name]] = 1.0

            if append_record_to_excel("ECC TOP DISEASES", row_data):
                st.success("Successfully saved to `ECC TOP DISEASES` sheet!")

# ---------------------------------------------------------
# FORM 2: ENDO
# ---------------------------------------------------------
elif selected_sheet == "ENDO":
    st.header("Endoscopy Unit Data Entry Form")
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
            specialty_sel = st.selectbox("Attending Specialty (Sorted by Field of Medicine)", SPECIALTY_DROPDOWN_OPTIONS)
            gastro = st.text_input("Gastroenterologist")
            ent = st.text_input("ENT Specialist")
            anesthesiologist = st.text_input("Anesthesiologist")

        proc_cols = ['GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES']
        selected_procs = st.multiselect("Select Procedure Flags", proc_cols)
        
        ca, cb, cc = st.columns(3)
        with ca: proc_type = st.radio("Nature", ["DIAGNOSTICS", "THERAPEUTIC"])
        with cb: setting = st.radio("Setting", ["OPD", "IPD"])
        with cc: payment = st.radio("Payment Method", ["HMO", "PHIC", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
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
                st.success("Successfully saved to `ENDO` sheet!")

# ---------------------------------------------------------
# FORM 3: HDU
# ---------------------------------------------------------
elif selected_sheet == "HDU":
    st.header("Hemodialysis Unit Data Entry Form")
    with st.form("hdu_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            entry_date = st.date_input("Dialysis Date", datetime.today())
            patient_name = st.text_input("Patient Name (LAST, FIRST)")
            diagnosis = st.text_input("Diagnosis", value="CKD")
        with c2:
            physician = st.text_input("Nephrologist", value="DR. ALEJANDRO SESE JR.")
            specialty_sel = st.selectbox("Physician Specialty (Sorted by Field of Medicine)", SPECIALTY_DROPDOWN_OPTIONS)
            shift_set = st.selectbox("Dialysis Shift Slot", ["1ST SET", "2ND SET", "3RD SET", "ONCALL"])
            patient_type = st.radio("Patient Type", ["OPD", "IPD"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
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
                st.success("Successfully saved to `HDU` sheet!")

# ---------------------------------------------------------
# FORM 4: OBGYNE CASES
# ---------------------------------------------------------
elif selected_sheet == "OBGYNE CASES":
    st.header("OBGYNE Cases Data Entry Form")
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
            specialty_sel = st.selectbox("Attending Specialty (Sorted by Field of Medicine)", SPECIALTY_DROPDOWN_OPTIONS)
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

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
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
                st.success("Successfully saved to `OBGYNE CASES` sheet!")

# ---------------------------------------------------------
# FORM 5: SCC CASES
# ---------------------------------------------------------
elif selected_sheet == "SCC CASES":
    st.header("Surgical Care Center (SCC) Data Entry Form")
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
            specialty_sel = st.selectbox("Surgical Department / Specialty (Sorted by Field of Medicine)", SPECIALTY_DROPDOWN_OPTIONS)
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

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
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
                complexity: 1.0,
                setting: 1.0,
                'CASE COUNT': 1.0
            }

            # Map specialty selection to SCC column
            spec_name = SPECIALTY_NAME_MAP.get(specialty_sel, "")
            scc_map = {
                "GENERAL SURGERY": "GENERAL SURGERY",
                "OPHTHALMOLOGY": "OPHTHALMOLOGY",
                "NEUROSURGERY": "NEUROSURGERY",
                "INTERVENTIONAL RADIOLOGY": "INTERVENTIONAL RADIOLOGY",
                "ORTHOPEDICS": "ORTHOPEDICS",
                "EENT / ENT": "EENT",
                "COLORECTAL SURGERY": "COLORECTAL",
                "UROLOGY": "UROLOGY",
                "DENTAL SURGERY": "DENTAL SURGERY",
                "THORACIC & CARDIOVASCULAR SURGERY (TCVS)": "TCVS",
                "PEDIATRIC SURGERY": "PEDIATRIC SURGERY",
                "OBSTETRICS & GYNECOLOGY (OBGYNE)": "OBGYNE"
            }
            if spec_name in scc_map:
                row_data[scc_map[spec_name]] = scc_map[spec_name]

            if anesthesiologist:
                row_data['ANESTHESIOLOGIST'] = anesthesiologist
                row_data['ANESTHESIA'] = "ANESTHESIA"
            for p in selected_scc_procs: row_data[p] = 1.0
            for b in billing: row_data[b] = 1.0

            if append_record_to_excel("SCC CASES", row_data):
                st.success("Successfully saved to `SCC CASES` sheet!")

# ---------------------------------------------------------
# FORM 6: SCU CASES
# ---------------------------------------------------------
elif selected_sheet == "SCU CASES":
    st.header("Special Care Unit (SCU) Data Entry Form")
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
            subspecialties = st.multiselect("Subspecialties (Sorted by Field of Medicine)", SPECIALTY_DROPDOWN_OPTIONS[1:])

        diag_flags = st.multiselect("Diagnostic Flags", ["PNEUMONIA", "SEPSIS", "PCAP", "SURGERY"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
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
            
            scu_map = {
                "PEDIATRICS": "PEDIATRICS",
                "NEONATOLOGY": "NEONATOLOGY",
                "PULMONOLOGY": "PULMONOLOGY",
                "HEMATOLOGY / ONCOLOGY": "HEMETOLOGY / ONCOLOGY",
                "NEUROSURGERY": "NEUROSURGERY",
                "GENERAL SURGERY": "GENERAL SURGERY"
            }
            for s_label in subspecialties:
                s_name = SPECIALTY_NAME_MAP.get(s_label, "")
                if s_name in scu_map:
                    row_data[scu_map[s_name]] = scu_map[s_name]

            if append_record_to_excel("SCU CASES", row_data):
                st.success("Successfully saved to `SCU CASES` sheet!")

# ---------------------------------------------------------
# DATA TABLE PREVIEW
# ---------------------------------------------------------
st.markdown("---")
st.subheader(f"Live Sheet Preview: `{selected_sheet}`")

sheet_df = read_excel_sheet(selected_sheet)
if not sheet_df.empty:
    st.dataframe(sheet_df.tail(10), use_container_width=True)
    st.caption(f"Showing last 10 entries of `{selected_sheet}` (Total: {len(sheet_df)} records)")
else:
    st.info(f"Worksheet `{selected_sheet}` currently has no records.")