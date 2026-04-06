#!/usr/bin/env python3
"""Convert leg-wise JSON to CSV format."""

import json
import csv
from pathlib import Path
from datetime import datetime

# Find the latest leg-wise JSON file
json_files = sorted(Path('.').glob('leg_wise_7147483_complete_*.json'), reverse=True)

if not json_files:
    print("❌ No leg-wise JSON files found!")
    exit(1)

json_file = json_files[0]
print(f"Converting: {json_file}")

# Load JSON
with open(json_file) as f:
    data = json.load(f)

print(f"Total records: {len(data):,}")

# Create CSV filename
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_file = f"leg_wise_7147483_complete_{timestamp}.csv"

# Write CSV
if data:
    fieldnames = list(data[0].keys())
    
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"\n✅ CSV CREATED")
    print(f"{'='*80}")
    print(f"File: {csv_file}")
    print(f"Records: {len(data):,}")
    print(f"Columns: {len(fieldnames)}")
    print(f"Fields: {', '.join(fieldnames)}")
    print(f"{'='*80}\n")
else:
    print("❌ No records in JSON file!")
