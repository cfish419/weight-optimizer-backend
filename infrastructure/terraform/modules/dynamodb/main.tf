terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# DynamoDB Tables for Weight Optimizer

# Flights Table
resource "aws_dynamodb_table" "flights" {
  name           = "${var.table_prefix}-flights"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "flight_id"

  attribute {
    name = "flight_id"
    type = "S"
  }

  attribute {
    name = "flight_number"
    type = "S"
  }

  attribute {
    name = "departure_date"
    type = "S"
  }

  global_secondary_index {
    name     = "FlightNumberIndex"
    hash_key = "flight_number"
  }

  global_secondary_index {
    name     = "DepartureDateIndex"
    hash_key = "departure_date"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-flights-table"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Baggage Table
resource "aws_dynamodb_table" "baggage" {
  name           = "${var.table_prefix}-baggage"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "baggage_id"

  attribute {
    name = "baggage_id"
    type = "S"
  }

  attribute {
    name = "flight_id"
    type = "S"
  }

  global_secondary_index {
    name     = "FlightBaggageIndex"
    hash_key = "flight_id"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-baggage-table"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Aircraft Configurations Table
resource "aws_dynamodb_table" "aircraft" {
  name           = "${var.table_prefix}-aircraft"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "aircraft_id"

  attribute {
    name = "aircraft_id"
    type = "S"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name        = "${var.project_name}-aircraft-table"
    Environment = var.environment
    Project     = var.project_name
  }
}

# Calculation Results Table
resource "aws_dynamodb_table" "calculations" {
  name           = "${var.table_prefix}-calculations"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "calculation_id"

  attribute {
    name = "calculation_id"
    type = "S"
  }

  attribute {
    name = "flight_id"
    type = "S"
  }

  global_secondary_index {
    name     = "FlightCalculationsIndex"
    hash_key = "flight_id"
  }

  server_side_encryption {
    enabled = true
  }

  point_in_time_recovery {
    enabled = true
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  tags = {
    Name        = "${var.project_name}-calculations-table"
    Environment = var.environment
    Project     = var.project_name
  }
}