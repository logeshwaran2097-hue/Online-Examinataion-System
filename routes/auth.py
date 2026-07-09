import sys
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from database import db, bcrypt
from models import User, OTPVerification, ActivityLog, Notification
from utils.otp import generate_and_save_otp, verify_otp
from utils.mail import send_otp_email
from email_validator import validate_email, EmailNotValidError

auth_bp = Blueprint('auth', __name__)

def log_activity(user_id, role, activity):
    """
    Helper function to record security and user activities to the activity_logs table.
    """
    try:
        log_entry = ActivityLog(
            user_id=user_id,
            user_role=role,
            activity=activity,
            ip_address=request.remote_addr or 'unknown',
            browser=request.user_agent.string[:255] or 'unknown'
        )
        db.session.add(log_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        # Fallback logging to stdout/stderr in case database write fails
        print(f"Error writing to activity_logs: {e}", file=sys.stderr)

def seed_default_student():
    """
    Ensures at least one verified student account exists in the database.
    """
    try:
        if not User.query.filter_by(email='student@eduexam.com').first():
            hashed_pw = bcrypt.generate_password_hash('studentpassword').decode('utf-8')
            default_student = User(
                full_name='Demo Student',
                email='student@eduexam.com',
                password=hashed_pw,
                is_verified=True,
                status=True
            )
            db.session.add(default_student)
            db.session.commit()
            print("INFO: Seeded default student account (student@eduexam.com / studentpassword)")
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding default student: {e}")

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.student_dashboard'))

    if request.method == 'POST':
        full_name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        phone_number = request.form.get('phone', '').strip()
        department = request.form.get('department', '').strip()
        year_of_study_raw = request.form.get('year_of_study', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        # Input Validation
        if not (full_name and email and password and confirm_password):
            flash('Please fill in all required fields.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        # Validate Email Format
        try:
            valid_email_info = validate_email(email)
            email = valid_email_info.normalized
        except EmailNotValidError as e:
            flash(f"Invalid email address: {e}", 'danger')
            return render_template('auth/register.html')

        # Validate Year of Study
        try:
            year_of_study = int(year_of_study_raw)
            if not (1 <= year_of_study <= 8):
                raise ValueError()
        except ValueError:
            flash('Year of study must be a number between 1 and 8.', 'danger')
            return render_template('auth/register.html')

        # Duplicate Checks
        if phone_number:
            existing_phone_user = User.query.filter_by(phone_number=phone_number).first()
            if existing_phone_user:
                if existing_phone_user.is_verified:
                    flash('An account with this phone number already exists.', 'danger')
                    return render_template('auth/register.html')
                elif existing_phone_user.email != email:
                    # Belonging to another unverified user: free up the phone number by setting it to None
                    existing_phone_user.phone_number = None
                    db.session.commit()

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            if existing_user.is_verified:
                flash('An account with this email address already exists.', 'danger')
                return render_template('auth/register.html')
            else:
                # User exists but is not verified: update details and send a new OTP
                try:
                    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                    existing_user.full_name = full_name
                    existing_user.phone_number = phone_number if phone_number else None
                    existing_user.department = department if department else None
                    existing_user.year_of_study = year_of_study
                    existing_user.password = hashed_pw
                    db.session.commit()

                    otp_code = generate_and_save_otp(email)
                    email_sent = send_otp_email(email, otp_code, purpose="verification")
                    session['verification_email'] = email
                    
                    if email_sent:
                        flash('Welcome back! A new OTP has been sent to your email to complete verification.', 'info')
                    else:
                        flash(f'Welcome back! Email failed. Your verification OTP is: {otp_code}', 'warning')
                    return redirect(url_for('auth.otp'))
                except Exception as e:
                    db.session.rollback()
                    flash(f"An error occurred during registration update: {e}", 'danger')
                    return render_template('auth/register.html')

        try:
            # Hash password and create unverified user
            hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(
                full_name=full_name,
                email=email,
                phone_number=phone_number if phone_number else None,
                department=department if department else None,
                year_of_study=year_of_study,
                password=hashed_pw,
                is_verified=False
            )
            db.session.add(new_user)
            db.session.commit()

            # Generate and Send OTP
            otp_code = generate_and_save_otp(email)
            email_sent = send_otp_email(email, otp_code, purpose="verification")
            
            # Store email in session to process verification step
            session['verification_email'] = email
            
            log_activity(new_user.id, 'student', 'Registered account (pending email verification)')
            
            if email_sent:
                flash('Registration successful! A 6-digit OTP has been sent to your email.', 'info')
            else:
                # Mail not configured — show OTP directly on screen for development
                flash(f'Registration successful! Email delivery failed. Your OTP is: {otp_code}  (Use this to verify)', 'warning')
            return redirect(url_for('auth.otp'))

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred during registration: {e}", 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')

@auth_bp.route('/otp', methods=['GET', 'POST'])
def otp():
    # Make sure we have a user to verify
    email = session.get('verification_email')
    if not email:
        flash('Session expired. Please register again.', 'danger')
        return redirect(url_for('auth.register'))

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        
        if not otp_code:
            flash('Please enter the verification code.', 'danger')
            return render_template('auth/otp.html')

        if verify_otp(email, otp_code):
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_verified = True
                db.session.commit()
                
                # Automatically log in the verified user
                login_user(user)
                session.pop('verification_email', None)
                
                log_activity(user.id, 'student', 'Completed email verification & logged in')
                
                # Insert welcome notification
                welcome_notif = Notification(
                    user_id=user.id,
                    title="Welcome!",
                    message="Your examination account is successfully verified and activated. Good luck!",
                    notification_type="system"
                )
                db.session.add(welcome_notif)
                db.session.commit()
                
                flash('Your account has been verified and activated successfully!', 'success')
                return redirect(url_for('dashboard.student_dashboard'))
            else:
                flash('User not found.', 'danger')
                return redirect(url_for('auth.register'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
            return render_template('auth/otp.html')

    return render_template('auth/otp.html')

@auth_bp.route('/resend-otp', methods=['POST'])
def resend_otp():
    # Determine which flow triggered resend
    email = session.get('verification_email') or session.get('reset_email')
    
    if not email:
        flash('Session expired. Please try your request again.', 'danger')
        return redirect(url_for('auth.register'))

    try:
        otp_code = generate_and_save_otp(email)
        purpose = "reset" if session.get('reset_email') else "verification"
        email_sent = send_otp_email(email, otp_code, purpose=purpose)
        if email_sent:
            flash('A new OTP verification code has been sent to your email.', 'success')
        else:
            flash(f'Email delivery failed. Your new OTP is: {otp_code}', 'warning')
    except Exception as e:
        flash(f"Failed to resend OTP: {e}", 'danger')

    if session.get('reset_email'):
        return redirect(url_for('auth.reset_password'))
    return redirect(url_for('auth.otp'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    seed_default_student()
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.student_dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        if not (email and password):
            flash('Please enter both email and password.', 'danger')
            return render_template('auth/login.html')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('Invalid email or password.', 'danger')
            return render_template('auth/login.html')

        # Check Account Status
        if not user.status:
            flash('This account is disabled. Please contact support.', 'danger')
            return render_template('auth/login.html')

        # Check Lockout Status
        if user.lockout_until and user.lockout_until > datetime.utcnow():
            remaining = int((user.lockout_until - datetime.utcnow()).total_seconds() / 60)
            flash(f"Too many failed login attempts. Account locked. Try again in {max(1, remaining)} minutes.", 'danger')
            return render_template('auth/login.html')

        # Verify Password
        if bcrypt.check_password_hash(user.password, password):
            # Reset brute-force counter
            user.failed_login_attempts = 0
            user.lockout_until = None
            db.session.commit()

            # Ensure email verification has occurred
            if not user.is_verified:
                session['verification_email'] = user.email
                # Generate new verification OTP
                otp_code = generate_and_save_otp(user.email)
                email_sent = send_otp_email(user.email, otp_code, purpose="verification")
                
                if email_sent:
                    flash('Your email is not verified yet. We sent a new verification code to your email.', 'info')
                else:
                    flash(f'Your email is not verified. Email failed. Your OTP is: {otp_code}', 'warning')
                return redirect(url_for('auth.otp'))

            # Setup login session
            login_user(user, remember=remember)
            log_activity(user.id, 'student', 'Successful login')
            
            flash(f"Welcome back, {user.full_name}!", 'success')
            return redirect(url_for('dashboard.student_dashboard'))
        else:
            # Increment failed attempts
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 5:
                user.lockout_until = datetime.utcnow() + timedelta(minutes=15)
                log_activity(user.id, 'student', 'Account locked due to 5 consecutive login failures')
                flash('Too many failed login attempts. Your account has been locked for 15 minutes.', 'danger')
            else:
                db.session.commit()
                log_activity(user.id, 'student', f"Failed login attempt ({user.failed_login_attempts}/5)")
                flash('Invalid email or password.', 'danger')
                
            return render_template('auth/login.html')

    return render_template('auth/login.html')

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        
        if not email:
            flash('Please enter your email address.', 'danger')
            return render_template('auth/forgot_password.html')

        user = User.query.filter_by(email=email).first()

        if user:
            if not user.status:
                flash('This account is disabled.', 'danger')
                return render_template('auth/forgot_password.html')

            try:
                # Generate reset OTP
                otp_code = generate_and_save_otp(email)
                email_sent = send_otp_email(email, otp_code, purpose="reset")
                session['reset_email'] = email
                
                log_activity(user.id, 'student', 'Requested password reset OTP')
                
                if email_sent:
                    flash('A password reset OTP has been sent to your email address.', 'success')
                else:
                    flash(f'Email delivery failed. Your reset OTP is: {otp_code}', 'warning')
                return redirect(url_for('auth.reset_password'))
            except Exception as e:
                flash(f"An error occurred while generating OTP: {e}", 'danger')
                return render_template('auth/forgot_password.html')
        else:
            # Prevent user enumeration by displaying a generic success message
            flash('If the email is registered in our system, a password reset OTP was sent.', 'success')
            return redirect(url_for('auth.reset_password'))

    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    query_email = request.args.get('email', '').strip()
    query_code = request.args.get('code', '').strip()

    if query_email and query_code:
        session['reset_email'] = query_email

    # Retrieve email from session
    email = session.get('reset_email')
    if not email:
        flash('Session expired or access denied. Please initiate password recovery again.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    code_val = query_code or request.form.get('otp_code', '').strip()

    if request.method == 'POST':
        otp_code = request.form.get('otp_code', '').strip()
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')

        if not (otp_code and password and confirm_password):
            flash('Please fill in all fields.', 'danger')
            return render_template('auth/reset_password.html', code=code_val)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/reset_password.html', code=code_val)

        # Verify OTP
        if verify_otp(email, otp_code):
            user = User.query.filter_by(email=email).first()
            if user:
                try:
                    # Update Password and reset lockout status
                    hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
                    user.password = hashed_pw
                    user.failed_login_attempts = 0
                    user.lockout_until = None
                    db.session.commit()

                    session.pop('reset_email', None)
                    
                    log_activity(user.id, 'student', 'Reset password successfully')
                    
                    # Notify user
                    notif = Notification(
                        user_id=user.id,
                        title="Password Changed",
                        message="Your password was reset successfully. If you did not make this change, contact support immediately.",
                        notification_type="security"
                    )
                    db.session.add(notif)
                    db.session.commit()

                    flash('Your password has been reset successfully! Please log in.', 'success')
                    return redirect(url_for('auth.login'))
                except Exception as e:
                    db.session.rollback()
                    flash(f"An error occurred while updating the password: {e}", 'danger')
                    return render_template('auth/reset_password.html', code=code_val)
            else:
                flash('User account not found.', 'danger')
                return redirect(url_for('auth.forgot_password'))
        else:
            flash('Invalid or expired OTP. Please try again.', 'danger')
            return render_template('auth/reset_password.html', code=code_val)

    return render_template('auth/reset_password.html', code=code_val)

@auth_bp.route('/logout')
@login_required
def logout():
    user_id = current_user.id
    logout_user()
    
    # Clear sessions and cookies
    session.clear()
    
    log_activity(user_id, 'student', 'Logged out')
    
    flash('You have logged out successfully.', 'success')
    return redirect(url_for('auth.login'))
