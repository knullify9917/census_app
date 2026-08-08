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
# 2. EXACT SPECIALTIES SORTED BY FIELD OF MEDICINE THEN ALPHABETICALLY
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

SPECIALTY_DROutpatient DepartmentOWN_OPTIONS = ["OTHERS"]
for field in sorted(SPECIALTIES_BY_FIELD.keys()):
    for spec in sorted(SPECIALTIES_BY_FIELD[field]):
        SPECIALTY_DROutpatient DepartmentOWN_OPTIONS.append(spec)

def get_spec_index(default_name):
    if default_name in SPECIALTY_DROutpatient DepartmentOWN_OPTIONS:
        return SPECIALTY_DROutpatient DepartmentOWN_OPTIONS.index(default_name)
    return 0

# ---------------------------------------------------------
# 3. STREAMLINED EXCEL SHEET HEADERS
# ---------------------------------------------------------
SHEET_HEADERS = {
    "ECC TOP DISEASES": [
        'MONTH', 'DATE', 'TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 'DIAGNOSIS', 
        'DISEASE CATEGORIES', 'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'HOSPITALIZATION MODE', 'MODE OF PAYMENT', 'TRANSFERRED TO', 'CASE COUNT'
    ],
    "ENDO": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'PROCEDURE CATEGORIES', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'SURGEON / PROCEDURALIST', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'PROCEDURE NATURE', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "HDU": [
        'MONTH', 'DATE', 'TRUE DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'DIAGNOSIS', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'DIALYSIS SHIFT SLOT', 'HOSPITALIZATION MODE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "OBGYNE CASES": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'PROCEDURE BREAKDOWN', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'SURGEON / OBGYNE', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "SCC CASES": [
        'MONTH', 'DATE', 'SCHEDULED TIME', 'ACTUAL TIME', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AGE', 
        'DIAGNOSIS', 'PROCEDURE', 'SURGICAL PROCEDURE FLAGS', 
        'ATTENDING PHYSICIAN', 'ATTENDING SPECIALIZATION', 
        'CO-MANAGEMENT PHYSICIAN', 'CO-MANAGEMENT SPECIALIZATION',
        'PRIMARY SURGEON', 'SURGEON SPECIALIZATION',
        'ANESTHESIOLOGIST', 'ANESTHESIOLOGIST SPECIALIZATION',
        'COMPLEXITY TIER', 'HOSPITALIZATION MODE', 'HOSPITAL KIT PACKAGE', 'MODE OF PAYMENT', 'CASE COUNT'
    ],
    "SCU CASES": [
        'MONTH', 'DATE', 'LAST NAME', 'FIRST NAME', 'MIDDLE NAME', 'SEX', 'AOG', 'AGE', 'DIAGNOSIS', 
        'DIAGNOSTIC FLAGS', 'ADMITTED FROM', 'ADMITTED TO', 
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

def ensure_excel_and_sheets_exist():
    need_rebuild = False
    if not os.path.exists(EXCEL_FILE):
        need_rebuild = True
    else:
        try:
            wb = openpyxl.load_workbook(EXCEL_FILE)
            for s_name, cols in SHEET_HEADERS.items():
                if s_name not in wb.sheetnames:
                    need_rebuild = True
                    break
                else:
                    ws = wb[s_name]
                    curr_cols = [ws.cell(row=4, column=c).value for c in range(1, ws.max_column + 1)]
                    if curr_cols != cols:
                        need_rebuild = True
                        break
        except Exception:
            need_rebuild = True

    if need_rebuild:
        wb = openpyxl.Workbook()
        wb.remove(wb.active)  # remove default sheet

        # Dashboard & Summary Sheet
        ws_sum = wb.create_sheet(title="Dashboard & Summary", index=0)
        ws_sum.views.sheetView[0].showGridLines = True
        ws_sum.cell(row=1, column=1, value="METRO TERESA MEDICAL CENTER (MTCMC)").font = BOLD_FONT
        ws_sum.cell(row=2, column=1, value="Census Masterfile Registry & Data Entry Dashboard").font = REGULAR_FONT
        sum_headers = ['Department / Module', 'Total Census Records', 'Active Column Count', 'Source Masterfile']
        for c, h in enumerate(sum_headers, 1):
            cell = ws_sum.cell(row=4, column=c, value=h)
            cell.fill = HEADER_FILL
            cell.font = HEADER_FONT
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border = THIN_BORDER

        for r_idx, (s_name, cols) in enumerate(SHEET_HEADERS.items(), start=5):
            ws_sum.cell(row=r_idx, column=1, value=s_name).font = BOLD_FONT
            ws_sum.cell(row=r_idx, column=2, value=0).font = REGULAR_FONT
            ws_sum.cell(row=r_idx, column=3, value=len(cols)).font = REGULAR_FONT
            ws_sum.cell(row=r_idx, column=4, value=f"MTCMC CENSUS - {s_name} MASTERFILE").font = REGULAR_FONT
            for c in range(1, 5):
                cell = ws_sum.cell(row=r_idx, column=c)
                cell.border = THIN_BORDER
                if c in [2, 3]:
                    cell.alignment = Alignment(horizontal='center', vertical='center')

        for c in range(1, 5):
            col_letter = openpyxl.utils.get_column_letter(c)
            ws_sum.column_dimensions[col_letter].width = 32

        # Create Department Sheets
        for s_name, cols in SHEET_HEADERS.items():
            ws = wb.create_sheet(title=s_name)
            ws.views.sheetView[0].showGridLines = True
            ws.cell(row=1, column=1, value=f"MTCMC CLINICAL CENSUS - {s_name} MASTERFILE").font = BOLD_FONT
            ws.cell(row=2, column=1, value="Streamlined Clinical Census Register").font = REGULAR_FONT

            for c_idx, col_name in enumerate(cols, start=1):
                cell = ws.cell(row=4, column=c_idx, value=col_name)
                cell.fill = HEADER_FILL
                cell.font = HEADER_FONT
                cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
                cell.border = THIN_BORDER
                col_letter = openpyxl.utils.get_column_letter(c_idx)
                ws.column_dimensions[col_letter].width = max(len(col_name) + 4, 16)

            ws.row_dimensions[4].height = 28
            ws.freeze_panes = "A5"

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
# FORM 1: ECC TOP DISEASES (Co-management removed for initial entry)
# ---------------------------------------------------------
if selected_sheet == "ECC TOP DISEASES":
    st.header("Emergency Care Center (ECC) Data Entry Form")
    with st.form("ecc_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            last_name = st.text_input("Last Name")
        with c2:
            first_name = st.text_input("First Name")
        with c3:
            middle_name = st.text_input("Middle Name")
        with c4:
            sex = st.selectbox("Sex", ["Male", "Female", "Others"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            entry_date = st.date_input("Date", datetime.today())
        with c6:
            entry_time = st.time_input("Time", datetime.now().time())
        with c7:
            age = st.number_input("Age", min_value=0, max_value=120, value=25)
        with c8:
            hosp_mode = st.selectbox("Hospitalization Mode", ["In-Patient Department", "Outpatient Department", "Private Case", "House Case (Walk-in)"])

        st.subheader("👨‍⚕️ Physician Information")
        c_doc1, c_doc2, c_doc3, c_doc4 = st.columns(4)
        with c_doc1:
            attending_physician = st.text_input("Attending Physician Name")
        with c_doc2:
            attending_spec = st.selectbox("Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS)
        with c_doc3:
            payment_selected = st.selectbox("Mode of Payment", ["PHIC", "HMO", "SELF-PAY", "CHARITY"])
        with c_doc4:
            transferred_to = st.selectbox("Transferred To", ["None", "GNU", "PICU", "ICU"])

        st.subheader("📋 Clinical Details")
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
                'MODE OF PAYMENT': payment_selected,
                'TRANSFERRED TO': transferred_to,
                'CASE COUNT': 1
            }

            if append_record_to_excel("ECC TOP DISEASES", row_data):
                st.success("Successfully saved to `ECC TOP DISEASES` sheet!")

# ---------------------------------------------------------
# FORM 2: ENDO
# ---------------------------------------------------------
elif selected_sheet == "ENDO":
    st.header("Endoscopy Unit Data Entry Form")
    
    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_endo")

    with st.form("endo_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            last_name = st.text_input("Last Name")
        with c2:
            first_name = st.text_input("First Name")
        with c3:
            middle_name = st.text_input("Middle Name")
        with c4:
            sex = st.selectbox("Sex", ["Male", "Female", "Others"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            entry_date = st.date_input("Procedure Date", datetime.today())
        with c6:
            sched_time = st.time_input("Scheduled Time", datetime.now().time())
        with c7:
            actual_time = st.time_input("Actual Time", datetime.now().time())
        with c8:
            age = st.number_input("Age", min_value=0, max_value=120, value=40)

        st.subheader("👨‍⚕️ Medical & Surgical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS)

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", key=f"cm_name_endo_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, key=f"cm_spec_endo_{i}")
                cm_entries.append((cm_name, cm_spec))

        c_surg1, c_surg2 = st.columns(2)
        with c_surg1:
            surgeon = st.text_input("Surgeon / Endoscopist / Proceduralist")
        with c_surg2:
            surgeon_spec = st.selectbox("Surgeon / Proceduralist Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("GASTROENTEROLOGY"))

        c_anes1, c_anes2 = st.columns(2)
        with c_anes1:
            anesthesiologist = st.text_input("Anesthesiologist Name (Optional)")
        with c_anes2:
            anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("GENERAL ANAESTHESIOLOGY"))

        st.subheader("📋 Diagnosis & Procedure Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis_text = st.text_input("Diagnosis")
        with cd2:
            procedure_text = st.text_input("Procedure Name")

        proc_cols = ['GASTROSCOPY', 'COLONOSCOPY', 'NASAL PROCEDURE', 'PEG PROCEDURE', 'ERCP', 'PROCTOSIGMOIDOSCOPY', 'PARACENTESIS', 'BRONCHOSCOPY', 'OTHER PROCEDURES']
        selected_procs = st.multiselect("Select Procedure Flags", proc_cols)
        
        ca, cb, cc, cd = st.columns(4)
        with ca: 
            proc_type = st.radio("Nature", ["DIAGNOSTICS", "THERAPEUTIC"])
        with cb: 
            hosp_mode = st.radio("Hospitalization Mode", ["Outpatient Department", "In-Patient Department"])
        with cc: 
            payment_selected = st.selectbox("Mode of Payment", ["PHIC", "HMO", "SELF-PAY"])
        with cd:
            kit_package = st.checkbox("Hospital Kit Package", value=False)

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
        if submitted:
            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "mixed"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'SCHEDULED TIME': sched_time.strftime("%I:%M:%S %p"),
                'ACTUAL TIME': actual_time.strftime("%I:%M:%S %p"),
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

            if append_record_to_excel("ENDO", row_data):
                st.success("Successfully saved to `ENDO` sheet!")

# ---------------------------------------------------------
# FORM 3: HDU
# ---------------------------------------------------------
elif selected_sheet == "HDU":
    st.header("Hemodialysis Unit Data Entry Form")

    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_hdu")

    with st.form("hdu_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            last_name = st.text_input("Last Name")
        with c2:
            first_name = st.text_input("First Name")
        with c3:
            middle_name = st.text_input("Middle Name")
        with c4:
            sex = st.selectbox("Sex", ["Male", "Female", "Others"])

        c5, c6 = st.columns(2)
        with c5:
            entry_date = st.date_input("Dialysis Date", datetime.today())
        with c6:
            diagnosis = st.text_input("Diagnosis", value="CKD")

        st.subheader("👨‍⚕️ Medical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Nephrologist / Physician Name", value="DR. ALEJANDRO SESE JR.")
        with c_att2:
            attending_spec = st.selectbox("Attending Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("NEPHROLOGY"))

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", key=f"cm_name_hdu_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, key=f"cm_spec_hdu_{i}")
                cm_entries.append((cm_name, cm_spec))

        c7, c8, c9 = st.columns(3)
        with c7:
            shift_set = st.selectbox("Dialysis Shift Slot", ["1ST SET", "2ND SET", "3RD SET", "ONCALL"])
        with c8:
            hosp_mode = st.radio("Hospitalization Mode", ["Outpatient Department", "In-Patient Department"])
        with c9:
            payment_selected = st.selectbox("Mode of Payment", ["PHIC", "HMO", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
        if submitted:
            epoch = datetime(1899, 12, 30)
            true_date = str((datetime.combine(entry_date, datetime.min.time()) - epoch).days)
            
            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%B %d, %Y"),
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

            if append_record_to_excel("HDU", row_data):
                st.success("Successfully saved to `HDU` sheet!")

# ---------------------------------------------------------
# FORM 4: OBGYNE CASES
# ---------------------------------------------------------
elif selected_sheet == "OBGYNE CASES":
    st.header("OBGYNE Cases Data Entry Form")

    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_obgyne")

    with st.form("obgyne_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            last_name = st.text_input("Last Name")
        with c2:
            first_name = st.text_input("First Name")
        with c3:
            middle_name = st.text_input("Middle Name")
        with c4:
            sex = st.selectbox("Sex", ["Female", "Male", "Others"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            entry_date = st.date_input("Procedure Date", datetime.today())
        with c6:
            sched_time = st.time_input("Scheduled Time", datetime.now().time())
        with c7:
            actual_time = st.time_input("Actual Time", datetime.now().time())
        with c8:
            age = st.number_input("Age", min_value=10, max_value=100, value=30)

        st.subheader("👨‍⚕️ Medical & Surgical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("OBSTETRICS & GYNAECOLOGY"))

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", key=f"cm_name_ob_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, key=f"cm_spec_ob_{i}")
                cm_entries.append((cm_name, cm_spec))

        c_surg1, c_surg2 = st.columns(2)
        with c_surg1:
            surgeon = st.text_input("Surgeon / OBGYNE Primary Operator")
        with c_surg2:
            surgeon_spec = st.selectbox("Surgeon Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("OBSTETRICS & GYNAECOLOGY"))

        c_anes1, c_anes2 = st.columns(2)
        with c_anes1:
            anesthesiologist = st.text_input("Anesthesiologist Name (Optional)")
        with c_anes2:
            anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("GENERAL ANAESTHESIOLOGY"))

        st.subheader("📋 OBGYNE Diagnosis & Procedure Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis = st.text_area("OBGYNE Diagnosis")
        with cd2:
            procedure = st.text_input("Procedure Name")

        ca, cb, cc, cd = st.columns(4)
        with ca:
            ob_procs = st.multiselect("Procedure Breakdown", ["CS PRIMARY", "CS", "NSD", "D&C", "HYSTERECTOMY", "EXLAP", "OTHER PROCEDURES", "NST"])
        with cb:
            complexity = st.selectbox("Complexity Tier", ["MAJOR", "MINOR", "DIAGNOSTIC"])
        with cc:
            hosp_mode = st.radio("Hospitalization Mode", ["In-Patient Department", "Outpatient Department"])
            kit_used = st.checkbox("Hospital Kit Package", value=True)
        with cd:
            payment_selected = st.selectbox("Mode of Payment", ["PHIC", "HMO", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
        if submitted:
            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'SCHEDULED TIME': sched_time.strftime("%I:%M:%S %p"),
                'ACTUAL TIME': actual_time.strftime("%I:%M:%S %p"),
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

            if append_record_to_excel("OBGYNE CASES", row_data):
                st.success("Successfully saved to `OBGYNE CASES` sheet!")

# ---------------------------------------------------------
# FORM 5: SCC CASES
# ---------------------------------------------------------
elif selected_sheet == "SCC CASES":
    st.header("Surgical Care Center (SCC) Data Entry Form")

    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_scc")

    with st.form("scc_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            last_name = st.text_input("Last Name")
        with c2:
            first_name = st.text_input("First Name")
        with c3:
            middle_name = st.text_input("Middle Name")
        with c4:
            sex = st.selectbox("Sex", ["Male", "Female", "Others"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            entry_date = st.date_input("Surgery Date", datetime.today())
        with c6:
            sched_time = st.time_input("Scheduled Time", datetime.now().time())
        with c7:
            actual_time = st.time_input("Actual Time", datetime.now().time())
        with c8:
            age = st.number_input("Age", min_value=0, max_value=120, value=35)

        st.subheader("👨‍⚕️ Medical & Surgical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS)

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", key=f"cm_name_scc_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, key=f"cm_spec_scc_{i}")
                cm_entries.append((cm_name, cm_spec))

        c_surg1, c_surg2 = st.columns(2)
        with c_surg1:
            surgeon = st.text_input("Primary Surgeon")
        with c_surg2:
            surgeon_spec = st.selectbox("Surgeon Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("GENERAL SURGERY"))

        c_anes1, c_anes2 = st.columns(2)
        with c_anes1:
            anesthesiologist = st.text_input("Anesthesiologist Name (Optional)")
        with c_anes2:
            anes_spec = st.selectbox("Anesthesiologist Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("GENERAL ANAESTHESIOLOGY"))

        st.subheader("📋 Pre/Post-Op & Surgical Details")
        cd1, cd2 = st.columns(2)
        with cd1:
            diagnosis = st.text_area("Pre/Post-Op Diagnosis")
        with cd2:
            procedure = st.text_area("Surgical Procedure")

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
            complexity = st.selectbox("Complexity Tier", ["MAJOR", "MEDIUM", "MINOR", "DIAGNOSTICS"])
        with cb: 
            hosp_mode = st.radio("Hospitalization Mode", ["Outpatient Department", "In-Patient Department"])
        with cc: 
            kit_package = st.checkbox("Hospital Kit Package", value=True)
        with cd: 
            payment_selected = st.selectbox("Mode of Payment", ["PHIC", "HMO", "SELF-PAY"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
        if submitted:
            valid_cm = [(name.strip(), spec) for name, spec in cm_entries if name.strip()]
            cm_names_str = "; ".join([item[0] for item in valid_cm]) if valid_cm else "N/A"
            cm_specs_str = "; ".join([item[1] for item in valid_cm]) if valid_cm else "N/A"

            row_data = {
                'MONTH': get_month_str(entry_date, "numeric_prefix"),
                'DATE': entry_date.strftime("%m/%d/%Y"),
                'SCHEDULED TIME': sched_time.strftime("%I:%M:%S %p"),
                'ACTUAL TIME': actual_time.strftime("%I:%M:%S %p"),
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

            if append_record_to_excel("SCC CASES", row_data):
                st.success("Successfully saved to `SCC CASES` sheet!")

# ---------------------------------------------------------
# FORM 6: SCU CASES
# ---------------------------------------------------------
elif selected_sheet == "SCU CASES":
    st.header("Special Care Unit (SCU) Data Entry Form")

    st.subheader("👨‍⚕️ Co-Management Physician Settings")
    num_comanage = st.number_input("Number of Co-Managing Physicians to Add", min_value=0, max_value=10, value=0, step=1, key="num_cm_scu")

    with st.form("scu_form", clear_on_submit=True):
        st.subheader("👤 Patient Demographics")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            last_name = st.text_input("Last Name")
        with c2:
            first_name = st.text_input("First Name")
        with c3:
            middle_name = st.text_input("Middle Name")
        with c4:
            sex = st.selectbox("Sex", ["Male", "Female", "Others"])

        c5, c6, c7, c8 = st.columns(4)
        with c5:
            entry_date = st.date_input("Admission Date", datetime.today())
            aog = st.text_input("Age of Gestation (AOG)", value="38 WEEKS")
        with c6:
            age_y = st.number_input("Age (Years)", min_value=0, max_value=18, value=0)
        with c7:
            age_m = st.number_input("Age (Months)", min_value=0, max_value=11, value=0)
        with c8:
            age_d = st.number_input("Age (Days)", min_value=0, max_value=31, value=0)

        st.subheader("👨‍⚕️ Medical Care Team")
        c_att1, c_att2 = st.columns(2)
        with c_att1:
            attending_physician = st.text_input("Attending Physician Name")
        with c_att2:
            attending_spec = st.selectbox("Attending Physician Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, index=get_spec_index("GENERAL PAEDIATRICS"))

        cm_entries = []
        if num_comanage > 0:
            st.markdown("##### 🤝 Co-Management Physician(s)")
            for i in range(int(num_comanage)):
                cm1, cm2 = st.columns(2)
                with cm1:
                    cm_name = st.text_input(f"Co-Management Physician #{i+1} Name", key=f"cm_name_scu_{i}")
                with cm2:
                    cm_spec = st.selectbox(f"Co-Management Physician #{i+1} Specialization", SPECIALTY_DROutpatient DepartmentOWN_OPTIONS, key=f"cm_spec_scu_{i}")
                cm_entries.append((cm_name, cm_spec))

        c10, c11, c12, c13 = st.columns(4)
        with c10:
            admitted_from = st.selectbox("Admitted From", ["ECC", "GNU 1C", "2A", "2B", "2C", "2D", "3A", "3B", "3C", "4A"])
        with c11:
            admitted_to = st.selectbox("Admitted To", ["NICU", "NSU", "PCN", "OUTBORN", "ROOM-IN"])
        with c12:
            hosp_mode = st.radio("Hospitalization Mode", ["In-Patient Department", "Outpatient Department"])
        with c13:
            payment_selected = st.selectbox("Mode of Payment", ["PHIC", "HMO", "SELF-PAY"])

        st.subheader("📋 Diagnosis & Diagnostic Flags")
        diagnosis = st.text_area("Diagnosis Text")
        diag_flags = st.multiselect("Diagnostic Flags", ["PNEUMONIA", "SEPSIS", "PCAP", "SURGERY"])

        submitted = st.form_submit_button("Submit Record to Excel Sheet")
        if submitted:
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
                'DATE': entry_date.strftime("%m/%d/%Y"),
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
                'ATTENDING PHYSICIAN': attending_physician if attending_physician else "N/A",
                'ATTENDING SPECIALIZATION': attending_spec,
                'CO-MANAGEMENT PHYSICIAN': cm_names_str,
                'CO-MANAGEMENT SPECIALIZATION': cm_specs_str,
                'HOSPITALIZATION MODE': hosp_mode,
                'MODE OF PAYMENT': payment_selected,
                'CASE COUNT': 1
            }

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