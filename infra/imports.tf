# These resources already existed before Terraform. Each block tells Terraform to adopt one,
# instead of trying to create a second copy.

import {
  to = aws_ecr_repository.bot
  id = "anamul-ai"
}

import {
  to = aws_dynamodb_table.chats
  id = "anamul-ai-chats"
}

import {
  to = aws_iam_role.bot
  id = "anamul-ai-lambda-role"
}

import {
  to = aws_iam_role_policy_attachment.logs
  id = "anamul-ai-lambda-role/arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

import {
  to = aws_iam_role_policy.save_chats
  id = "anamul-ai-lambda-role:save-chats"
}

import {
  to = aws_lambda_function.bot
  id = "anamul-ai"
}

import {
  to = aws_lambda_function_url.bot
  id = "anamul-ai"
}

import {
  to = aws_lambda_permission.url
  id = "anamul-ai/public-function-url"
}

import {
  to = aws_lambda_permission.url_invoke
  id = "anamul-ai/public-function-url-invoke"
}

import {
  to = aws_cloudwatch_log_group.bot
  id = "/aws/lambda/anamul-ai"
}
