"""
ALTERNATIVE: SendGrid Email Backend Configuration

Use this if Gmail SMTP isn't working.
SendGrid is more reliable and free for up to 100 emails/day.
"""

# TO SWITCH TO SENDGRID:
# 1. Sign up at https://sendgrid.com (free account)
# 2. Get your API Key from SendGrid dashboard
# 3. On Render, set environment variables:
#    - SENDGRID_API_KEY = your_key_from_sendgrid
#    - EMAIL_FROM_ADDRESS = noreply@yourdomain.com
# 4. Replace the EMAIL section in quizz_app/settings.py with this:

EMAIL_SECTION_FOR_SENDGRID = """
import os

# SendGrid Configuration (Alternative to Gmail SMTP)
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')

if SENDGRID_API_KEY:
    EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
    SENDGRID_SANDBOX_MODE_IN_DEBUG = False
else:
    # Fallback to console if no SendGrid key
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEFAULT_FROM_EMAIL = os.getenv(
    'EMAIL_FROM_ADDRESS',
    'noreply@quizfy.com'
)

# Alternative: If you still want Gmail but as backup
USE_GMAIL_BACKUP = False
if USE_GMAIL_BACKUP:
    EMAIL_HOST = 'smtp.gmail.com'
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = 'quizfyplatform@gmail.com'
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
"""

# INSTALLATION:
INSTALL_COMMAND = """
pip install sendgrid-django
"""

# Why SendGrid is better:
# ✓ Designed for transactional emails
# ✓ Better deliverability
# ✓ No 2-Step Verification needed
# ✓ Free tier: 100 emails/day
# ✓ Professional infrastructure
# ✓ Less likely to be blocked
# ✓ Easier to debug

# Why Gmail SMTP fails:
# ✗ Gmail treats SMTP as security risk
# ✗ Requires 2-Step Verification
# ✗ Requires app password (different from login)
# ✗ Some regions/ISPs block port 587
# ✗ Gmail may block Render's IP
# ✗ Less reliable for automated emails

print(__doc__)
