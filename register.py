from flask import Blueprint, request, jsonify, render_template
import hashlib
from extensions import db
from models import User

# Khởi tạo Blueprint cho register
register_bp = Blueprint('register', __name__)

# Route đăng ký
@register_bp.route('/register', methods=['GET'])
def register_page():
    return render_template('register.html')

@register_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    fullname = data.get('fullname')
    email = data.get('email')
    phone_number = data.get('phone_number') 
    password = data.get('password')

    # Kiểm tra giá trị phone_number
    if not phone_number or not phone_number.isdigit():
        return jsonify({'success': False, 'message': 'Số điện thoại không hợp lệ!'})

    # Kiểm tra email đã tồn tại
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'success': False, 'message': 'Email này đã được sử dụng!'})

    # Mã hóa mật khẩu
    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # Thêm người dùng mới vào cơ sở dữ liệu
    new_user = User(
        username=username,
        fullname=fullname,
        email=email,
        phone_number=phone_number,
        password=hashed_password,
        role='Customer'
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'success': True, 'message': 'Đăng ký thành công!'})

