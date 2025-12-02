terraform_main = '''terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# RDS PostgreSQL Database
resource "aws_db_instance" "freight_db" {
  identifier     = "freight-rate-predictor"
  engine         = "postgres"
  engine_version = "15.5"
  instance_class = "db.t3.micro"
  
  allocated_storage    = 20
  storage_type         = "gp3"
  storage_encrypted    = true
  
  db_name  = "freight_rates"
  username = var.db_username
  password = var.db_password
  
  skip_final_snapshot = false
  final_snapshot_identifier = "freight-db-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  
  publicly_accessible = false
  
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
  
  backup_retention_period = 7
  multi_az               = false
  
  tags = {
    Name        = "freight-rate-predictor"
    Environment = var.environment
  }
}

# Security Group for RDS
resource "aws_security_group" "rds_sg" {
  name        = "freight-rds-sg"
  description = "Security group for freight rate predictor RDS"
  
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  tags = {
    Name = "freight-rds-sg"
  }
}

# S3 Bucket for Data Lake
resource "aws_s3_bucket" "data_lake" {
  bucket = "freight-rate-data-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name        = "freight-data-lake"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "data_lake_versioning" {
  bucket = aws_s3_bucket.data_lake.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake_encryption" {
  bucket = aws_s3_bucket.data_lake.id
  
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket for Deployment Artifacts
resource "aws_s3_bucket" "deployment" {
  bucket = "freight-deployments-${data.aws_caller_identity.current.account_id}"
  
  tags = {
    Name        = "freight-deployments"
    Environment = var.environment
  }
}

# Lambda Execution Role
resource "aws_iam_role" "lambda_role" {
  name = "freight-lambda-role"
  
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
    Name = "freight-lambda-role"
  }
}

# Lambda Policy for RDS, S3, CloudWatch
resource "aws_iam_role_policy" "lambda_policy" {
  name = "freight-lambda-policy"
  role = aws_iam_role.lambda_role.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${aws_s3_bucket.data_lake.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "*"
      }
    ]
  })
}

# API Gateway
resource "aws_apigatewayv2_api" "freight_api" {
  name          = "freight-rate-api"
  protocol_type = "HTTP"
  
  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "OPTIONS"]
    allow_headers = ["*"]
  }
  
  tags = {
    Name = "freight-rate-api"
  }
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.freight_api.id
  name        = "prod"
  auto_deploy = true
  
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }
}

# CloudWatch Log Group for API
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/freight-rate-api"
  retention_in_days = 7
  
  tags = {
    Name = "freight-api-logs"
  }
}

# Data source for current AWS account
data "aws_caller_identity" "current" {}
'''

with open(f"{project_root}/infrastructure/terraform/main.tf", "w") as f:
    f.write(terraform_main)

# Create infrastructure/terraform/variables.tf
terraform_vars = '''variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "db_username" {
  description = "RDS master username"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "RDS master password"
  type        = string
  sensitive   = true
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "freight-rate-predictor"
}
'''

with open(f"{project_root}/infrastructure/terraform/variables.tf", "w") as f:
    f.write(terraform_vars)

# Create infrastructure/terraform/outputs.tf
terraform_outputs = '''output "rds_endpoint" {
  description = "RDS database endpoint"
  value       = aws_db_instance.freight_db.endpoint
}

output "rds_address" {
  description = "RDS database address"
  value       = aws_db_instance.freight_db.address
}

output "s3_data_lake_bucket" {
  description = "S3 data lake bucket name"
  value       = aws_s3_bucket.data_lake.id
}

output "s3_deployment_bucket" {
  description = "S3 deployment bucket name"
  value       = aws_s3_bucket.deployment.id
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_role.arn
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_stage.prod.invoke_url
}
'''

with open(f"{project_root}/infrastructure/terraform/outputs.tf", "w") as f:
    f.write(terraform_outputs)

# Create infrastructure/terraform/terraform.tfvars.example
terraform_tfvars = '''aws_region = "us-east-1"
environment = "production"
# Add your sensitive variables in terraform.tfvars (not in version control)
# db_username = "your_username"
# db_password = "your_password"
'''

with open(f"{project_root}/infrastructure/terraform/terraform.tfvars.example", "w") as f:
    f.write(terraform_tfvars)

print("✅ Created Terraform infrastructure files")