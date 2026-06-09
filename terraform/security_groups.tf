# --- ALB: receives traffic from API Gateway VPC Link ---
resource "aws_security_group" "alb" {
  name        = "${local.name}-alb-sg"
  description = "Internal ALB fronting the ECS services."
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "HTTP from within the VPC (API Gateway VPC Link)."
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name}-alb-sg"
  }
}

# --- SPA container ---
resource "aws_security_group" "spa" {
  name        = "${local.name}-spa-sg"
  description = "SPA frontend tasks."
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Traffic from the ALB only."
    from_port       = 8080
    to_port         = 8080
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name}-spa-sg"
  }
}

# --- API container ---
resource "aws_security_group" "api" {
  name        = "${local.name}-api-sg"
  description = "API backend tasks."
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Traffic from the ALB only."
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${local.name}-api-sg"
  }
}

# --- RDS Postgres ---
resource "aws_security_group" "db" {
  name        = "${local.name}-db-sg"
  description = "RDS Postgres, reachable only from the API."
  vpc_id      = aws_vpc.main.id

  ingress {
    description     = "Postgres from the API tasks only."
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.api.id]
  }

  tags = {
    Name = "${local.name}-db-sg"
  }
}
