# My AWS setup for Anamul AI, written as code. I built it by hand in the console first (Days 12-19);
# imports.tf adopts those resources, so Terraform now tracks them instead of creating new ones.
#
# Run from this folder: terraform init (once), then terraform plan to see what would change.

terraform {
  required_version = ">= 1.5" # import blocks need 1.5+

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}
