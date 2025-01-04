from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from models import Airport, Flight, User
from extensions import db
import hashlib

authentication_routes = Blueprint('authentication_routes', __name__)

@authentication_routes.route('/')
def index():
    # Xóa thông tin người dùng trong session khi người dùng quay lại trang login
    session.pop('user', None)

    # Tạo session cho người dùng mới (chưa đăng nhập)
    session['user'] = {
        'id': "No", 
        'username': "No",
        'fullname' : "No",
        'email': "No", 
        'phone_number': "No", 
        'password': "No", 
        'role': "Khách hàng"
    }
    return render_template('login.html')

@authentication_routes.route('/dang_nhap', methods=['POST'])
def dang_nhap():
    email = request.form.get('email')
    password = request.form.get('mat_khau')

    # Kiểm tra xác thực người dùng
    user = authenticate_user(email, password)
    
    if user:
        # Lưu thông tin người dùng vào session
        session['user'] = {
            'id': user.id, 
            'username': user.username,  
            'fullname' : user.fullname,
            'email': user.email, 
            'phone_number': user.phone_number, 
            'role': user.role  
        }

        # Dựa trên vai trò của người dùng, điều hướng tới trang tương ứng
        if user.role == 'Admin':
            return redirect(url_for('.trang_admin'))
        elif user.role == 'Staff':
            return redirect(url_for('.trang_nhan_vien'))
        elif user.role == 'Customer':
            return redirect(url_for('.trang_khach_hang'))
    else:
        flash('Email hoặc mật khẩu không đúng!', 'error')
        return redirect(url_for('.index'))

@authentication_routes.route('/trang_admin')
def trang_admin():
    # Kiểm tra quyền truy cập của người dùng
    if 'user' in session and session['user']['role'] == 'Admin':
        role = session['user']['role']
        username = session['user']['username']
        return render_template('trang_admin.html', role=role, username=username)
    else:
        flash('Truy cập bị từ chối. Vui lòng đăng nhập với tư cách Admin.', 'error')
        return redirect(url_for('.dang_nhap'))

@authentication_routes.route('/trang_nhan_vien')
def trang_nhan_vien():
    # Kiểm tra quyền truy cập của người dùng
    if 'user' in session and session['user']['role'] == 'Staff':
        role = session['user']['role']
        username = session['user']['username']
        return render_template('trang_nhan_vien.html', role=role, username=username)
    else:
        flash('Truy cập bị từ chối. Vui lòng đăng nhập với tư cách Nhân viên.', 'error')
        return redirect(url_for('.dang_nhap'))
    
    
@authentication_routes.route('/trang_khach_hang')
def trang_khach_hang():
    # Lấy quyền của người dùng từ session
    role = session.get('user', {}).get('role', 'Customer')
    username = session['user']['username']

    # Lấy danh sách sân bay để hiển thị form tìm kiếm
    airport_departure_list = db.session.query(Airport).all()
    airport_arrival_list = db.session.query(Airport).all()

    return render_template(
        'danh_sach_dat_ve.html',
        role=role,
        airport_departure_list=airport_departure_list,
        airport_arrival_list=airport_arrival_list,
        airport_departure_selected='',  
        airport_arrival_selected='',
        start_date='',
        username=username
    )
def authenticate_user(email, password):
    """Xác thực người dùng dựa trên email và mật khẩu."""
    # Tìm người dùng qua email
    user = User.query.filter_by(email=email).first()

    # Kiểm tra người dùng và so khớp mật khẩu
    if user:
        hashed_password = hashlib.md5(password.encode()).hexdigest()  
        if user.password == hashed_password:  
            return user
    return None