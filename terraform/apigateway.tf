# Public entrypoint. API Gateway (HTTP API) fronts the whole app and reaches
# the internal ALB over a VPC Link.
resource "aws_apigatewayv2_api" "main" {
  name          = "${local.name}-api-gw"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers = ["authorization", "content-type"]
  }

  # GRAPHIX: this API gateway realizes the public edge gateway in the L2 model.
  tags = {
    graphix_l2 = "L2_EdgeGateway"
  }
}

resource "aws_security_group" "vpc_link" {
  name        = "${local.name}-vpclink-sg"
  description = "API Gateway VPC Link ENIs."
  vpc_id      = aws_vpc.main.id

  egress {
    description = "To the internal ALB."
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${local.name}-vpclink-sg"
  }
}

resource "aws_apigatewayv2_vpc_link" "main" {
  name               = "${local.name}-vpclink"
  security_group_ids = [aws_security_group.vpc_link.id]
  subnet_ids         = aws_subnet.private[*].id
}

resource "aws_apigatewayv2_integration" "alb" {
  api_id             = aws_apigatewayv2_api.main.id
  integration_type   = "HTTP_PROXY"
  integration_method = "ANY"
  integration_uri    = aws_lb_listener.http.arn
  connection_type    = "VPC_LINK"
  connection_id      = aws_apigatewayv2_vpc_link.main.id
}

resource "aws_apigatewayv2_route" "default" {
  api_id    = aws_apigatewayv2_api.main.id
  route_key = "$default"
  target    = "integrations/${aws_apigatewayv2_integration.alb.id}"
}

resource "aws_cloudwatch_log_group" "apigw" {
  name              = "/apigw/${local.name}"
  retention_in_days = 30
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.main.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.apigw.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
    })
  }
}
