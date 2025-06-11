# CSV to DynamoDB ETL Pipeline with AWS Glue

An event-driven, serverless ETL solution that automatically processes CSV files uploaded to S3 and loads them into DynamoDB using AWS Glue.

## 🏗️ Architecture

```
CSV Upload → S3 → EventBridge → Glue Workflow → Glue Job → DynamoDB
```

### Components
- **S3 Bucket**: Storage for CSV files and ETL scripts
- **AWS Glue**: ETL job processing with data validation and transformation
- **DynamoDB**: Target database for processed data
- **EventBridge**: Event-driven automation trigger
- **Lambda**: Custom resource for script deployment
- **IAM Roles**: Secure service permissions

## ✨ Features

- 🚀 **Event-Driven**: Automatically processes CSV files on upload
- 🔄 **Latest Technology**: Uses AWS Glue 5.0 for optimal performance
- ✅ **Data Validation**: Filters out invalid records and ensures data quality
- 🛡️ **Type Safety**: Converts data types for DynamoDB compatibility
- 📊 **Job Bookmarking**: Prevents duplicate processing
- 🏷️ **Clean Naming**: Uses 8-character resource suffixes for manageable names
- 📈 **Monitoring**: Built-in CloudWatch logging and metrics

## 📋 Prerequisites

- AWS CLI configured with appropriate permissions
- CloudFormation deployment permissions
- IAM permissions to create roles and policies
- Python 3.x (for the CSV generation utility)

## 🚀 Quick Start

### 1. Deploy the Stack

```bash
aws cloudformation create-stack \
  --stack-name csv-glue-pipeline \
  --template-body file://csv-to-ddb-glue.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides NotificationEmail=<YOUR EMAIL ADDRESS HERE>
```

### 2. Get the S3 Upload Location

```bash
aws cloudformation describe-stacks \
  --stack-name csv-glue-pipeline \
  --query "Stacks[0].Outputs[?OutputKey=='S3UploadLocation'].OutputValue" \
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
aws s3 cp data.csv s3://YOUR_BUCKET_NAME/raw-csv-files/
```

### 5. Monitor Processing

```bash
# Check job status
aws glue get-job-runs --job-name YOUR_JOB_NAME --max-items 1

# Verify data in DynamoDB
aws dynamodb scan --table-name YOUR_TABLE_NAME --max-items 5
```

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

### Data Validation
The ETL process automatically:
- Filters out rows with missing `account` or `offer_id` values
- Converts key fields to strings for DynamoDB compatibility
- Preserves all other columns as additional attributes

## 🏗️ Infrastructure Details

### Created Resources
The CloudFormation template creates:

| Resource | Purpose | Naming Pattern |
|----------|---------|----------------|
| S3 Bucket | CSV file storage | `csv-to-ddb-glue-{8-char-id}` |
| DynamoDB Table | Data storage | `ingested-csv-data-{8-char-id}` |
| Glue Job | ETL processing | `csv-to-ddb-processor-{8-char-id}` |
| Glue Workflow | Job orchestration | `csv-toddb-glue-{8-char-id}` |
| EventBridge Rule | Event automation | `csv-to-ddb-trigger-{8-char-id}` |
| IAM Roles | Service permissions | Various with `{8-char-id}` suffix |

### DynamoDB Table Schema
```
Primary Key: account (String)
Sort Key: offer_id (String)
Billing Mode: Pay-per-request
```

## 🔧 Configuration Options

### Glue Job Settings
- **Version**: 5.0 (latest)
- **Worker Type**: G.1X
- **Number of Workers**: 2
- **Job Bookmarking**: Enabled
- **Timeout**: 480 minutes

### Customization
To modify the solution:

1. **Change table schema**: Update the DynamoDB table definition
2. **Modify ETL logic**: Edit the embedded Python script in the Lambda function
3. **Adjust resources**: Modify Glue job worker configuration
4. **Add validation**: Enhance the data filtering logic

## 📊 Monitoring and Troubleshooting

### CloudWatch Logs
Glue job logs are available in CloudWatch:
```
Log Group: /aws-glue/jobs
Log Stream: [job-name]/[run-id]
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Job not triggering | Check EventBridge rule and S3 event configuration |
| DynamoDB errors | Verify CSV has required `account` and `offer_id` columns |
| Permission errors | Ensure IAM roles have proper policies |
| Job failures | Check CloudWatch logs for detailed error messages |

### Monitoring Commands

```bash
# Check recent job runs
aws glue get-job-runs --job-name YOUR_JOB_NAME --max-items 5

# View CloudWatch logs
aws logs describe-log-streams --log-group-name "/aws-glue/jobs"

# Check DynamoDB item count
aws dynamodb describe-table --table-name YOUR_TABLE_NAME --query "Table.ItemCount"
```

## 🔄 Development Workflow

### Testing Changes
1. Modify the CloudFormation template
2. Update the stack:
   ```bash
   aws cloudformation update-stack \
     --stack-name csv-glue-pipeline \
     --template-body file://csv-to-ddb-glue.yaml \
     --capabilities CAPABILITY_NAMED_IAM
   ```
3. Generate test data: `python make-csv.py --rows 100`
4. Upload and test with the sample CSV file
5. Monitor the job execution

### ETL Script Development
The ETL script is embedded in the CloudFormation template. To modify:
1. Update the script content in the Lambda function
2. Deploy the stack update
3. The Lambda function automatically uploads the new script to S3

## 🧹 Cleanup

To remove all resources:

```bash
# Empty the S3 bucket first
aws s3 rm s3://YOUR_BUCKET_NAME --recursive

# Delete the stack
aws cloudformation delete-stack --stack-name csv-glue-pipeline
```

## 💰 Cost Considerations

- **DynamoDB**: Pay-per-request pricing based on read/write operations
- **Glue**: Charged per DPU-hour (Data Processing Unit)
- **S3**: Standard storage and request pricing
- **EventBridge**: Minimal cost for rule evaluations
- **Lambda**: Free tier covers the script upload function

## 📁 Repository Structure

```
.
├── README.md                 # This documentation
├── csv-to-ddb-glue.yaml     # CloudFormation template
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
3. Open an issue in this repository with:
   - Error messages
   - CloudFormation events
   - Sample data (anonymized)

---

**Built with ❤️ using AWS CloudFormation, Glue 5.0, and serverless best practices**
