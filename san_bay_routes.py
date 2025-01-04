from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from datetime import datetime, timedelta
from models import Airport, Rule
from flask import request, jsonify
from flask import flash, redirect, url_for
from sqlalchemy import or_

san_bay_routes = Blueprint('san_bay_routes', __name__)

@san_bay_routes.route('/danh_sach_san_bay', methods=['GET'])
def danh_sach_san_bay():
    try:
        search_query = request.args.get('search', '')  

        airport_list = Airport.query.filter(
            or_(
                Airport.abbreviate_name.ilike(f"%{search_query}%"),  
                Airport.name.ilike(f"%{search_query}%"),            
                Airport.location.ilike(f"%{search_query}%"),         
                Airport.nation.ilike(f"%{search_query}%")           
            )
        ).all()

        # Kiểm tra quyền hạn người dùng từ session
        role = session.get('role', 'Admin')
        username = session['user']['username']

        return render_template(
            'danh_sach_san_bay.html',
            airport_list=airport_list,
            role=role,
            username=username,
            search_query=search_query  
        )
    except Exception as e:
        return f"Lỗi khi lấy danh sách sân bay: {str(e)}", 500

    

@san_bay_routes.route('/them_san_bay', methods=['GET', 'POST'])
def them_san_bay():
    username = session['user']['username']

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
            
            # Kiểm tra xem sân bay đã tồn tại chưa dựa trên mã hoặc tên
            existing_airport_by_abbr = Airport.query.filter_by(abbreviate_name=abbreviate_name).first()
            existing_airport_by_name = Airport.query.filter_by(name=name).first()

            if existing_airport_by_abbr:
                flash('Sân bay với mã viết tắt này đã tồn tại. Vui lòng chọn mã khác.')
                return redirect(url_for('san_bay_routes.them_san_bay'))

            if existing_airport_by_name:
                flash('Sân bay với tên này đã tồn tại. Vui lòng chọn tên khác.')
                return redirect(url_for('san_bay_routes.them_san_bay'))

            # Tạo đối tượng Airport mới
            new_airport = Airport(
                abbreviate_name=abbreviate_name,
                name=name,
                location=location,
                nation=nation
            )
            db.session.add(new_airport)
            db.session.commit()
            flash('Thêm sân bay thành công!')
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
        except Exception as e:
            flash('Vượt quá số lượng sân bay trong quy định')
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
    role = session.get('role', 'Admin')
    return render_template('them_san_bay.html',role=role,username=username)


@san_bay_routes.route('/sua_san_bay/<string:airport_id>', methods=['GET', 'POST'])
def sua_san_bay(airport_id):
    username = session['user']['username']
    airport = Airport.query.filter_by(abbreviate_name=airport_id).first()
    if not airport:
        flash("Không tìm thấy sân bay!")
        return redirect(url_for('san_bay_routes.danh_sach_san_bay'))

    if request.method == 'POST':
        try:
            new_abbreviate_name = request.form['abbreviate_name']
            new_name = request.form['name']
            new_location = request.form['location']
            new_nation = request.form['nation']

            # Kiểm tra trùng lặp mã viết tắt
            if new_abbreviate_name != airport.abbreviate_name:
                existing_airport_by_abbr = Airport.query.filter_by(abbreviate_name=new_abbreviate_name).first()
                if existing_airport_by_abbr:
                    flash("Mã viết tắt này đã tồn tại. Vui lòng chọn mã khác.")
                    return redirect(url_for('san_bay_routes.sua_san_bay', airport_id=airport_id))

            # Kiểm tra trùng lặp tên sân bay
            if new_name != airport.name:
                existing_airport_by_name = Airport.query.filter_by(name=new_name).first()
                if existing_airport_by_name:
                    flash("Tên sân bay này đã tồn tại. Vui lòng chọn tên khác.")
                    return redirect(url_for('san_bay_routes.sua_san_bay', airport_id=airport_id))

            # Cập nhật thông tin sân bay
            airport.abbreviate_name = new_abbreviate_name
            airport.name = new_name
            airport.location = new_location
            airport.nation = new_nation
            
            db.session.commit()
            flash("Cập nhật sân bay thành công!")
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
        except Exception as e:
            db.session.rollback()
            flash(f"Lỗi: {str(e)}")
            return redirect(url_for('san_bay_routes.sua_san_bay', airport_id=airport_id))

    role = session.get('role', 'Admin')
    return render_template('sua_san_bay.html', airport=airport, role=role, username=username)


@san_bay_routes.route('/xoa_san_bay/<string:airport_id>', methods=['GET', 'POST'])
def xoa_san_bay(airport_id):
    try:
        # Tìm sân bay cần xóa
        airport = Airport.query.filter_by(abbreviate_name=airport_id).first()
        if not airport:
            flash("Không tìm thấy sân bay!", "danger")
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))

        # Kiểm tra nếu sân bay có chuyến bay khởi hành hoặc đến
        if airport.departure_flights or airport.arrival_flights:
            # Duyệt qua các chuyến bay để kiểm tra lịch chuyến bay
            for flight in airport.departure_flights + airport.arrival_flights:
                if flight.flight_schedules:
                    flash("Không thể xóa sân bay vì đã có chuyến bay hoặc lịch chuyến bay liên quan!", "warning")
                    return redirect(url_for('san_bay_routes.danh_sach_san_bay'))


        # Kiểm tra nếu sân bay đã trở thành sân bay trung gian
        if airport.intermediate_airports:
            flash("Không thể xóa sân bay vì nó đã trở thành sân bay trung gian trong các chuyến bay.", "warning")
            return redirect(url_for('san_bay_routes.danh_sach_san_bay'))

        # Nếu không có chuyến bay hoặc lịch chuyến bay, cho phép xóa
        db.session.delete(airport)
        db.session.commit()
        flash("Xóa sân bay thành công!", "success")
        return redirect(url_for('san_bay_routes.danh_sach_san_bay'))

    except Exception as e:
        db.session.rollback()
        flash(f"Lỗi: {str(e)}", "danger")
        return redirect(url_for('san_bay_routes.danh_sach_san_bay'))
