import gspread
from google.oauth2.service_account import Credentials
import os
import sqlite3

# Initialize credentials and open Google Sheets
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope) if os.path.exists("credentials.json") else None
client = gspread.authorize(creds)
sh = client.open("MTCMC_CENSUS_MASTERFILES_SYSTEM")

# Clear Google Sheet tabs
for ws in sh.worksheets():
    if ws.title != "Hospital Information System":
        ws.clear()
        ws.update('A1', [[f"MTCMC CLINICAL CENSUS - {ws.title} MASTERFILE"]])

# Clear Local SQLite database tables
conn = sqlite3.connect("hospital_local.sqlite")
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
for table in cursor.fetchall():
    cursor.execute(f'DELETE FROM "{table[0]}";')
conn.commit()
conn.close()

print("All department data, metrics, and tallies have been completely wiped clean.")