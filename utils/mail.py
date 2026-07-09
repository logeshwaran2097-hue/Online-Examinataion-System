import sys
from flask_mail import Message
from database import mail
from flask import current_app

def send_otp_email(recipient_email, otp, purpose="verification"):
    """
    Send an OTP email using Flask-Mail.
    Handles 'verification' (account registration) and 'reset' (password reset).
    Gracefully catches socket/SMTP errors and outputs to stderr for easier local development.
    """
    if purpose == "verification":
        subject = "Verify Your Account - Online Examination System"
        body = f"""Hello,

Thank you for registering at Online Examination System.

Your 6-digit email verification OTP is: {otp}

This code is valid for 5 minutes. Please do not share this OTP with anyone.

Best regards,
EduExam Support Team
"""
    elif purpose == "reset":
        subject = "Reset Your Password - Online Examination System"
        try:
            from flask import request, url_for
            reset_link = f"{request.host_url.rstrip('/')}{url_for('auth.reset_password', email=recipient_email, code=otp)}"
        except Exception:
            reset_link = f"http://localhost:5000/reset-password?email={recipient_email}&code={otp}"
        body = f"""Hello,

We received a request to reset your password for the Online Examination System.

You can reset your password immediately by clicking the link below:
{reset_link}

Or you can enter the following 6-digit OTP code manually: {otp}

This code and link are valid for 5 minutes. If you did not make this request, please ignore this email.

Best regards,
EduExam Support Team
"""
    else:
        subject = "OTP Notification"
        body = f"Your OTP is: {otp}"

    try:
        # Fallback check for missing SMTP configuration to avoid waiting for connection timeouts
        if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_SERVER'):
            raise Exception("Mail server credentials are not configured in environment variables.")

        sender = current_app.config.get('MAIL_DEFAULT_SENDER') or 'no-reply@eduexam.com'
        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body,
            sender=sender
        )
        mail.send(msg)
        print(f"SUCCESS: Verification email sent to {recipient_email}.", file=sys.stdout)
        return True
    except Exception as e:
        # Development fallback: log details to console so developer/tester can access the OTP
        print(f"\n[MAIL SYSTEM FALLBACK] Failed to send email to {recipient_email}: {e}", file=sys.stderr)
        print(f"----------------------------------------", file=sys.stderr)
        print(f"Recipient: {recipient_email}", file=sys.stderr)
        print(f"Subject:   {subject}", file=sys.stderr)
        print(f"OTP Code:  {otp}", file=sys.stderr)
        print(f"----------------------------------------\n", file=sys.stderr)
        return False
