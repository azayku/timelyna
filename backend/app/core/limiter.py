"""Rate limiter configuration."""
from pyrate_limiter import Duration, Limiter, Rate

# Login attempts: 10 requests per minute
login_limiter = Limiter(Rate(10, Duration.MINUTE))

# Password reset requests: 5 requests per minute
password_reset_limiter = Limiter(Rate(5, Duration.MINUTE))
