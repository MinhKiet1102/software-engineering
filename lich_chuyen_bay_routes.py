from flask import Blueprint, render_template, redirect, url_for, flash, session, request
# from db_utils import cursor, db
from extensions import db
from datetime import datetime
from models import FlightSchedule, Airport, Rule, IntermediateAirport

lich_chuyen_bay_routes = Blueprint('lich_chuyen_bay_routes', __name__)


@lich_chuyen_bay_routes.route('/lich_chuyen_bay/<flight_id>', methods=['GET', 'POST'])
def lich_chuyen_bay(flight_id):
    try:
        schedule_flight_list = FlightSchedule.query.filter_by(flight_id=flight_id).all()
        
        role = session.get('user', {}).get('role', 'Customer')

        if role == "Admin":
            return render_template(
                'lich_chuyen_bay_admin.html', 
                schedule_flight_list=schedule_flight_list,
                flight_id=flight_id,
                role=role
            )
        elif role == "Staff":
            return render_template(
                'lich_chuyen_bay.html',  # Hiển thị giao diện nhân viên
                schedule_flight_list=schedule_flight_list,
                flight_id=flight_id,
                role=role
            )
        else:
            flash('Bạn không có quyền truy cập!')
            return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))

    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))



@lich_chuyen_bay_routes.route('/them_lich_chuyen_bay/<flight_id>', methods=['GET', 'POST'])
def them_lich_chuyen_bay(flight_id):
    role = session.get('user', {}).get('role', 'Customer')

    if role not in ['Admin', 'Staff']:
        flash('Bạn không có quyền truy cập!')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))

    if request.method == 'POST':
        # Lấy thông tin từ form
        start_date = request.form.get('start_date')
        flight_time = request.form.get('flight_time')
        quantity_class_1 = request.form.get('quantity_class1')
        quantity_class_2 = request.form.get('quantity_class2')

        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            flight_time = datetime.strptime(flight_time, '%Y-%m-%d %H:%M:%S')

            rule_info = Rule.query.first()
            min_flight_duration = rule_info.min_flight_time

            flight_duration = (flight_time - start_date).total_seconds() / 60 

            if flight_duration < min_flight_duration:
                flash(f"Thời gian bay tối thiểu là {min_flight_duration} phút. Vui lòng điều chỉnh thời gian bay.")
                return redirect(url_for('lich_chuyen_bay_routes.them_lich_chuyen_bay', flight_id=flight_id))

            # Tạo đối tượng LichChuyenBay và thêm vào cơ sở dữ liệu
            schedule_flight = FlightSchedule(
                flight_id=flight_id,
                start_date=start_date,
                flight_time=flight_time,
                quantity_class1=quantity_class_1,
                quantity_class2=quantity_class_2
            )
            db.session.add(schedule_flight)
            db.session.commit()

            last_insert_id = schedule_flight.id

            stt_list = request.form.getlist('stt[]')
            intermediate_airports_list = request.form.getlist('intermediate_airports[]')
            time_stop_list = request.form.getlist('stop_time[]')
            note_list = request.form.getlist('note[]')

            for stt, airport, time, note in zip(stt_list, intermediate_airports_list, time_stop_list, note_list):
                intermediate_airports = IntermediateAirport(
                    flight_schedule_id=last_insert_id,
                    airport_id=airport,
                    stop_time=time,
                    note=note
                )
                db.session.add(intermediate_airports)

            db.session.commit()
            flash('Thêm lịch chuyến bay thành công!')
            return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))

        except Exception as e:
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}')

    try:
        airport_list = Airport.query.all()
        rule_info = Rule.query.first()

        if role == 'Admin':
            return render_template('them_lich_chuyen_bay_admin.html', 
                                   flight_id=flight_id, 
                                   airport_list=airport_list, 
                                   rule_info=rule_info, 
                                   role=role)
        elif role == 'Staff':
            return render_template('them_lich_chuyen_bay.html', 
                                   flight_id=flight_id, 
                                   airport_list=airport_list, 
                                   rule_info=rule_info, 
                                   role=role)

    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))


@lich_chuyen_bay_routes.route('/sua_lich_chuyen_bay/<int:flight_schedule_id>', methods=['GET', 'POST'])
def sua_lich_chuyen_bay(flight_schedule_id):
    # try:
        # Lấy thông tin lịch chuyến bay hiện tại
        schedule_flight = FlightSchedule.query.get_or_404(flight_schedule_id)
        flight_id = schedule_flight.flight_id

        if request.method == 'POST':
            # Lấy dữ liệu từ form
            schedule_flight.start_date = request.form.get('start_date')
            schedule_flight.flight_time = request.form.get('flight_time')
            schedule_flight.quantity_class1 = request.form.get('quantity_class_1')
            schedule_flight.quantity_class2 = request.form.get('quantity_class_2')

            # Xóa các sân bay trung gian cũ
            IntermediateAirport.query.filter_by(flight_schedule_id=flight_schedule_id).delete()

            # Thêm các sân bay trung gian mới
            stt_list = request.form.getlist('stt[]')
            intermediate_airports_list = request.form.getlist('intermediate_airports[]')
            time_stop_list = request.form.getlist('time_stop[]')
            note_list = request.form.getlist('note[]')

            for stt, airport, time, note in zip(stt_list, intermediate_airports_list, time_stop_list, note_list):
                intermediate_airports = IntermediateAirport(
                    flight_schedule_id=flight_schedule_id,
                    airport_id=airport,
                    stop_time=time,
                    note=note
                )
                db.session.add(intermediate_airports)

            db.session.commit()
            role = session.get('user', {}).get('role', 'Customer')
            flash('Cập nhật lịch chuyến bay thành công!')
            if role == "Admin":
                return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))
            elif role == "Staff":
                return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))

        # Truy vấn danh sách sân bay và quy định
        airport_list = Airport.query.all()
        intermediate_airports_list = IntermediateAirport.query.filter_by(flight_schedule_id=flight_schedule_id).all()
        rule_info = Rule.query.first()
        role = session.get('user', {}).get('role', 'Customer')

        if role == 'Admin':
            return render_template('sua_lich_chuyen_bay_admin.html', 
            schedule_flight=schedule_flight,
            intermediate_airports_list=intermediate_airports_list,
            airport_list=airport_list,
            rule_info=rule_info,
            role=role)
        elif role == 'Staff':
            return render_template('sua_lich_chuyen_bay.html', 
            schedule_flight=schedule_flight,
            intermediate_airports_list=intermediate_airports_list,
            airport_list=airport_list,
            rule_info=rule_info,
            role=role)
    # except Exception as e:
    #     flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))




@lich_chuyen_bay_routes.route('/xoa_lich_chuyen_bay/<int:flight_schedule_id>')
def xoa_lich_chuyen_bay(flight_schedule_id):    
    try:
        # Lấy thông tin lịch chuyến bay
        schedule_flight = FlightSchedule.query.get_or_404(flight_schedule_id)
        flight_id = schedule_flight.id

        # Xóa lịch chuyến bay và các sân bay trung gian liên quan
        IntermediateAirport.query.filter_by(flight_schedule_id=flight_schedule_id).delete()
        db.session.delete(schedule_flight)
        db.session.commit()

        flash('Xóa lịch chuyến bay thành công!')
    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}')

    return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))


