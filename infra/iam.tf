# The identity the Lambda function runs as. It may write logs and save chats, nothing else.
resource "aws_iam_role" "bot" {
  name        = "anamul-ai-lambda-role"
  description = "Lets the Anamul AI Lambda function run and write logs"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.bot.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Only add and update chats, only in my table: the bot can't read, list or delete anything
resource "aws_iam_role_policy" "save_chats" {
  name = "save-chats"
  role = aws_iam_role.bot.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["dynamodb:PutItem", "dynamodb:UpdateItem"]
      Resource = aws_dynamodb_table.chats.arn
    }]
  })
}
