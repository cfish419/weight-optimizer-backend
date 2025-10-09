output "flights_table_name" {
  description = "Name of the flights DynamoDB table"
  value       = aws_dynamodb_table.flights.name
}

output "flights_table_arn" {
  description = "ARN of the flights DynamoDB table"
  value       = aws_dynamodb_table.flights.arn
}

output "baggage_table_name" {
  description = "Name of the baggage DynamoDB table"
  value       = aws_dynamodb_table.baggage.name
}

output "baggage_table_arn" {
  description = "ARN of the baggage DynamoDB table"
  value       = aws_dynamodb_table.baggage.arn
}

output "aircraft_table_name" {
  description = "Name of the aircraft DynamoDB table"
  value       = aws_dynamodb_table.aircraft.name
}

output "aircraft_table_arn" {
  description = "ARN of the aircraft DynamoDB table"
  value       = aws_dynamodb_table.aircraft.arn
}

output "calculations_table_name" {
  description = "Name of the calculations DynamoDB table"
  value       = aws_dynamodb_table.calculations.name
}

output "calculations_table_arn" {
  description = "ARN of the calculations DynamoDB table"
  value       = aws_dynamodb_table.calculations.arn
}

output "table_arns" {
  description = "List of all DynamoDB table ARNs"
  value = [
    aws_dynamodb_table.flights.arn,
    aws_dynamodb_table.baggage.arn,
    aws_dynamodb_table.aircraft.arn,
    aws_dynamodb_table.calculations.arn
  ]
}