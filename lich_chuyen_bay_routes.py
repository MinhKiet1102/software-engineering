from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from datetime import datetime
from models import FlightSchedule, Airport, Rule, IntermediateAirport, Booking, Ticket
from sqlalchemy import or_

lich_chuyen_bay_routes = Blueprint('lich_chuyen_bay_routes', __name__)

from datetime import datetime

@lich_chuyen_bay_routes.route('/lich_chuyen_bay/<flight_id>', methods=['GET', 'POST'])
def lich_chuyen_bay(flight_id):
    username = session['user']['username']
    search_query = request.args.get('search', '')  # Lấy từ khóa tìm kiếm

    try:
        # Chuyển đổi định dạng ngày
        formatted_date = None
        if search_query:
            try:
                formatted_date = datetime.strptime(search_query, '%d-%m-%Y').strftime('%Y-%m-%d')
            except ValueError:
                pass
        
        # Lấy danh sách lịch chuyến bay
        query = FlightSchedule.query.filter_by(flight_id=flight_id)
        if formatted_date:  
            query = query.filter(FlightSchedule.start_date.ilike(f"%{formatted_date}%"))
        else: 
            query = query.filter(
                or_(
                    FlightSchedule.id.ilike(f"%{search_query}%"),
                    FlightSchedule.flight_time.ilike(f"%{search_query}%")
                )
            )
        schedule_flight_list = query.all()

        ticket_classes = db.session.query(Ticket.ticket_class).distinct().all()
        ticket_classes = [tc[0] for tc in ticket_classes]
        role = session.get('user', {}).get('role', 'Customer')

        if role == "Admin":
            return render_template(
                'lich_chuyen_bay_admin.html', 
                schedule_flight_list=schedule_flight_list,
                flight_id=flight_id,
                role=role,
                ticket_classes=ticket_classes,
                username=username,
                search_query=search_query
            )
        elif role == "Staff":
            return render_template(
                'lich_chuyen_bay.html',  
                schedule_flight_list=schedule_flight_list,
                flight_id=flight_id,
                role=role,
                ticket_classes=ticket_classes,
                username=username,
                search_query=search_query
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
    username = session['user']['username']

    # Kiểm tra quyền: chỉ "Người quản trị" hoặc "Nhân viên" được truy cập
    if role not in ['Admin', 'Staff']:
        flash('Bạn không có quyền truy cập!')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))

    if request.method == 'POST':
        # Lấy thông tin từ form
        start_date = request.form.get('start_date')  # Dạng: '2025-01-05T15:33'
        flight_time = request.form.get('flight_time')


        try:
            # Chuyển đổi `start_date` sang định dạng phù hợp
            start_date_formatted = datetime.strptime(start_date, "%Y-%m-%dT%H:%M")  # Đầu vào HTML
            start_date_final = start_date_formatted.strftime("%Y-%m-%d %H:%M:%S")  # Định dạng lưu vào DB

            # Tạo đối tượng FlightSchedule và thêm vào cơ sở dữ liệu
            schedule_flight = FlightSchedule(
                flight_id=flight_id,
                start_date=start_date_final,  # Đảm bảo giá trị có định dạng chuẩn DB
                flight_time=flight_time,
            )
            db.session.add(schedule_flight)
            db.session.commit()

            # Lấy ID của lịch chuyến bay vừa thêm
            last_insert_id = schedule_flight.id

            # Thêm các sân bay trung gian
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
        # Truy vấn danh sách sân bay để hiển thị trong dropdown
        airport_list = Airport.query.all()
        # Truy vấn thông tin quy định
        rule_info = Rule.query.first()
        # Render trang dựa trên quyền
        if role == 'Admin':
            return render_template('them_lich_chuyen_bay_admin.html', 
                                   flight_id=flight_id, 
                                   airport_list=airport_list, 
                                   rule_info=rule_info, 
                                   role=role,
                                   username=username)
        elif role == 'Staff':
            return render_template('them_lich_chuyen_bay.html', 
                                   flight_id=flight_id, 
                                   airport_list=airport_list, 
                                   rule_info=rule_info, 
                                   role=role,
                                   username=username)

    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))


@lich_chuyen_bay_routes.route('/sua_lich_chuyen_bay/<int:flight_schedule_id>', methods=['GET', 'POST'])
def sua_lich_chuyen_bay(flight_schedule_id):
    # try:
        username = session['user']['username']
        # Lấy thông tin lịch chuyến bay hiện tại
        schedule_flight = FlightSchedule.query.get_or_404(flight_schedule_id)
        flight_id = schedule_flight.flight_id

        if request.method == 'POST':
            # Lấy dữ liệu từ form
            schedule_flight.start_date = request.form.get('start_date')
            schedule_flight.flight_time = request.form.get('flight_time')

            # Xóa các sân bay trung gian cũ
            IntermediateAirport.query.filter_by(flight_schedule_id=flight_schedule_id).delete()

            # Thêm các sân bay trung gian mới
            stt_list = request.form.getlist('stt[]')
            intermediate_airports_list = request.form.getlist('intermediate_airports[]')
            time_stop_list = request.form.getlist('stop_time[]')
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
            role=role,
            username=username)
        elif role == 'Staff':
            return render_template('sua_lich_chuyen_bay.html', 
            schedule_flight=schedule_flight,
            intermediate_airports_list=intermediate_airports_list,
            airport_list=airport_list,
            rule_info=rule_info,
            role=role,
            username=username)
    # except Exception as e:
    #     flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))




@lich_chuyen_bay_routes.route('/xoa_lich_chuyen_bay/<int:flight_schedule_id>')
def xoa_lich_chuyen_bay(flight_schedule_id):
    try:
        # Lấy lịch chuyến bay cần xóa
        schedule_flight = FlightSchedule.query.get(flight_schedule_id)
        if not schedule_flight:
            flash('Lịch chuyến bay không tồn tại.')
            return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=0))

        flight_id = schedule_flight.flight.id

        # Kiểm tra nếu có bản ghi đặt vé liên quan
        related_bookings = Booking.query.filter_by(flight_schedule_id=flight_schedule_id).count()
        if related_bookings > 0:
            flash('Không thể xóa lịch chuyến bay vì đã có khách hàng đặt vé.')
            return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))

        # Xóa tất cả các vé liên quan
        Ticket.query.filter_by(flight_schedule_id=flight_schedule_id).delete()

        # Xóa các sân bay trung gian liên quan
        IntermediateAirport.query.filter_by(flight_schedule_id=flight_schedule_id).delete()

        # Xóa lịch chuyến bay
        db.session.delete(schedule_flight)
        db.session.commit()

        flash('Xóa lịch chuyến bay thành công!')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id))

    except Exception as e:
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('lich_chuyen_bay_routes.lich_chuyen_bay', flight_id=flight_id if 'flight_id' in locals() else 0))


