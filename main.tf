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
  bucket = "weekly-volleyball"
  key    = "virtual-equator-386019-d1063402b3b1.json"
  source = "virtual-equator-386019-d1063402b3b1.json"
}

resource "aws_s3_object" "code_zip" {
  bucket = "weekly-volleyball"
  key    = "code_zip.zip"
  source = "code_zip.zip"
}

resource "aws_iam_role" "lambda_execution_role" {
  name = "vball_lambda_execution_role"

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
}

resource "aws_iam_policy" "lambda_execution_policy" {
  name = "vball_lambda_execution_policy"

  policy = jsonencode({
    Version = "2012-10-17"
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
      }
    ]
  })
}


resource "aws_iam_role_policy_attachment" "lambda_execution_policy_attachment" {
  policy_arn = aws_iam_policy.lambda_execution_policy.arn
  role       = aws_iam_role.lambda_execution_role.name
}

data "aws_s3_object" "code_zip" {
  bucket = aws_s3_bucket.volleyball_spreadsheets.id
  key    = "code_zip.zip"
}

resource "aws_lambda_function" "volleyball_tracker" {
  role             = aws_iam_role.lambda_execution_role.arn
  filename         = "code_zip.zip"
  function_name    = "volleyball-tracker"
  handler          = "spreadsheet.run"
  runtime          = "python3.8"
  timeout          = 30
  memory_size      = 128
}

