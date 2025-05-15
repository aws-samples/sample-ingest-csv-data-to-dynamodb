import csv
import random
import string
import datetime

# List of account_type_codes
account_type_codes = [''.join(random.choices(string.ascii_uppercase, k=2)) for _ in range(26)]

# List of offer_type_ids
offer_type_ids = [''.join(random.choices(string.digits, k=8)) for _ in range(100)]

# List of risk levels
risk_levels = ['high', 'medium', 'low']

# Generate data rows
data_rows = []
for _ in range(1500):
    account = ''.join(random.choices(string.digits, k=8))
    offer_id = ''.join(random.choices(string.digits, k=12))
    catalog_id = ''.join(random.choices(string.digits, k=18))
    account_type_code = random.choice(account_type_codes)
    offer_type_id = random.choice(offer_type_ids)
    created = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=random.randint(0, 365))
    expire = created + datetime.timedelta(days=random.randint(7, 365))
    risk = random.choice(risk_levels)
    data_row = [
        account, 
        offer_id, 
        catalog_id, 
        account_type_code, 
        offer_type_id, 
        created.isoformat(), 
        expire.isoformat(), 
        risk
    ]
    data_rows.append(data_row)

# Write data to CSV file
with open('data.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        'account', 
        'offer_id', 
        'catalog_id', 
        'account_type_code', 
        'offer_type_id', 
        'created', 
        'expire', 
        'risk'
    ])
    writer.writerows(data_rows)

print("CSV file generated successfully.")