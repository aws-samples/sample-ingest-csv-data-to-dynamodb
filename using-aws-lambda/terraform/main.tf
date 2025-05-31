# Provider configuration
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# Data sources
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Create zip file for Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../import.py"
  output_path = "${path.module}/lambda_function.zip"
}

# Create zip file for setup notification Lambda
data "archive_file" "setup_lambda_zip" {
  type        = "zip"
  output_path = "${path.module}/setup_lambda.zip"
  source {
    content = templatefile("${path.module}/setup_notification.py", {})
    filename = "index.py"
  }
}

# S3 Bucket for CSV files
resource "aws_s3_bucket" "import_bucket" {
  bucket        = var.s3_bucket_name
  force_destroy = true

  tags = {
    Name        = var.s3_bucket_name
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "import_bucket_versioning" {
  bucket = aws_s3_bucket.import_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket server-side encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "import_bucket_encryption" {
  bucket = aws_s3_bucket.import_bucket.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# DynamoDB Table
resource "aws_dynamodb_table" "csv_data_table" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "account"
  range_key      = "offer_id"

  attribute {
    name = "account"
    type = "S"
  }

  attribute {
    name = "offer_id"
    type = "S"
  }

  tags = {
    Name        = var.dynamodb_table_name
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# IAM Role for Lambda execution
resource "aws_iam_role" "lambda_execution_role" {
  name = var.iam_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = var.iam_role_name
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# Attach basic execution role policy
resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Custom IAM Policy for DynamoDB and S3 access
resource "aws_iam_policy" "dynamodb_s3_policy" {
  name        = "DynamoDBWriteS3ReadPolicy-${var.environment}"
  description = "Policy for Lambda to access DynamoDB and S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:BatchWriteItem"
        ]
        Resource = aws_dynamodb_table.csv_data_table.arn
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.import_bucket.arn,
          "${aws_s3_bucket.import_bucket.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${aws_s3_bucket.import_bucket.arn}/json-copy/*",
          "${aws_s3_bucket.import_bucket.arn}/unprocessed/*"
        ]
      }
    ]
  })

  tags = {
    Name        = "DynamoDBWriteS3ReadPolicy"
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# Attach custom policy to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_custom_policy" {
  role       = aws_iam_role.lambda_execution_role.name
  policy_arn = aws_iam_policy.dynamodb_s3_policy.arn
}

# Lambda Function for CSV processing
resource "aws_lambda_function" "import_lambda" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = var.lambda_function_name
  role            = aws_iam_role.lambda_execution_role.arn
  handler         = "import.lambda_handler"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  runtime         = "python3.13"
  timeout         = 180
  memory_size     = 2048
  architectures   = ["arm64"]

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      DYNAMO_DB_TABLE_NAME = var.dynamodb_table_name
    }
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_basic_execution,
    aws_iam_role_policy_attachment.lambda_custom_policy,
  ]

  tags = {
    Name        = var.lambda_function_name
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# Lambda permission for S3 to invoke the function
resource "aws_lambda_permission" "s3_invoke_lambda" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.import_lambda.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.import_bucket.arn
  source_account = data.aws_caller_identity.current.account_id
}

# IAM Role for setup notification Lambda
resource "aws_iam_role" "setup_notification_role" {
  name = "${var.iam_role_name}-setup-notification"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.iam_role_name}-setup-notification"
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# Attach basic execution role policy to setup Lambda
resource "aws_iam_role_policy_attachment" "setup_lambda_basic_execution" {
  role       = aws_iam_role.setup_notification_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# IAM Policy for setup notification Lambda
resource "aws_iam_policy" "setup_notification_policy" {
  name        = "S3NotificationPermission-${var.environment}"
  description = "Policy for setup notification Lambda"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutBucketNotification",
          "s3:GetBucketNotification",
          "s3:PutBucketNotificationConfiguration"
        ]
        Resource = aws_s3_bucket.import_bucket.arn
      }
    ]
  })

  tags = {
    Name        = "S3NotificationPermission"
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# Attach setup notification policy
resource "aws_iam_role_policy_attachment" "setup_notification_policy_attachment" {
  role       = aws_iam_role.setup_notification_role.name
  policy_arn = aws_iam_policy.setup_notification_policy.arn
}

# Lambda Function for S3 notification setup
resource "aws_lambda_function" "setup_notification_lambda" {
  filename         = data.archive_file.setup_lambda_zip.output_path
  function_name    = "${var.lambda_function_name}-setup-notification"
  role            = aws_iam_role.setup_notification_role.arn
  handler         = "index.handler"
  source_code_hash = data.archive_file.setup_lambda_zip.output_base64sha256
  runtime         = "python3.9"
  timeout         = 60

  depends_on = [
    aws_iam_role_policy_attachment.setup_lambda_basic_execution,
    aws_iam_role_policy_attachment.setup_notification_policy_attachment,
  ]

  tags = {
    Name        = "${var.lambda_function_name}-setup-notification"
    Environment = var.environment
    Project     = "CSV-to-DynamoDB-ETL"
  }
}

# S3 Bucket Notification using the setup Lambda
resource "aws_s3_bucket_notification" "import_bucket_notification" {
  bucket = aws_s3_bucket.import_bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.import_lambda.arn
    events              = ["s3:ObjectCreated:*"]
  }

  depends_on = [
    aws_lambda_permission.s3_invoke_lambda,
    aws_lambda_function.import_lambda,
  ]
}

