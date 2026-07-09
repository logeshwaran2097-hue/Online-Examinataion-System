import secrets
from datetime import datetime, timedelta
from database import db
from models import OTPVerification

def generate_otp(length=6):
    """
    Generate a cryptographically secure numeric OTP of specified length.
    """
    return "".join(secrets.choice("0123456789") for _ in range(length))

def generate_and_save_otp(email):
    """
    Generate a new 6-digit OTP for the given email, save it to the database
    with a 5-minute expiration time, and invalidate any previous active OTPs.
    """
    # Invalidate previous OTPs for this email to prevent reuse/backlogs
    OTPVerification.query.filter_by(email=email, verification_status=False).delete()
    
    otp = generate_otp(6)
    expiry = datetime.utcnow() + timedelta(minutes=5)
    
    otp_entry = OTPVerification(
        email=email,
        otp=otp,
        expiry_time=expiry,
        verification_status=False
    )
    
    db.session.add(otp_entry)
    db.session.commit()
    return otp

def verify_otp(email, code):
    """
    Verify if the provided OTP code is valid and has not expired.
    Returns True and marks it as used if valid, otherwise False.
    """
    # Find matching unverified OTP entry
    otp_entry = OTPVerification.query.filter_by(
        email=email,
        otp=code,
        verification_status=False
    ).first()
    
    if not otp_entry:
        return False
        
    # Check expiry
    if datetime.utcnow() > otp_entry.expiry_time:
        return False
        
    # Mark as verified
    otp_entry.verification_status = True
    db.session.commit()
    return True
