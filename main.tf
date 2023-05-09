provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "volleyball_spreadsheets" {
  bucket = "weekly-volleyball"
}

resource "aws_s3_bucket_versioning" "volleyball_spreadsheets_versioning" {
  bucket = aws_s3_bucket.volleyball_spreadsheets.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "json_key" {
  depends_on = [ aws_s3_bucket.volleyball_spreadsheets, aws_s3_bucket_versioning.volleyball_spreadsheets_versioning ]
  bucket     = "weekly-volleyball"
  key        = "virtual-equator-386019-d1063402b3b1.json"
  source     = "virtual-equator-386019-d1063402b3b1.json"
}

resource "aws_s3_object" "code_zip" {
  depends_on = [ aws_s3_bucket.volleyball_spreadsheets, aws_s3_bucket_versioning.volleyball_spreadsheets_versioning ]
  bucket     = "weekly-volleyball"
  key        = "code_zip.zip"
  source     = "code_zip.zip"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "vball_lambda_execution_role"


  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action    = "sts:AssumeRole"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_dynamodb_table" "volleyball_tracker" {
  name         = "volleyball_tracker"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }
}

resource "aws_dynamodb_table_item" "example_item" {
  depends_on = [ aws_dynamodb_table.volleyball_tracker ]
  table_name = aws_dynamodb_table.volleyball_tracker.name
  hash_key   = aws_dynamodb_table.volleyball_tracker.hash_key
  item       = <<ITEM
{
  "id": {"S": "week_counter"},
  "current_week": {"N": "0"},
  "current_session": {"N": "1"}
}
ITEM
}




resource "aws_iam_policy" "lambda_execution_policy" {
  name   = "vball_lambda_execution_policy"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.volleyball_spreadsheets.arn}/*"
      },
      {
        Action = [
          "dynamodb:GetItem",
          "dynamodb:UpdateItem"
        ]
        Effect   = "Allow"
        Resource = "${aws_dynamodb_table.volleyball_tracker.arn}"
      },
      {
        Action = [
            "ses:SendEmail"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:ses:us-east-1:*:*"
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "lambda_execution_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_execution_policy.arn
  role       = aws_iam_role.lambda_execution_role.name
}

resource "aws_lambda_function" "volleyball_tracker" {
  depends_on = [ 
    aws_iam_role_policy_attachment.lambda_execution_policy_attachment,
    aws_dynamodb_table.volleyball_tracker,
    aws_s3_bucket.volleyball_spreadsheets
   ]
  role             = aws_iam_role.lambda_execution_role.arn
  filename         = "code_zip.zip"
  function_name    = "volleyball-tracker"
  handler          = "spreadsheet.run"
  runtime          = "python3.8"
  timeout          = 30
  memory_size      = 128
}

