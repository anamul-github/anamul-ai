resource "aws_lambda_function" "bot" {
  function_name = "anamul-ai"
  description   = "Anamul AI: answers questions about Anamul Hasan"
  role          = aws_iam_role.bot.arn
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.bot.repository_url}:latest"
  architectures = ["arm64"]
  memory_size   = 2048 # More memory also means more CPU: cold starts went from ~13 s to ~4 s at 2 GB
  timeout       = 60

  lifecycle {
    ignore_changes = [
      image_uri,   # deploy.sh sets the exact image on every deploy
      environment, # My API keys: set_lambda_keys.sh puts them there, and they never go in this repo
    ]
  }
}

# The bot's public address. Streaming mode lets answers appear word by word.
resource "aws_lambda_function_url" "bot" {
  function_name      = aws_lambda_function.bot.function_name
  authorization_type = "NONE" # Anyone can chat; the rate limit in api.py keeps it fair
  invoke_mode        = "RESPONSE_STREAM"
}

# Public access through the URL needs two permissions: one to call the URL, one to run the function
resource "aws_lambda_permission" "url" {
  statement_id           = "public-function-url"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.bot.function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "url_invoke" {
  statement_id             = "public-function-url-invoke"
  action                   = "lambda:InvokeFunction"
  function_name            = aws_lambda_function.bot.function_name
  principal                = "*"
  invoked_via_function_url = true
}

resource "aws_cloudwatch_log_group" "bot" {
  name = "/aws/lambda/${aws_lambda_function.bot.function_name}"
}

output "url" {
  description = "The address my website calls"
  value       = aws_lambda_function_url.bot.function_url
}
