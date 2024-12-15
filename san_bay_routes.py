from flask import Blueprint, render_template, redirect, url_for, flash, session, request
# from db_utils import cursor, db
from extensions import db
from datetime import datetime, timedelta
from models import Airport, Rule
from flask import request, jsonify

san_bay_routes = Blueprint('san_bay_routes', __name__)

@san_bay_routes.route('/danh_sach_san_bay', methods=['GET'])
def danh_sach_san_bay():
    try:
        # Lấy danh sách tất cả sân bay từ cơ sở dữ liệu
        airport_list = Airport.query.all()

        # Kiểm tra quyền hạn người dùng từ session (Admin/User)
        role = session.get('role', 'User')  # Mặc định là 'User' nếu không có role trong session

        # Render template HTML và truyền dữ liệu
        return render_template(
            'danh_sach_san_bay.html',
            airport_list=airport_list,
            role=role
        )
    except Exception as e:
        return f"Lỗi khi lấy danh sách sân bay: {str(e)}", 500
    

@san_bay_routes.route('/them_san_bay', methods=['GET', 'POST'])
def them_san_bay():
    if request.method == 'POST':
        abbreviate_name = request.form['abbreviate_name']
        name = request.form['name']
        location = request.form['location']
        nation = request.form['nation']
        
        try:
            # Lấy quy tắc hiện tại (giả sử chỉ có một bản ghi trong bảng rules)
            rule = Rule.query.first()
            if not rule:
                return "Quy tắc chưa được cấu hình, vui lòng thêm quy tắc trước.", 400
            
            # Kiểm tra số lượng sân bay hiện tại
            current_airport_count = Airport.query.count()
            if current_airport_count >= rule.quantity_airport:
                flash('Số lượng sân bay đã đạt tối đa. Không thể thêm sân bay mới')
                return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
            # Tạo đối tượng Airport mới
            new_airport = Airport(
                abbreviate_name=abbreviate_name,
                name=name,
                location=location,
                nation=nation
            )
            db.session.add(new_airport)
            db.session.commit()
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
        except Exception as e:
            flash('Vượt quá số lượng sân bay trong quy định')
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
    return render_template('them_san_bay.html')


@san_bay_routes.route('/sua_san_bay/<string:airport_id>', methods=['GET', 'POST'])
def sua_san_bay(airport_id):
    airport = Airport.query.filter_by(abbreviate_name=airport_id).first()
    if not airport:
        return "Không tìm thấy sân bay!", 404

    if request.method == 'POST':
        try:
            airport.abbreviate_name = request.form['abbreviate_name']
            airport.name = request.form['name']
            airport.location = request.form['location']
            airport.nation = request.form['nation']
            
            db.session.commit()
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
        except Exception as e:
            db.session.rollback()
            return f"Lỗi: {str(e)}", 400
    
    return render_template('sua_san_bay.html', airport=airport)

@san_bay_routes.route('/xoa_san_bay/<string:airport_id>', methods=['GET', 'POST'])
def xoa_san_bay(airport_id):
    try:
        airport = Airport.query.filter_by(abbreviate_name=airport_id).first()
        if not airport:
            return "Không tìm thấy sân bay!", 404
        
        db.session.delete(airport)
        db.session.commit()
        return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
    except Exception as e:
        db.session.rollback()
        return f"Lỗi: {str(e)}", 400