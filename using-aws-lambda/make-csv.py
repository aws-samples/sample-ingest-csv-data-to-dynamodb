#!/usr/bin/env python3
"""
CSV Data Generator for AWS Glue ETL Pipeline

Generates sample CSV data that matches the expected schema for testing
the CSV to DynamoDB ETL pipeline.

Usage:
    python make-csv.py                              # Generate 1000 rows to data.csv
    python make-csv.py --rows 1000000               # Generate 1M rows
    python make-csv.py --rows 5000 --output large.csv  # Custom file
    python make-csv.py --accounts 100 --rows 10000     # More unique accounts
"""

import csv
import random
import string
import datetime
import argparse
import sys
from typing import List


def generate_account_pool(size: int) -> List[str]:
    """Generate a pool of unique account IDs."""
    accounts = set()
    while len(accounts) < size:
        account = ''.join(random.choices(string.digits, k=8))
        accounts.add(account)
    return list(accounts)


def generate_csv_data(rows: int, accounts: int, output_file: str) -> None:
    """Generate CSV data with specified parameters."""
    print(f"Generating {rows:,} rows with {accounts} unique accounts...")
    
    # Generate pools of data
    account_pool = generate_account_pool(accounts)
    account_type_codes = [''.join(random.choices(string.ascii_uppercase, k=2)) for _ in range(26)]
    offer_type_ids = [''.join(random.choices(string.digits, k=8)) for _ in range(100)]
    risk_levels = ['high', 'medium', 'low']
    
    # CSV header
    header = [
        'account', 
        'offer_id', 
        'catalog_id', 
        'account_type_code', 
        'offer_type_id', 
        'created', 
        'expire', 
        'risk'
    ]
    
    # Generate and write data in chunks for memory efficiency
    chunk_size = 10000
    rows_written = 0
    
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        
        while rows_written < rows:
            # Calculate chunk size for this iteration
            current_chunk_size = min(chunk_size, rows - rows_written)
            chunk_data = []
            
            for _ in range(current_chunk_size):
                account = random.choice(account_pool)
                offer_id = ''.join(random.choices(string.digits, k=12))
                catalog_id = ''.join(random.choices(string.digits, k=18))
                account_type_code = random.choice(account_type_codes)
                offer_type_id = random.choice(offer_type_ids)
                
                # Generate realistic date ranges
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
                chunk_data.append(data_row)
            
            # Write chunk to file
            writer.writerows(chunk_data)
            rows_written += current_chunk_size
            
            # Progress indicator for large files
            if rows >= 50000 and rows_written % 50000 == 0:
                progress = (rows_written / rows) * 100
                print(f"Progress: {progress:.1f}% ({rows_written:,}/{rows:,} rows)")
    
    print(f"✅ CSV file '{output_file}' generated successfully with {rows:,} rows!")
    
    # Show file size for large files
    import os
    file_size = os.path.getsize(output_file)
    if file_size > 1024 * 1024:  # > 1MB
        size_mb = file_size / (1024 * 1024)
        print(f"📁 File size: {size_mb:.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description='Generate CSV test data for AWS Glue ETL pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python make-csv.py                                    # 1000 rows, 20 accounts
  python make-csv.py --rows 1000000                    # 1 million rows
  python make-csv.py --rows 5000 --output large.csv    # Custom output file
  python make-csv.py --accounts 100 --rows 50000       # More unique accounts
  python make-csv.py --rows 100000 --accounts 500 --output test_data.csv
        """)
    
    parser.add_argument(
        '--rows', 
        type=int, 
        default=1000, 
        help='Number of rows to generate (default: 1000)'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default='data.csv', 
        help='Output CSV file name (default: data.csv)'
    )
    
    parser.add_argument(
        '--accounts', 
        type=int, 
        default=20, 
        help='Number of unique account IDs to generate (default: 20)'
    )
    
    args = parser.parse_args()
    
    # Validation
    if args.rows <= 0:
        print("❌ Error: Number of rows must be positive")
        sys.exit(1)
    
    if args.accounts <= 0:
        print("❌ Error: Number of accounts must be positive")
        sys.exit(1)
    
    if args.accounts > args.rows:
        print("⚠️  Warning: More accounts than rows - some accounts will have no data")
    
    try:
        generate_csv_data(args.rows, args.accounts, args.output)
    except KeyboardInterrupt:
        print("\n⏹️  Generation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error generating CSV: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
