# Where the bot's container images live. deploy.sh pushes a new one on every deploy.
resource "aws_ecr_repository" "bot" {
  name                 = "anamul-ai"
  image_tag_mutability = "MUTABLE" # deploy.sh moves the "latest" tag, but deploys by digest

  image_scanning_configuration {
    scan_on_push = true
  }
}

# Visitors' questions and answers, with no names or IP addresses. Each chat deletes itself after 90 days.
resource "aws_dynamodb_table" "chats" {
  name         = "anamul-ai-chats"
  billing_mode = "PAY_PER_REQUEST" # Pay per chat, nothing when nobody visits
  hash_key     = "id"

  attribute {
    name = "id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }
}
