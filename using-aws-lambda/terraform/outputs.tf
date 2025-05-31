# Output values for the CSV to DynamoDB ETL pipeline

output "dynamodb_table_name" {
  description = "The name of the created DynamoDB table"
  value       = aws_dynamodb_table.csv_data_table.name
}

output "dynamodb_table_arn" {
  description = "The ARN of the created DynamoDB table"
  value       = aws_dynamodb_table.csv_data_table.arn
}

output "lambda_function_arn" {
  description = "The ARN of the created Lambda function"
  value       = aws_lambda_function.import_lambda.arn
}

output "lambda_function_name" {
  description = "The name of the created Lambda function"
  value       = aws_lambda_function.import_lambda.function_name
}

output "s3_bucket_name" {
  description = "The name of the created S3 bucket"
  value       = aws_s3_bucket.import_bucket.id
}

output "s3_bucket_arn" {
  description = "The ARN of the created S3 bucket"
  value       = aws_s3_bucket.import_bucket.arn
}

output "iam_role_name" {
  description = "The name of the created IAM role"
  value       = aws_iam_role.lambda_execution_role.name
}

output "iam_role_arn" {
  description = "The ARN of the created IAM role"
  value       = aws_iam_role.lambda_execution_role.arn
}

output "upload_command" {
  description = "AWS CLI command to upload CSV files"
  value       = "aws s3 cp your-file.csv s3://${aws_s3_bucket.import_bucket.id}/"
}

output "monitoring_commands" {
  description = "Useful monitoring commands"
  value = {
    check_logs = "aws logs describe-log-groups --log-group-name-prefix '/aws/lambda/${aws_lambda_function.import_lambda.function_name}'"
    scan_table = "aws dynamodb scan --table-name ${aws_dynamodb_table.csv_data_table.name} --max-items 5"
    list_json_copies = "aws s3 ls s3://${aws_s3_bucket.import_bucket.id}/json-copy/"
    list_unprocessed = "aws s3 ls s3://${aws_s3_bucket.import_bucket.id}/unprocessed/"
  }
}

