#!/usr/bin/env bash
set -euo pipefail

# Setup AWS IAM OIDC role for GitHub Actions deployments
# - Creates GitHub OIDC provider if missing
# - Creates a deploy role with least-privilege policy
# - Optionally stores AWS secrets in the GitHub repo using gh CLI
#
# Usage:
#   GITHUB_OWNER=your-org GITHUB_REPO=your-repo \
#   AWS_REGION=us-east-1 \
#   STACK_NAME=TotalLifeAI-Prod-Clean \
#   ./setup-github-oidc.sh
#
# Optional:
#   ALLOW_ALL_BRANCHES=true (default only main)

command -v aws >/dev/null || { echo "AWS CLI is required"; exit 1; }
command -v jq >/dev/null || { echo "jq is required"; exit 1; }

AWS_REGION=${AWS_REGION:-us-east-1}
STACK_NAME=${STACK_NAME:-TotalLifeAI-Prod-Clean}
ALLOW_ALL_BRANCHES=${ALLOW_ALL_BRANCHES:-false}

# Try to infer owner/repo from git if not provided
if [[ -z "${GITHUB_OWNER:-}" || -z "${GITHUB_REPO:-}" ]]; then
  if command -v git >/dev/null; then
    ORIGIN=$(git config --get remote.origin.url || echo "")
    # Support https and ssh remotes
    if [[ "$ORIGIN" =~ github.com[:/](.+)/(.+)(\.git)?$ ]]; then
      GITHUB_OWNER=${GITHUB_OWNER:-${BASH_REMATCH[1]}}
      GITHUB_REPO=${GITHUB_REPO:-${BASH_REMATCH[2]%.git}}
    fi
  fi
fi

if [[ -z "${GITHUB_OWNER:-}" || -z "${GITHUB_REPO:-}" ]]; then
  echo "Please set GITHUB_OWNER and GITHUB_REPO env vars."
  exit 1
fi

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
OIDC_ARN="arn:aws:iam::${ACCOUNT_ID}:oidc-provider/token.actions.githubusercontent.com"

echo "Checking GitHub OIDC provider in account ${ACCOUNT_ID}..."
if ! aws iam get-open-id-connect-provider --open-id-connect-provider-arn "$OIDC_ARN" >/dev/null 2>&1; then
  echo "Creating GitHub OIDC provider..."
  aws iam create-open-id-connect-provider \
    --url https://token.actions.githubusercontent.com \
    --client-id-list sts.amazonaws.com \
    --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 >/dev/null
else
  echo "OIDC provider already exists."
fi

ROLE_NAME="TotalLifeAI-GitHubDeployRole"
ROLE_ARN="arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME}"

if aws iam get-role --role-name "$ROLE_NAME" >/dev/null 2>&1; then
  echo "Deploy role exists: $ROLE_ARN"
else
  echo "Creating deploy role: $ROLE_NAME"
  if [[ "$ALLOW_ALL_BRANCHES" == "true" ]]; then
    SUB_CLAIM="repo:${GITHUB_OWNER}/${GITHUB_REPO}:ref:refs/heads/*"
  else
    SUB_CLAIM="repo:${GITHUB_OWNER}/${GITHUB_REPO}:ref:refs/heads/main"
  fi

  cat > assume-role-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "${OIDC_ARN}" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": { "token.actions.githubusercontent.com:aud": "sts.amazonaws.com" },
        "StringLike": { "token.actions.githubusercontent.com:sub": "${SUB_CLAIM}" }
      }
    }
  ]
}
EOF

  aws iam create-role \
    --role-name "$ROLE_NAME" \
    --assume-role-policy-document file://assume-role-policy.json >/dev/null
fi

echo "Composing least-privilege inline policy..."

# Discover resource names from the stack for better scoping
CF_JSON=$(aws cloudformation describe-stacks --stack-name "$STACK_NAME" 2>/dev/null || echo '{}')
FRONTEND_BUCKET=$(echo "$CF_JSON" | jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="FrontendBucketName").OutputValue // empty')
CLUSTER_NAME=$(echo "$CF_JSON" | jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="ClusterName").OutputValue // empty')
SERVICE_NAME=$(echo "$CF_JSON" | jq -r '.Stacks[0].Outputs[] | select(.OutputKey=="ServiceName").OutputValue // empty')

