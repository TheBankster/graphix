resource "random_password" "db" {
  length  = 24
  special = false
}

# --- Database credentials ---
resource "aws_secretsmanager_secret" "db" {
  name        = "${local.name}/db/credentials"
  description = "RDS Postgres master credentials."
}

resource "aws_secretsmanager_secret_version" "db" {
  secret_id = aws_secretsmanager_secret.db.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db.result
    dbname   = var.db_name
    host     = aws_db_instance.postgres.address
    port     = aws_db_instance.postgres.port
  })
}

# --- SendGrid API key (email provider) ---
resource "aws_secretsmanager_secret" "sendgrid" {
  name        = "${local.name}/sendgrid/api-key"
  description = "SendGrid API key for transactional email."
}

resource "aws_secretsmanager_secret_version" "sendgrid" {
  secret_id     = aws_secretsmanager_secret.sendgrid.id
  secret_string = var.sendgrid_api_key
}

# --- Payment processor API key (external) ---
resource "aws_secretsmanager_secret" "payment" {
  name        = "${local.name}/payment-processor/api-key"
  description = "API key for the external payment processor."
}

resource "aws_secretsmanager_secret_version" "payment" {
  secret_id     = aws_secretsmanager_secret.payment.id
  secret_string = var.payment_processor_api_key
}
