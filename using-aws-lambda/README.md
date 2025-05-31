# CSV to DynamoDB ETL Pipeline with AWS Lambda

An event-driven, serverless ETL solution that automatically processes CSV files uploaded to S3 and loads them into DynamoDB using AWS Lambda with robust error handling and data backup.

## 🏗️ Architecture

```
CSV Upload → S3 → Lambda Function → DynamoDB
                ↓
           JSON Backup + Error Handling
```

![Architecture diagram](https://d2908q01vomqb2.cloudfront.net/887309d048beef83ad3eabf2a79a64a389ab1c9f/2025/05/05/DBBLOG-diagram-update-1-1024x474.png)

### Components
- **S3 Bucket**: Storage for CSV files, JSON backups, and error logs
- **AWS Lambda**: Python 3.13 function for CSV processing and data transformation
- **DynamoDB**: Target database for processed data
- **S3 Event Notifications**: Event-driven automation trigger
- **IAM Roles**: Secure service permissions
- **Custom Resource**: Helper Lambda for S3 notification setup

## ✨ Features

- 🚀 **Event-Driven**: Automatically processes CSV files on upload
- 🔄 **Latest Runtime**: Uses Python 3.13 with arm64 architecture for optimal performance
- ✅ **Data Validation**: Cleans data and removes empty values
- 🔁 **Retry Logic**: Implements exponential backoff for DynamoDB operations
- 💾 **Data Backup**: Creates JSON copies of all processed data
- 🛡️ **Error Handling**: Saves unprocessed items for troubleshooting
- 📊 **Batch Processing**: Efficient 25-item batches for DynamoDB writes
- 📈 **Monitoring**: Built-in CloudWatch logging and metrics

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- CloudFormation deployment permissions
- IAM permissions to create roles and policies
- Python 3.x (for the CSV generation utility)

## 🚀 Quick Start

### 1. Deploy the Stack

```bash
aws cloudformation deploy \
  --template-file s3-dynamo-ingest.yaml \
  --stack-name csv-lambda-pipeline \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    DynamoDBTableName=my-data-table \
    LambdaFunctionName=csv-processor-lambda \
    S3BucketName=my-unique-csv-bucket-12345 \
    IAMRoleName=csv-processor-lambda-role
```

### 2. Get the S3 Upload Location

```bash
aws cloudformation describe-stacks \
  --stack-name csv-lambda-pipeline \
  --query "Stacks[0].Outputs[?OutputKey=='S3BucketName'].OutputValue" \
  --output text
```

### 3. Generate Test Data (Optional)

Use the included utility to generate sample CSV files:

```bash
# Generate a CSV file with 1000 records (default)
python make-csv.py

# Generate 1 million rows for performance testing
python make-csv.py --rows 1000000

# Custom output file with specific row count
python make-csv.py --rows 5000 --output test_data.csv
```

### 4. Upload a CSV File

```bash
# Upload the generated file to trigger processing
aws s3 cp data.csv s3://YOUR_BUCKET_NAME/
```

### 5. Monitor Processing

```bash
# Check Lambda function logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/YOUR_FUNCTION_NAME"

# Verify data in DynamoDB
aws dynamodb scan --table-name YOUR_TABLE_NAME --max-items 5

# Check for processed JSON backup
aws s3 ls s3://YOUR_BUCKET_NAME/json-copy/
```

## ⚙️ Configuration Parameters

The following parameters can be configured during stack deployment:

| Parameter | Type | Description | Default Value |
|-----------|------|-------------|---------------|
| `DynamoDBTableName` | String | The name of the DynamoDB table | `your-dynamodb-table-name` |
| `LambdaFunctionName` | String | The name of the Lambda function | `your-lambda-function` |
| `S3BucketName` | String | The name of the S3 bucket | `your-lambda-function` |
| `IAMRoleName` | String | The name of the IAM role for the Lambda | `iam-role-name` |

**Important Notes:**
- S3 bucket names must be globally unique
- Provide unique and descriptive names for all parameters
- The template creates IAM resources with custom names

## 🛠️ CSV Generation Utility

The `make-csv.py` script generates test data that matches the expected schema for testing the ETL pipeline. It supports flexible parameters for different testing scenarios.

### Usage

```bash
# Basic usage - 1000 rows with 20 unique accounts
python make-csv.py

# Generate 1 million rows for performance testing
python make-csv.py --rows 1000000

# Custom output file with specific row count
python make-csv.py --rows 5000 --output large.csv

# More unique accounts for realistic distribution
python make-csv.py --accounts 100 --rows 50000

# Complex example: 100K rows, 500 accounts, custom file
python make-csv.py --rows 100000 --accounts 500 --output test_data.csv
```

### Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--rows` | Number of records to generate | 1000 |
| `--output` | Output CSV file name | `data.csv` |
| `--accounts` | Number of unique account IDs | 20 |
| `--help` | Show help and examples | - |

### Features
- **Enhanced validation**: Validates input parameters with helpful error messages
- **Memory efficient**: Uses chunked processing for large files (10K row chunks)
- **Progress tracking**: Shows progress indicators for files ≥ 50K rows
- **Unique accounts**: Generates specified number of unique account IDs
- **Realistic data**: Random but properly formatted test data with proper date ranges
- **File size reporting**: Shows file size in MB for large outputs (> 1MB)
- **Smart warnings**: Alerts when account count exceeds row count
- **User-friendly output**: Uses emoji indicators for better user experience

### Generated Data Structure

The script creates CSV files with the following columns:

| Column | Format | Example |
|--------|--------|---------|
| `account` | 8-digit number | `12345678` |
| `offer_id` | 12-digit number | `987654321012` |
| `catalog_id` | 18-digit number | `111222333444555666` |
| `account_type_code` | 2 random uppercase letters | `ND`, `ZS` |
| `offer_type_id` | 8-digit number | `84487157` |
| `created` | ISO datetime (UTC) | `2024-07-30T20:16:16.777001+00:00` |
| `expire` | ISO datetime (UTC) | `2025-07-23T20:16:16.777001+00:00` |
| `risk` | Risk level | `low`, `medium`, `high` |

### Data Generation Logic
- **Account pool**: Creates unique 8-digit account IDs from the specified count
- **Date ranges**: `created` dates are within the last 365 days, `expire` dates are 7-365 days after creation
- **Realistic distribution**: Account type codes and offer type IDs are randomly selected from generated pools
- **Memory optimization**: Data is generated and written in 10,000-row chunks

### Sample Output

```csv
account,offer_id,catalog_id,account_type_code,offer_type_id,created,expire,risk
12345678,987654321012,111222333444555666,ND,84487157,2024-07-30T20:16:16.777001+00:00,2025-07-23T20:16:16.777001+00:00,low
87654321,123456789012,222333444555666777,ZS,16885136,2025-01-02T20:16:16.777589+00:00,2025-12-04T20:16:16.777589+00:00,medium
```

### Console Output Examples

```bash
# Small file generation
$ python make-csv.py --rows 1000
Generating 1,000 rows with 20 unique accounts...
✅ CSV file 'data.csv' generated successfully with 1,000 rows!

# Large file generation with progress
$ python make-csv.py --rows 100000
Generating 100,000 rows with 20 unique accounts...
Progress: 50.0% (50,000/100,000 rows)
Progress: 100.0% (100,000/100,000 rows)
✅ CSV file 'data.csv' generated successfully with 100,000 rows!
📁 File size: 12.4 MB

# Validation warning
$ python make-csv.py --rows 100 --accounts 200
⚠️  Warning: More accounts than rows - some accounts will have no data
Generating 100 rows with 200 unique accounts...
✅ CSV file 'data.csv' generated successfully with 100 rows!
```

## 📁 CSV File Requirements

### Required Columns
Your CSV files must include these columns as the first two fields:

- `account` - Primary key (will be converted to string)
- `offer_id` - Sort key (will be converted to string)

### Data Processing Workflow

1. **Upload CSV**: Upload a CSV file to the S3 bucket
   - **Expected Format**: CSV with header row (Lambda uses `csv.DictReader`)
   - **Encoding**: Supports UTF-8 with BOM characters

2. **Lambda Trigger**: S3 `ObjectCreated` event triggers the Lambda function

3. **Data Processing**:
   - Retrieves CSV file from S3
   - Reads and parses CSV content
   - Removes empty string values from each row
   - Batches rows (25 items per batch) for DynamoDB writes
   - Implements retry logic with exponential backoff (up to 3 retries)

4. **Data Storage**:
   - **DynamoDB**: Successfully processed items stored with `account` as HASH key and `offer_id` as RANGE key
   - **JSON Backup**: All processed items saved to `s3://bucket/json-copy/filename.json`
   - **Error Handling**: Unprocessed items saved to `s3://bucket/unprocessed/filename.unprocessed.json`

## 🏗️ Infrastructure Details

### Created Resources
The CloudFormation template creates:

| Resource | Purpose | Type |
|----------|---------|------|
| `ImportBucket` | CSV file storage and outputs | S3 Bucket |
| `DynamoDBTable` | Data storage | DynamoDB Table |
| `ImportLambdaFunction` | CSV processing | Lambda Function (Python 3.13, arm64) |
| `SetupBucketNotificationFunction` | S3 event configuration | Lambda Function |
| `LambdaExecutionRole` | Main Lambda permissions | IAM Role |
| `SetupNotificationRole` | Setup Lambda permissions | IAM Role |
| `DynamoDBWriteS3ReadPolicy` | Lambda access policy | IAM Policy |
| `LambdaPermission` | S3 invoke permissions | Lambda Permission |
| `BucketNotificationConfiguration` | S3 event trigger setup | Custom Resource |

### DynamoDB Table Schema
```
Primary Key: account (String)
Sort Key: offer_id (String)
Billing Mode: Pay-per-request
```

### Lambda Function Details
- **Runtime**: Python 3.13
- **Architecture**: arm64
- **Timeout**: 15 minutes
- **Memory**: 128 MB
- **Batch Size**: 25 items per DynamoDB write
- **Retry Logic**: Up to 3 attempts with exponential backoff

## 📤 Stack Outputs

The stack provides the following outputs:

| Output | Description |
|--------|-------------|
| `DynamoDBTableName` | Name of the created DynamoDB table |
| `LambdaFunctionArn` | ARN of the data processing Lambda function |
| `S3BucketName` | Name of the created S3 bucket |
| `IAMRoleName` | Name of the IAM role for the Lambda function |

## 📊 Monitoring and Troubleshooting

### CloudWatch Logs
Lambda function logs are available in CloudWatch:
```
Log Group: /aws/lambda/[function-name]
Log Stream: [timestamp]/[request-id]
```

### S3 Output Structure
```
s3://your-bucket/
├── uploaded-file.csv          # Original CSV files
├── json-copy/
│   └── uploaded-file.json     # JSON backup of processed data
└── unprocessed/
    └── uploaded-file.unprocessed.json  # Failed items for review
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Lambda not triggering | Check S3 event configuration and Lambda permissions |
| DynamoDB errors | Verify CSV has required `account` and `offer_id` columns |
| Timeout errors | Consider breaking large files into smaller chunks |
| Memory errors | Monitor Lambda memory usage and increase if needed |
| Permission errors | Ensure IAM roles have proper policies |

### Monitoring Commands

```bash
# Check recent Lambda invocations
aws logs describe-log-streams --log-group-name "/aws/lambda/YOUR_FUNCTION_NAME"

# View latest execution logs
aws logs filter-log-events \
  --log-group-name "/aws/lambda/YOUR_FUNCTION_NAME" \
  --start-time $(date -d '1 hour ago' +%s)000

# Check DynamoDB item count
aws dynamodb describe-table --table-name YOUR_TABLE_NAME --query "Table.ItemCount"

# List processed files
aws s3 ls s3://YOUR_BUCKET_NAME/json-copy/

# Check for failed items
aws s3 ls s3://YOUR_BUCKET_NAME/unprocessed/
```

## 🔄 Development Workflow

### Testing Changes
1. Modify the CloudFormation template
2. Update the stack:
   ```bash
   aws cloudformation update-stack \
     --stack-name csv-lambda-pipeline \
     --template-body file://s3-dynamo-ingest.yaml \
     --capabilities CAPABILITY_NAMED_IAM
   ```
3. Generate test data: `python make-csv.py --rows 100`
4. Upload and test with the sample CSV file
5. Monitor Lambda execution logs

### Lambda Function Development
The Lambda function code is embedded in the CloudFormation template. To modify:
1. Update the function code in the template
2. Deploy the stack update
3. Test with sample CSV files

## 🧹 Cleanup

To remove all resources:

```bash
# Empty the S3 bucket first (required before deletion)
aws s3 rm s3://YOUR_BUCKET_NAME --recursive

# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name csv-lambda-pipeline
```

## 💰 Cost Considerations

- **Lambda**: Pay per request and execution time
- **DynamoDB**: Pay-per-request pricing based on read/write operations
- **S3**: Standard storage and request pricing
- **CloudWatch**: Log storage and monitoring costs

## 📁 Repository Structure

```
.
├── README.md                 # This documentation
├── s3-dynamo-ingest.yaml     # CloudFormation template
└── make-csv.py              # CSV generation utility
```

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Submit a pull request with detailed description

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review CloudWatch logs for detailed error information
3. Check S3 for unprocessed items
4. Open an issue in this repository with:
   - Error messages
   - CloudFormation events
   - Sample data (anonymized)

---

**Built with ❤️ using AWS Lambda, CloudFormation, and serverless best practices**

## 📚 Additional Resources

- [AWS Blog: Ingest CSV data to Amazon DynamoDB using AWS Lambda](https://aws.amazon.com/blogs/database/ingest-csv-data-to-amazon-dynamodb-using-aws-lambda/)
- [AWS Lambda Python Runtime Documentation](https://docs.aws.amazon.com/lambda/latest/dg/python-handler.html)
- [DynamoDB BatchWriteItem Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/bp-use-batch-operations.html)
