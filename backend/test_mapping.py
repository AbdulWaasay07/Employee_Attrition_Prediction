import pandas as pd
import json
import uuid
import math
from app.db.database import SessionLocal
from app.db import models

# simulate chunk from HR upload
data = {
    'employee_id': ['emp001'],
    'ticket_category': ['Workload'],
    'ticket_severity': [' High '],
    'date_opened': ['2026-06-01'],
    'status': ['Open'],
    'satisfaction': [2]
}
chunk = pd.DataFrame(data)

# simulate what happens in process_file_in_chunks
column_mapping = {"date_opened": "issue_date", "ticket_severity": "severity", "ticket_category": "category", "satisfaction": "satisfaction_score"}
if column_mapping:
    clean_mapping = {str(k).lower().strip(): str(v).lower().strip() for k, v in column_mapping.items()}
    chunk = chunk.rename(columns=clean_mapping)

if 'issue_date' in chunk.columns:
    chunk['issue_date'] = pd.to_datetime(chunk['issue_date'], errors='coerce')

if 'ticket_id' not in chunk.columns or chunk['ticket_id'].isnull().all():
    chunk['ticket_id'] = [str(uuid.uuid4()) for _ in range(len(chunk))]

chunk.columns = chunk.columns.str.lower().str.strip()

records = chunk.to_dict(orient="records")
for record in records:
    for key, value in record.items():
        if isinstance(value, float) and math.isnan(value):
            record[key] = None

print("KEYS AFTER CLEANING:", list(records[0].keys()))
print("SUCCESSFULLY PREPARED HR TICKET MAPPING")
