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
    # HTML email formatting to reduce spam score and land in inbox
    html_body = None
    if purpose == "verification":
        subject = "Verify Your Account - Online Examination System"
        body = f"""Hello,

Thank you for registering at Online Examination System.

Your 6-digit email verification OTP is: {otp}

This code is valid for 5 minutes. Please do not share this OTP with anyone.

Best regards,
EduExam Support Team
"""
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f5f7; margin: 0; padding: 20px; }}
        .card {{ max-width: 500px; background: #ffffff; margin: 40px auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; text-align: center; margin-bottom: 20px; }}
        .title {{ font-size: 20px; font-weight: 600; color: #1e293b; margin-bottom: 15px; text-align: center; }}
        .otp-container {{ background: #f1f5f9; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0; border: 1px dashed #cbd5e1; }}
        .otp {{ font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #2563eb; margin: 0; }}
        .footer {{ font-size: 12px; color: #64748b; text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">EduExam</div>
        <div class="title">Verify Your Account</div>
        <p>Hello,</p>
        <p>Thank you for registering at Online Examination System. Use the following 6-digit verification code to complete your registration:</p>
        <div class="otp-container">
            <div class="otp">{otp}</div>
        </div>
        <p style="color: #64748b; font-size: 14px;">This code is valid for 5 minutes. Please do not share this OTP with anyone.</p>
        <div class="footer">
            Best regards,<br>
            <strong>EduExam Support Team</strong>
        </div>
    </div>
</body>
</html>"""
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
        html_body = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f5f7; margin: 0; padding: 20px; }}
        .card {{ max-width: 500px; background: #ffffff; margin: 40px auto; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); border: 1px solid #e1e4e8; }}
        .logo {{ font-size: 24px; font-weight: bold; color: #2563eb; text-align: center; margin-bottom: 20px; }}
        .title {{ font-size: 20px; font-weight: 600; color: #1e293b; margin-bottom: 15px; text-align: center; }}
        .btn-container {{ text-align: center; margin: 25px 0; }}
        .btn {{ background: #2563eb; color: #ffffff !important; padding: 12px 30px; text-decoration: none; border-radius: 30px; font-weight: 600; display: inline-block; box-shadow: 0 4px 10px rgba(37,99,235,0.2); }}
        .otp-container {{ background: #f1f5f9; padding: 15px; text-align: center; border-radius: 8px; margin: 20px 0; border: 1px dashed #cbd5e1; }}
        .otp {{ font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #2563eb; margin: 0; }}
        .footer {{ font-size: 12px; color: #64748b; text-align: center; margin-top: 30px; border-top: 1px solid #e2e8f0; padding-top: 15px; }}
    </style>
</head>
<body>
    <div class="card">
        <div class="logo">EduExam</div>
        <div class="title">Reset Your Password</div>
        <p>Hello,</p>
        <p>We received a request to reset your password for the Online Examination System. Click the button below to reset your password immediately:</p>
        <div class="btn-container">
            <a href="{reset_link}" class="btn" target="_blank">Reset Password</a>
        </div>
        <p>Or you can enter the following 6-digit OTP code manually on the reset page:</p>
        <div class="otp-container">
            <div class="otp">{otp}</div>
        </div>
        <p style="color: #64748b; font-size: 14px;">This code and link are valid for 5 minutes. If you did not request this password reset, please ignore this email.</p>
        <div class="footer">
            Best regards,<br>
            <strong>EduExam Support Team</strong>
        </div>
    </div>
</body>
</html>"""
    else:
        subject = "OTP Notification"
        body = f"Your OTP is: {otp}"

    try:
        # Fallback check for missing SMTP configuration to avoid waiting for connection timeouts
        if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_SERVER'):
            raise Exception("Mail server credentials are not configured in environment variables.")

        # Resolve correct sender: Prefer MAIL_DEFAULT_SENDER, fall back to authenticated MAIL_USERNAME to avoid spoofing flags
        raw_sender = current_app.config.get('MAIL_DEFAULT_SENDER') or current_app.config.get('MAIL_USERNAME') or 'no-reply@eduexam.com'
        sender_tuple = ("EduExam Support", raw_sender)

        msg = Message(
            subject=subject,
            recipients=[recipient_email],
            body=body,
            html=html_body,
            sender=sender_tuple
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