S3_ARN_BUCKET="arn:aws:s3:::${FRONTEND_BUCKET:-*}"
S3_ARN_OBJECTS="arn:aws:s3:::${FRONTEND_BUCKET:-*}/*"
ECR_ARN="arn:aws:ecr:${AWS_REGION}:${ACCOUNT_ID}:repository/totallifeai-backend"
ECS_CLUSTER_ARN="arn:aws:ecs:${AWS_REGION}:${ACCOUNT_ID}:cluster/${CLUSTER_NAME:-*}"
ECS_SERVICE_ARN="arn:aws:ecs:${AWS_REGION}:${ACCOUNT_ID}:service/${CLUSTER_NAME:-*}/${SERVICE_NAME:-*}"
IAM_ROLE_WILDCARD="arn:aws:iam::${ACCOUNT_ID}:role/*"

cat > deploy-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ECRPushPull",
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:BatchGetImage",
        "ecr:DescribeRepositories"
      ],
      "Resource": ["${ECR_ARN}", "*"]
    },
    {
      "Sid": "ECSUpdateServiceAndTaskDef",
      "Effect": "Allow",
      "Action": [
        "ecs:DescribeServices",
        "ecs:DescribeTaskDefinition",
        "ecs:RegisterTaskDefinition",
        "ecs:UpdateService",
        "ecs:RunTask",
        "ecs:DescribeTasks",
        "ecs:ListTasks"
      ],
      "Resource": ["${ECS_CLUSTER_ARN}", "${ECS_SERVICE_ARN}", "*"]
    },
    {
      "Sid": "AllowPassTaskRolesToEcs",
      "Effect": "Allow",
      "Action": ["iam:PassRole"],
      "Resource": "${IAM_ROLE_WILDCARD}",
      "Condition": { "StringEquals": { "iam:PassedToService": "ecs-tasks.amazonaws.com" } }
    },
    {
      "Sid": "CFDescribe",
      "Effect": "Allow",
      "Action": ["cloudformation:DescribeStacks"],
      "Resource": "*"
    },
    {
      "Sid": "S3FrontendDeploy",
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": "${S3_ARN_BUCKET}"
    },
    {
      "Sid": "S3FrontendWrite",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:DeleteObject"],
      "Resource": "${S3_ARN_OBJECTS}"
    },
    {
      "Sid": "CloudFrontInvalidate",
      "Effect": "Allow",
      "Action": ["cloudfront:CreateInvalidation", "cloudfront:ListDistributions"],
      "Resource": "*"
    }
  ]
}
EOF

aws iam put-role-policy \
  --role-name "$ROLE_NAME" \
  --policy-name TotalLifeAI-GitHubDeployPolicy \
  --policy-document file://deploy-policy.json >/dev/null

echo "\n✅ Deploy role ready: $ROLE_ARN"

echo "\nNext: add repo secrets so GitHub Actions can deploy:"
echo "  AWS_ACCOUNT_ID=${ACCOUNT_ID}"
echo "  AWS_DEPLOY_ROLE_ARN=${ROLE_ARN}"

if command -v gh >/dev/null; then
  read -r -p "Set secrets in $GITHUB_OWNER/$GITHUB_REPO via gh now? [y/N] " yn
  if [[ "$yn" =~ ^[Yy]$ ]]; then
    gh secret set AWS_ACCOUNT_ID -b"${ACCOUNT_ID}" -R "$GITHUB_OWNER/$GITHUB_REPO"
    gh secret set AWS_DEPLOY_ROLE_ARN -b"${ROLE_ARN}" -R "$GITHUB_OWNER/$GITHUB_REPO"
    echo "✅ Secrets set in GitHub repo $GITHUB_OWNER/$GITHUB_REPO"
  else
    echo "Skipping gh secret set."
  fi
else
  echo "Install GitHub CLI (gh) to set secrets from terminal, or add them in the GitHub UI."
fi

echo "\nAll set. Push to main to trigger the workflow, or use the Actions tab to run manually."

