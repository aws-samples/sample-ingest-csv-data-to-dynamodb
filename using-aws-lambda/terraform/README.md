# Terraform Configuration for CSV to DynamoDB ETL Pipeline

This directory contains Terraform configuration files to deploy the same infrastructure as the CloudFormation template, providing an Infrastructure as Code (IaC) alternative.

## 📁 File Structure

```
terraform/
├── main.tf                    # Main Terraform configuration
├── variables.tf               # Input variable definitions
├── outputs.tf                 # Output value definitions
├── setup_notification.py      # Setup Lambda function code
├── terraform.tfvars.example   # Example variables file
└── README.md                  # This file
```

## 🚀 Quick Start

### 1. Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0 installed
- AWS CLI configured with appropriate permissions
- The `import.py` file from the parent directory (Lambda function code)

### 2. Configuration

```bash
# Copy the example variables file
cp terraform.tfvars.example terraform.tfvars

# Edit terraform.tfvars with your specific values
# IMPORTANT: Change s3_bucket_name to something globally unique!
vim terraform.tfvars
```

### 3. Deploy

```bash
# Initialize Terraform
terraform init

# Review the planned changes
terraform plan

# Apply the configuration
terraform apply
```

### 4. Test the Deployment

```bash
# Generate test data (from parent directory)
cd ..
python make-csv.py --rows 100

# Upload test file
aws s3 cp data.csv s3://YOUR_BUCKET_NAME/

# Check results
terraform output monitoring_commands
```

## ⚙️ Configuration Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `aws_region` | AWS region for resources | `us-east-1` | No |
| `environment` | Environment name | `dev` | No |
| `dynamodb_table_name` | DynamoDB table name | `your-dynamodb-table-name` | Yes |
| `lambda_function_name` | Lambda function name | `your-lambda-function` | Yes |
| `s3_bucket_name` | S3 bucket name (globally unique) | `your-lambda-function` | Yes |
| `iam_role_name` | IAM role name | `iam-role-name` | Yes |
| `tags` | Additional resource tags | `{}` | No |

## 📤 Outputs

After deployment, Terraform provides useful outputs:

```bash
# View all outputs
terraform output

# Get specific output
terraform output s3_bucket_name
terraform output lambda_function_arn
```

## 🔧 Resource Details

### Created Resources

- **S3 Bucket**: CSV file storage with versioning and encryption
- **DynamoDB Table**: Pay-per-request table with composite key
- **Lambda Function**: Python 3.13 CSV processor (arm64)
- **IAM Roles & Policies**: Secure access permissions
- **S3 Notifications**: Automatic Lambda triggers

### Key Features

- **Terraform State Management**: Infrastructure state tracking
- **Variable Validation**: Input validation for resource names
- **Resource Tagging**: Consistent tagging across resources
- **Output Values**: Easy access to resource information
- **Dependencies**: Proper resource dependency management

## 🔄 Updates and Maintenance

### Updating the Infrastructure

```bash
# Review changes
terraform plan

# Apply updates
terraform apply
```

### Updating Lambda Function Code

```bash
# After modifying import.py, redeploy
terraform apply -replace=aws_lambda_function.import_lambda
```

## 🧹 Cleanup

```bash
# Destroy all resources
terraform destroy

# Confirm destruction
# Type 'yes' when prompted
```

**Note**: The S3 bucket is configured with `force_destroy = true` to allow deletion even if it contains objects.

## 🔒 Security Considerations

- **IAM Least Privilege**: Roles have minimal required permissions
- **S3 Encryption**: Bucket uses server-side encryption
- **Resource Isolation**: Resources are properly namespaced
- **State Security**: Store Terraform state securely (consider remote backends)

## 🆚 CloudFormation vs Terraform

| Feature | CloudFormation | Terraform |
|---------|---------------|----------|
| **Syntax** | YAML/JSON | HCL |
| **State Management** | AWS-managed | Local/Remote |
| **Multi-cloud** | AWS only | Multi-cloud |
| **Resource Updates** | Drift detection | Plan/Apply workflow |
| **Custom Resources** | Lambda-based | Providers/plugins |

## 🔍 Troubleshooting

### Common Issues

**S3 Bucket Already Exists**
```bash
# Error: BucketAlreadyExists
# Solution: Change s3_bucket_name in terraform.tfvars
```

**Lambda Function Not Triggering**
```bash
# Check S3 notification configuration
aws s3api get-bucket-notification-configuration --bucket YOUR_BUCKET_NAME

# Verify Lambda permissions
aws lambda get-policy --function-name YOUR_FUNCTION_NAME
```

**Permission Denied Errors**
```bash
# Check Terraform state for actual resource names
terraform show

# Verify IAM policies
aws iam list-attached-role-policies --role-name YOUR_ROLE_NAME
```

### Debug Commands

```bash
# View Terraform state
terraform state list
terraform state show aws_lambda_function.import_lambda

# Validate configuration
terraform validate

# Format configuration
terraform fmt
```

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Lambda Terraform Examples](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lambda_function)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)

---

**Built with ❤️ using Terraform and AWS best practices**

