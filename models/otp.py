from datetime import datetime
from database import db

class OTPVerification(db.Model):
    """
    Model representing one-time password verifications.
    """
    __tablename__ = 'otp_verification'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=True, index=True)
    otp = db.Column(db.String(10), nullable=True)
    expiry_time = db.Column(db.DateTime, nullable=True)
    verification_status = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<OTPVerification email={self.email} verified={self.verification_status}>"
