data "aws_iam_policy_document" "ecs_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

# --- Execution role: pull images, write logs, read secrets at task start ---
resource "aws_iam_role" "ecs_execution" {
  name               = "${local.name}-ecs-execution"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "secrets_read" {
  statement {
    actions = ["secretsmanager:GetSecretValue"]
    resources = [
      aws_secretsmanager_secret.db.arn,
      aws_secretsmanager_secret.sendgrid.arn,
      aws_secretsmanager_secret.payment.arn,
    ]
  }
}

resource "aws_iam_role_policy" "execution_secrets" {
  name   = "${local.name}-execution-secrets"
  role   = aws_iam_role.ecs_execution.id
  policy = data.aws_iam_policy_document.secrets_read.json
}

# --- Task role for the API: runtime access to secrets ---
resource "aws_iam_role" "api_task" {
  name               = "${local.name}-api-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}

resource "aws_iam_role_policy" "api_task_secrets" {
  name   = "${local.name}-api-task-secrets"
  role   = aws_iam_role.api_task.id
  policy = data.aws_iam_policy_document.secrets_read.json
}

# --- Task role for the SPA (no privileged access needed) ---
resource "aws_iam_role" "spa_task" {
  name               = "${local.name}-spa-task"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume.json
}
