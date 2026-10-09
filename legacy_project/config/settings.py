# settings.py
# Application configuration
# DO NOT commit production values to git (but we do anyway)

# Application
APP_NAME = "OrderSystem"
APP_VERSION = "1.2.3"
DEBUG = True  # TODO: set to False in production

# Database
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "orders_db"
DB_USER = "admin"
DB_PASSWORD = "admin123"

# Paths
DATA_PATH = "data/"
LOG_PATH = "logs/"
EXPORT_PATH = "exports/"

# Business rules (magic numbers that should be named constants)
TAX_RATE_PREMIUM = 0.15
TAX_RATE_STANDARD = 0.2
DISCOUNT_LARGE = 0.05    # for orders > 1000
DISCOUNT_MEDIUM = 0.03   # for orders > 500
MIN_AGE = 18
PREMIUM_ROLE = 3
REGULAR_ROLE = 2

# Email
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "noreply@company.com"
SMTP_PASS = "Password123!"

# Limits
MAX_ORDERS_PER_DAY = 50
SESSION_TIMEOUT = 3600
MAX_RETRIES = 3
