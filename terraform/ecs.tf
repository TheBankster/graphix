resource "aws_ecs_cluster" "main" {
  name = "${local.name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_cloudwatch_log_group" "spa" {
  name              = "/ecs/${local.name}/spa"
  retention_in_days = 30
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${local.name}/api"
  retention_in_days = 30
}

# --- SPA task & service ---
resource "aws_ecs_task_definition" "spa" {
  family                   = "${local.name}-spa"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.spa_task.arn

  container_definitions = jsonencode([
    {
      name      = "spa"
      image     = var.spa_image
      essential = true
      portMappings = [
        { containerPort = 8080, protocol = "tcp" }
      ]
      environment = [
        # The SPA calls the API through the same public origin under /api.
        { name = "API_BASE_URL", value = "/api" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.spa.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "spa"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "spa" {
  name            = "${local.name}-spa"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.spa.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.spa.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.spa.arn
    container_name   = "spa"
    container_port   = 8080
  }

  # GRAPHIX: this service realizes the Web Front-End container in the L2 model.
  tags = {
    graphix_l2 = "L2_WebFrontEnd"
  }

  depends_on = [aws_lb_listener.http]
}

# --- API task & service ---
resource "aws_ecs_task_definition" "api" {
  family                   = "${local.name}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 512
  memory                   = 1024
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.api_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.api_image
      essential = true
      portMappings = [
        { containerPort = 8000, protocol = "tcp" }
      ]
      environment = [
        { name = "PAYMENT_PROCESSOR_URL", value = var.payment_processor_url }
      ]
      secrets = [
        { name = "DATABASE_CREDENTIALS", valueFrom = aws_secretsmanager_secret.db.arn },
        { name = "SENDGRID_API_KEY", valueFrom = aws_secretsmanager_secret.sendgrid.arn },
        { name = "PAYMENT_PROCESSOR_API_KEY", valueFrom = aws_secretsmanager_secret.payment.arn }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
        }
      }
    }
  ])
}

resource "aws_ecs_service" "api" {
  name            = "${local.name}-api"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.api.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 8000
  }

  # GRAPHIX: this service realizes the Processing Engine container in the L2 model.
  tags = {
    graphix_l2 = "L2_ProcessingEngine"
  }

  depends_on = [aws_lb_listener_rule.api]
}
