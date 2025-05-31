# Input variables for the CSV to DynamoDB ETL pipeline

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "dynamodb_table_name" {
  description = "The name of the DynamoDB table"
  type        = string
  default     = "your-dynamodb-table-name"
  
  validation {
    condition     = length(var.dynamodb_table_name) > 0 && length(var.dynamodb_table_name) <= 255
    error_message = "DynamoDB table name must be between 1 and 255 characters."
  }
}

variable "lambda_function_name" {
  description = "The name of the Lambda function"
  type        = string
  default     = "your-lambda-function"
  
  validation {
    condition     = length(var.lambda_function_name) > 0 && length(var.lambda_function_name) <= 64
    error_message = "Lambda function name must be between 1 and 64 characters."
  }
}

variable "s3_bucket_name" {
  description = "The name of the S3 bucket (must be globally unique)"
  type        = string
  default     = "your-lambda-function"
  
  validation {
    condition     = length(var.s3_bucket_name) >= 3 && length(var.s3_bucket_name) <= 63
    error_message = "S3 bucket name must be between 3 and 63 characters."
  }
}

variable "iam_role_name" {
  description = "The name of the IAM role"
  type        = string
  default     = "iam-role-name"
  
  validation {
    condition     = length(var.iam_role_name) > 0 && length(var.iam_role_name) <= 64
    error_message = "IAM role name must be between 1 and 64 characters."
  }
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

