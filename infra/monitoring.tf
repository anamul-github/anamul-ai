# Alerts: an email when the bot starts failing, gets a suspicious amount of traffic, or AWS costs more than expected.
# My email lives in terraform.tfvars, which git ignores, so it never appears in this public repo.

variable "alert_email" {
  description = "Where alerts go"
  type        = string
  sensitive   = true
}

resource "aws_sns_topic" "alerts" {
  name = "anamul-ai-alerts"
}

# AWS emails a confirmation link first; alerts only arrive after I click it
resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# api.py prints {"event": "answer_failed", ...} whenever Claude or Voyage fails. Visitors see "busy, try
# again", so without this count I would never know.
resource "aws_cloudwatch_log_metric_filter" "answer_failures" {
  name           = "answer-failures"
  log_group_name = aws_cloudwatch_log_group.bot.name
  pattern        = "{ $.event = \"answer_failed\" }"

  metric_transformation {
    name          = "AnswerFailures"
    namespace     = "AnamulAI"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "answer_failures" {
  alarm_name          = "anamul-ai-answer-failures"
  alarm_description   = "Claude or Voyage failed 3+ times in 5 minutes: visitors are getting \"busy, try again\"."
  namespace           = "AnamulAI"
  metric_name         = "AnswerFailures"
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 3
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn] # Also tell me when it's fixed
}

# Lambda itself crashed or timed out (not just a busy API): the bot may be down
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "anamul-ai-lambda-errors"
  alarm_description   = "The Lambda function crashed or timed out. Check the logs."
  namespace           = "AWS/Lambda"
  metric_name         = "Errors"
  dimensions          = { FunctionName = aws_lambda_function.bot.function_name }
  statistic           = "Sum"
  period              = 300
  evaluation_periods  = 1
  threshold           = 1
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
  ok_actions          = [aws_sns_topic.alerts.arn]
}

# My usual traffic is a few dozen questions a day. 200 in an hour would mean a bot or an attack running up
# my Claude bill, even with the per-visitor limit (many visitors x 20 questions each).
resource "aws_cloudwatch_metric_alarm" "traffic_spike" {
  alarm_name          = "anamul-ai-traffic-spike"
  alarm_description   = "200+ requests in one hour. Check who is asking, and the Claude bill."
  namespace           = "AWS/Lambda"
  metric_name         = "Invocations"
  dimensions          = { FunctionName = aws_lambda_function.bot.function_name }
  statistic           = "Sum"
  period              = 3600
  evaluation_periods  = 1
  threshold           = 200
  comparison_operator = "GreaterThanOrEqualToThreshold"
  treat_missing_data  = "notBreaching"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# Every deploy leaves a ~300 MB image behind, and storage past the free 500 MB costs money.
# Keep the newest 5: enough to roll back a few deploys.
resource "aws_ecr_lifecycle_policy" "keep_recent" {
  repository = aws_ecr_repository.bot.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep only the 5 newest images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 5
      }
      action = { type = "expire" }
    }]
  })
}

# A monthly budget for the whole AWS account: an email at 80% of $5 spent, and when AWS forecasts going over.
# It replaces the "zero-spend" budget, which emailed at $0.01 and was already set off by image storage.
resource "aws_budgets_budget" "monthly" {
  name         = "anamul-ai-monthly"
  budget_type  = "COST"
  limit_amount = "5"
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.alert_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.alert_email]
  }
}
