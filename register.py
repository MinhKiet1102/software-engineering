from flask import Blueprint, request, jsonify, render_template, session, flash, redirect, url_for
import hashlib
from extensions import db
from models import User

register_bp = Blueprint('register', __name__)

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

    hashed_password = hashlib.md5(password.encode()).hexdigest()

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


@register_bp.route('/register_staff_admin', methods=['POST'])
def register_staff_admin():
    data = request.get_json()
    username = data.get('username')
    fullname = data.get('fullname')
    email = data.get('email')
    phone_number = data.get('phone_number') 
    password = data.get('password')
    role = data.get('role')  # Lấy role từ dữ liệu form

    # Kiểm tra quyền truy cập (chỉ Admin mới được thực hiện)
    if session.get('user', {}).get('role') != 'Admin':
        return jsonify({'success': False, 'message': 'Bạn không có quyền thực hiện thao tác này!'})

    # Kiểm tra giá trị phone_number
    if not phone_number or not phone_number.isdigit():
        return jsonify({'success': False, 'message': 'Số điện thoại không hợp lệ!'})

    # Kiểm tra email đã tồn tại
    user = User.query.filter_by(email=email).first()
    if user:
        return jsonify({'success': False, 'message': 'Email này đã được sử dụng!'})

    # Kiểm tra role hợp lệ
    valid_roles = ['Staff', 'Admin']
    if role not in valid_roles:
        return jsonify({'success': False, 'message': 'Vai trò không hợp lệ!'})

    hashed_password = hashlib.md5(password.encode()).hexdigest()

    # Thêm người dùng mới vào cơ sở dữ liệu
    new_user = User(
        username=username,
        fullname=fullname,
        email=email,
        phone_number=phone_number,
        password=hashed_password,
        role=role
    )
    
    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        'success': True, 
        'message': f'Tạo tài khoản {role} thành công!'
    })

@register_bp.route('/them_tai_khoan_admin', methods=['GET'])
def them_tai_khoan_admin():
    role = session.get('user', {}).get('role', 'Admin')
    username = session['user']['username']
    return render_template('them_tai_khoan_admin.html', role=role, username=username)

