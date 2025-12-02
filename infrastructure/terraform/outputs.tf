output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.freight_db.address
}

output "s3_data_lake_bucket" {
  description = "S3 data lake bucket"
  value       = aws_s3_bucket.data_lake.id
}
