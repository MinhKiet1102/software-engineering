from flask import Blueprint, request, render_template, redirect, url_for, flash, session
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from extensions import db
from models import User
import hashlib  # Để mã hóa mật khẩu

ForgotPassword = Blueprint('ForgotPassword', __name__)

# Email tài khoản gửi OTP
SENDER_EMAIL = "aivivu2016@gmail.com"
SENDER_PASSWORD = "foej pojr trve zagc" 

# Lưu OTP tạm thời
otp_storage = {}


@ForgotPassword.route('/forgot', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'GET':
        return render_template('forgot_password.html')
    
    email = request.form.get('email')

    # Kiểm tra email có tồn tại trong cơ sở dữ liệu
    user = User.query.filter_by(email=email).first()
    if not user:
        flash('Email không tồn tại!', 'error')
        return redirect(url_for('ForgotPassword.forgot_password'))

    # Tạo OTP
    otp = random.randint(100000, 999999)
    otp_storage[email] = otp

    # Gửi email OTP kèm link verify_otp
    try:
        verify_link = request.url_root + url_for('ForgotPassword.verify_otp')  # URL verify OTP
        send_otp_email(email, otp, verify_link)
        flash('Mã OTP đã được gửi đến email của bạn.', 'success')
        session['email'] = email  # Lưu email để xử lý bước tiếp theo
        return redirect(url_for('ForgotPassword.verify_otp'))
    except Exception as e:
        flash('Không thể gửi email. Vui lòng thử lại sau.', 'error')
        return redirect(url_for('ForgotPassword.forgot_password'))


@ForgotPassword.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'GET':
        return render_template('verify_otp.html')
    
    email = session.get('email')
    if not email:
        flash('Phiên làm việc của bạn đã hết hạn!', 'error')
        return redirect(url_for('ForgotPassword.forgot_password'))

    otp = request.form.get('otp')
    if otp_storage.get(email) == int(otp):
        flash('Xác thực OTP thành công!', 'success')
        return redirect(url_for('ForgotPassword.reset_password'))
    else:
        flash('Mã OTP không đúng!', 'error')
        return redirect(url_for('ForgotPassword.verify_otp'))


@ForgotPassword.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    if request.method == 'GET':
        return render_template('reset_password.html')

    email = session.get('email')
    if not email:
        flash('Phiên làm việc của bạn đã hết hạn!', 'error')
        return redirect(url_for('ForgotPassword.forgot_password'))

    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if new_password != confirm_password:
        flash('Mật khẩu xác nhận không khớp!', 'error')
        return redirect(url_for('ForgotPassword.reset_password'))

    # Cập nhật mật khẩu mới vào cơ sở dữ liệu
    hashed_password = hashlib.md5(new_password.encode()).hexdigest()  # Mã hóa mật khẩu
    user = User.query.filter_by(email=email).first()

    if user:
        user.password = hashed_password
        db.session.commit()

        # Xóa OTP đã sử dụng
        otp_storage.pop(email, None)
        session.pop('email', None)

        flash('Mật khẩu của bạn đã được cập nhật thành công!', 'success')
        return redirect(url_for('authentication_routes.index'))  # Điều hướng về trang đăng nhập
    else:
        flash('Không tìm thấy người dùng với email này!', 'error')
        return redirect(url_for('ForgotPassword.forgot_password'))


def send_otp_email(recipient_email, otp, verify_link):
    """Hàm gửi email OTP kèm link xác thực"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email
    msg['Subject'] = 'Mã OTP khôi phục mật khẩu'

    body = f"""
    Xin chào,
    
    Mã OTP của bạn là: {otp}
    Vui lòng nhập mã OTP này tại link bên dưới để khôi phục mật khẩu:
    {verify_link}

    Trân trọng,
    Aivivu
    """
    msg.attach(MIMEText(body, 'plain'))

    # Gửi email qua SMTP
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, recipient_email, msg.as_string())
    server.quit()
