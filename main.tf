provider "aws" {
  region = "us-east-1"
}

resource "aws_s3_bucket" "volleyball_spreadsheets" {
  bucket = "weekly-volleyball-spreadsheets"
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

resource "null_resource" "zip_files" {
  provisioner "local-exec" {
    command = "zip -j ./Archive.zip ./dependencies/* ./spreadsheets.py"
  }
}

data "archive_file" "my_zip" {
  type        = "zip"
  source_file = "${null_resource.zip_files.id}"
}

resource "aws_lambda_function" "volleyball_tracker" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "volleyball-tracker"
  role             = aws_iam_role.lambda_execution_role.arn
  handler          = "lambda_function.run"
  runtime          = "python3.8"
  timeout          = 10
  memory_size      = 128
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  environment {
    variables = {
      SHEET_NAME       = "Volleyball"
      WORKSHEET_NAME   = "Early Summer"
      BUCKET_NAME      = aws_s3_bucket.volleyball_spreadsheets.id
      OBJECT_KEY       = "virtual-equator-386019-d1063402b3b1.json"
      TABLE_NAME       = "volleyball_tracker"
      REGION           = "us-east-1"
    }
  }
}

resource "aws_cloudwatch_event_rule" "lambda_trigger" {
  name        = "vball-scheduler"
  description = "Trigger the lambda function once every 7 days starting May 25th"
  schedule_expression = "cron(0 23 25-31 5/7 ? 2023)"
}

resource "aws_lambda_permission" "allow_eventbridge_trigger" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.volleyball_tracker.arn
  principal     = "events.amazonaws.com"
}

resource "aws_cloudwatch_event_target" "target_lambda_function" {
  rule      = aws_cloudwatch_event_rule.lambda_trigger.name
  arn       = aws_lambda_function.volleyball_tracker.arn
  target_id = "TargetFunctionV1"
}

