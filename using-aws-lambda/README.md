# S3 to DynamoDB CSV Ingestion via Lambda

This project deploys an AWS serverless architecture using CloudFormation to automatically ingest CSV files uploaded to an S3 bucket, process them with a Lambda function, and store the data into a DynamoDB table. It also creates a JSON copy of the processed data and logs any unprocessed items back to S3.

## Architecture Overview

![Architecture diagram](https://d2908q01vomqb2.cloudfront.net/887309d048beef83ad3eabf2a79a64a389ab1c9f/2025/05/05/DBBLOG-diagram-update-1-1024x474.png)

1.  **S3 Bucket (`ImportBucket`):** Acts as the entry point. CSV files are uploaded here.
2.  **S3 Event Notification:** When a new CSV file is created in the bucket, an S3 event notification triggers the `ImportLambdaFunction`.
3.  **Lambda Function (`ImportLambdaFunction`):**
    *   Written in Python 3.13.
    *   Parses the CSV file.
    *   Cleans the data (removes empty strings).
    *   Writes data in batches to the DynamoDB table.
    *   Implements retry logic for DynamoDB `BatchWriteItem` operations.
    *   Saves any items that couldn't be processed after retries to an `unprocessed/` prefix in the S3 bucket (as JSON).
    *   Saves a JSON copy of all successfully processed items to a `json-copy/` prefix in the S3 bucket.
4.  **DynamoDB Table (`DynamoDBTable`):** Stores the ingested data. The table uses `account` as the HASH key and `offer_id` as the RANGE key.
5.  **IAM Roles and Policies:**
    *   `LambdaExecutionRole`: Grants the `ImportLambdaFunction` necessary permissions to read from S3, write to DynamoDB, and write logs to CloudWatch.
    *   `SetupNotificationRole`: Grants a helper Lambda function permissions to configure S3 bucket notifications.
6.  **Helper Lambda & Custom Resource (`SetupBucketNotificationFunction`, `BucketNotificationConfiguration`):**
    *   A common pattern to configure S3 bucket notifications *after* the target Lambda function and its permissions are created, avoiding circular dependencies. The `SetupBucketNotificationFunction` is invoked by the `BucketNotificationConfiguration` (a CloudFormation Custom Resource) to set up the S3 event trigger.

## Features

*   Automated CSV ingestion from S3.
*   Data parsing and basic cleaning.
*   Batch writing to DynamoDB for efficiency.
*   Retry mechanism for DynamoDB writes with exponential backoff.
*   Handling of unprocessed items by saving them to S3.
*   Creation of a JSON copy of processed data in S3.
*   Configurable via CloudFormation parameters.
*   Uses Python 3.13 runtime and arm64 architecture for the main Lambda.

## Prerequisites

*   AWS Account.
*   AWS CLI configured (if deploying via CLI).
*   Sufficient IAM permissions to create the resources defined in the template (S3 buckets, Lambda functions, IAM roles, DynamoDB tables).

## CloudFormation Parameters

The following parameters can be configured during stack deployment:

| Parameter            | Type   | Description                                 | Default Value            |
| :------------------- | :----- | :------------------------------------------ | :----------------------- |
| `DynamoDBTableName`  | String | The name of the DynamoDB table              | `your-dynamodb-table-name` |
| `LambdaFunctionName` | String | The name of the Lambda function             | `your-lambda-function`   |
| `S3BucketName`       | String | The name of the S3 bucket                   | `your-lambda-function`   |
| `IAMRoleName`        | String | The name of the IAM role for the Lambda     | `iam-role-name`          |

**Note:**
*   S3 bucket names must be globally unique. You will likely need to change `S3BucketName`.
*   It's recommended to provide unique and descriptive names for all parameters.

## Deployment

You can deploy this CloudFormation template using the AWS Management Console or the AWS CLI.

### Using AWS CLI

1.  Save the CloudFormation template to a file (e.g., `s3-dynamo-ingest.yaml`).
2.  Run the following command, replacing placeholders as needed:

    ```bash
    aws cloudformation deploy \
      --template-file s3-dynamo-ingest.yaml \
      --stack-name s3-csv-to-dynamodb-stack \
      --capabilities CAPABILITY_NAMED_IAM \
      --parameter-overrides \
        DynamoDBTableName=my-data-table \
        LambdaFunctionName=csv-processor-lambda \
        S3BucketName=my-unique-csv-bucket-12345 \
        IAMRoleName=csv-processor-lambda-role
    ```

    *   `--capabilities CAPABILITY_NAMED_IAM` is required because the template creates IAM resources with custom names.

### Using AWS Management Console

1.  Navigate to the AWS CloudFormation console.
2.  Click "Create stack" (with new resources).
3.  Choose "Upload a template file" and select your `s3-dynamo-ingest.yaml` file.
4.  Click "Next".
5.  Enter a "Stack name".
6.  Fill in the parameters. Ensure `S3BucketName` is globally unique.
7.  Click "Next" through the options pages.
8.  On the "Review" page, acknowledge that the template will create IAM resources by checking the box.
9.  Click "Create stack".

## How it Works (Workflow)

1.  **Upload CSV:** Upload a CSV file to the root or any path within the S3 bucket specified by `S3BucketName`.
    *   **Expected CSV Format:** The CSV file should have a header row, as the Lambda uses `csv.DictReader` to parse it. Each row will become an item in DynamoDB.
    *   Example:
        ```csv
        account,offer_id,product_name,price
        acc123,offer001,Widget A,19.99
        acc456,offer002,Gadget B,29.50
        acc123,offer003,Accessory C,9.75
        ```

2.  **Lambda Trigger:** The S3 `ObjectCreated` event triggers the `ImportLambdaFunction`.

3.  **Lambda Processing:**
    *   The Lambda function retrieves the CSV file from S3.
    *   It reads the CSV content, decoding it as `utf-8-sig` (to handle potential BOM characters).
    *   It iterates through each row, converting it into a dictionary.
    *   Empty string values are removed from each row's dictionary.
    *   Rows are batched (default batch size: 25) and written to the DynamoDB table.
    *   If `BatchWriteItem` returns unprocessed items, the Lambda retries up to 3 times with exponential backoff.
    *   **Unprocessed Items:** If items remain unprocessed after retries, they are collected and saved as a JSON array to `s3://<S3BucketName>/unprocessed/<original_csv_filename>.unprocessed.json`.
    *   **JSON Copy:** A JSON representation of all *successfully processed* items is created and saved to `s3://<S3BucketName>/json-copy/<original_csv_filename_without_extension>.json`.

4.  **DynamoDB Storage:**
    *   Successfully processed rows are stored as items in the DynamoDB table.
    *   The `account` field from the CSV becomes the HASH key.
    *   The `offer_id` field from the CSV becomes the RANGE key.
    *   Other columns in the CSV become attributes of the DynamoDB item.

## Resources Created

This CloudFormation stack will create the following key resources:

*   **AWS::IAM::Role (`LambdaExecutionRole`):** For the main data processing Lambda.
*   **AWS::IAM::Policy (`DynamoDBWriteS3ReadPolicy`):** Attached to `LambdaExecutionRole`, allowing S3 read, limited S3 write (for json-copy and unprocessed), and DynamoDB write access.
*   **AWS::DynamoDB::Table (`DynamoDBTable`):** The target table for CSV data.
*   **AWS::S3::Bucket (`ImportBucket`):** The source bucket for CSV uploads.
*   **AWS::Lambda::Function (`ImportLambdaFunction`):** The core Python function for processing CSVs.
*   **AWS::Lambda::Permission (`LambdaPermission`):** Allows S3 to invoke the `ImportLambdaFunction`.
*   **AWS::Lambda::Function (`SetupBucketNotificationFunction`):** Helper Lambda to configure S3 notifications.
*   **AWS::IAM::Role (`SetupNotificationRole`):** For the `SetupBucketNotificationFunction`.
*   **AWS::CloudFormation::CustomResource (`BucketNotificationConfiguration`):** Triggers the `SetupBucketNotificationFunction` to set S3 event notifications.

## Outputs

The stack will output the following values, which can be found in the "Outputs" tab of the CloudFormation stack in the AWS console:

*   `DynamoDBTableName`: The name of the created DynamoDB table.
*   `LambdaFunctionArn`: The ARN of the created data processing Lambda function.
*   `S3BucketName`: The name of the created S3 bucket.
*   `IAMRoleName`: The name of the IAM role created for the data processing Lambda.

## Cleanup

To remove all resources created by this stack, delete the CloudFormation stack:

### Using AWS CLI

```bash
aws cloudformation delete-stack --stack-name s3-csv-to-dynamodb-stack

## Using the solution
Once the CloudFormation template is deployed all the necessary infrastructure for the solution is in place.  You can use the **make-csv.py** script to generate sample CSV data that aligns with the structure of the Amazon DynamoDB table.

[Generate sample CSV file step by step instructions](https://aws.amazon.com/blogs/database/ingest-csv-data-to-amazon-dynamodb-using-aws-lambda/)