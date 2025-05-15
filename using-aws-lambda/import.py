import logging
import boto3
import os
import csv
import json
import time
from io import StringIO

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

region = os.getenv('AWS_REGION')
table_name = os.getenv('DYNAMO_DB_TABLE_NAME')

dynamo_endpoint_url = f"https://dynamodb.{region}.amazonaws.com"
ddbClient = boto3.resource('dynamodb', endpoint_url=dynamo_endpoint_url)
s3client = boto3.client('s3')

def lambda_handler(event, context):
    logger.info("Received Event: %s", event)
    ddbTable = ddbClient.Table(table_name)

    # Get the object from the event
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    csv_filename = os.path.basename(key)

    logger.info("Bucket Name extracted from the event: %s", bucket)
    logger.info("Object Key extracted from the event: %s", key)
    
    try:
        # Get the CSV object from S3
        csv_object = s3client.get_object(Bucket=bucket, Key=key)
        
        # Read and parse CSV data
        try:
            csv_data = csv_object['Body'].read().decode('utf-8-sig')
            csv_reader = csv.DictReader(StringIO(csv_data))
            
            # Convert CSV to list of dictionaries
            rows = []
            for row in csv_reader:
                # Remove empty strings and clean up the data
                cleaned_row = {k: v for k, v in row.items() if v is not None and v != ''}
                if cleaned_row:  # Only append if the row has data
                    rows.append(cleaned_row)
                    
            logger.info(f"Successfully parsed {len(rows)} rows from CSV")
                    
        except Exception as e:
            # Simple catch-all for CSV parsing errors
            error_msg = f"Error parsing CSV: {str(e)}"
            logger.error(error_msg)
            return {
                "statusCode": 400,
                "body": json.dumps({"error": error_msg})
            }

        # Write to DynamoDB with retry logic for unprocessed items
        batch_size = 25
        unprocessed_items = []
        
        for idx in range(0, len(rows), batch_size):
            batch = rows[idx:idx + batch_size]
            request_items = {table_name: [{'PutRequest': {'Item': item}} for item in batch]}
            retries = 0
            
            # Retry logic with exponential backoff
            while retries <= 3:
                resp = ddbClient.meta.client.batch_write_item(RequestItems=request_items)
                unp = resp.get('UnprocessedItems', {}).get(table_name, [])
                
                if not unp:
                    break
                    
                request_items = {table_name: unp}
                retries += 1
                time.sleep(2 ** retries)
                logger.warning(f"Retry {retries} for {len(unp)} unprocessed items")
            
            # Handle any remaining unprocessed items
            if unp:
                items = [r['PutRequest']['Item'] for r in unp]
                save_unprocessed(bucket, csv_filename, items)
                unprocessed_items.extend(items)
        
        logger.info("Data written to DynamoDB table successfully.")

        # Create JSON object with array (excluding unprocessed items)
        processed_items = []
        unprocessed_item_set = {json.dumps(item, sort_keys=True) for item in unprocessed_items}
        
        for item in rows:
            if json.dumps(item, sort_keys=True) not in unprocessed_item_set:
                processed_items.append(item)
        
        json_object = {"data": processed_items}
        json_data = json.dumps(json_object, indent=2)
        
        # Create the JSON key with just the filename
        json_key = f"json-copy/{csv_filename.replace('.csv', '.json')}"
        s3client.put_object(Body=json_data, Bucket=bucket, Key=json_key)

        logger.info(f"JSON data uploaded to {bucket}/{json_key}")

        return {
            "statusCode": 200,
            "body": json.dumps({
                "processed_rows": len(processed_items),
                "unprocessed_rows": len(unprocessed_items),
                "unprocessed_file": f"unprocessed/{csv_filename}.unprocessed.json" if unprocessed_items else None,
                "json_copy": json_key
            })
        }

    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        logger.error(error_msg)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": error_msg})
        }

def save_unprocessed(bucket, fname, items):
    """Save items that couldn't be written to DynamoDB"""
    key = f"unprocessed/{fname}.unprocessed.json"
    try:
        existing = json.loads(s3client.get_object(Bucket=bucket, Key=key)['Body'].read())
    except s3client.exceptions.NoSuchKey:
        existing = []
    except Exception as e:
        logger.warning(f"Error reading existing unprocessed items: {str(e)}")
        existing = []
        
    existing.extend(items)
    s3client.put_object(Bucket=bucket, Key=key, Body=json.dumps(existing))
    logger.info(f"Saved {len(items)} unprocessed items to {key}")