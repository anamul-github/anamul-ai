# Lets GitHub Actions deploy the bot without any AWS keys stored in GitHub.
# GitHub proves who it is with a short-lived token (OIDC); AWS checks the token and hands out
# temporary credentials, only to my repo's main branch, only for what deploy.sh needs.

resource "aws_iam_openid_connect_provider" "github" {
  url            = "https://token.actions.githubusercontent.com"
  client_id_list = ["sts.amazonaws.com"]
}

resource "aws_iam_role" "github_deploy" {
  name        = "anamul-ai-github-deploy"
  description = "GitHub Actions deploys Anamul AI from the main branch"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Federated = aws_iam_openid_connect_provider.github.arn }
      Action    = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          # Only workflows running on main in my repo: not forks, not other branches
          "token.actions.githubusercontent.com:sub" = "repo:anamul-github/anamul-ai:ref:refs/heads/main"
        }
      }
    }]
  })
}

# Exactly what scripts/deploy.sh does: push an image to my ECR repo, point Lambda at it, check it
resource "aws_iam_role_policy" "github_deploy" {
  name = "deploy"
  role = aws_iam_role.github_deploy.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "ecr:GetAuthorizationToken" # Logging in to ECR can't be limited to one repo
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:BatchGetImage",
          "ecr:CompleteLayerUpload",
          "ecr:GetDownloadUrlForLayer",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
        ]
        Resource = aws_ecr_repository.bot.arn
      },
      {
        Effect = "Allow"
        Action = [
          "lambda:GetFunction",
          "lambda:GetFunctionConfiguration",
          "lambda:GetFunctionUrlConfig",
          "lambda:UpdateFunctionCode",
        ]
        Resource = aws_lambda_function.bot.arn
      },
    ]
  })
}

output "github_deploy_role_arn" {
  description = "Goes in GitHub as the repository variable AWS_DEPLOY_ROLE_ARN"
  value       = aws_iam_role.github_deploy.arn
}
