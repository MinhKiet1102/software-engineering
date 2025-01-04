from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from models import Flight, Airport, Ticket, FlightSchedule, Booking, IntermediateAirport
from sqlalchemy.orm import joinedload
from sqlalchemy import or_


chuyen_bay_routes = Blueprint('chuyen_bay_routes', __name__)


@chuyen_bay_routes.route('/them_chuyen_bay_admin', methods=['GET', 'POST'])
def them_chuyen_bay_admin():
    if request.method == 'GET':
        try:
            username = session['user']['username']
            # Lấy danh sách sân bay từ cơ sở dữ liệu
            airport_list = Airport.query.all()
            role = session.get('user', {}).get('role', 'Admin')
            return render_template('them_chuyen_bay.html', airport_list=airport_list, role=role, username=username)
        except Exception as e:
            flash(f'Có lỗi xảy ra khi tải danh sách sân bay: {str(e)}')
            return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

    elif request.method == 'POST':
        # Lấy thông tin từ form
        flight_id = request.form.get('flight_id')
        airport_arrival = request.form.get('airport_arrival')
        airport_departure = request.form.get('airport_departure')
        start_location = request.form.get('start_location')
        destination = request.form.get('destination')

        # Kiểm tra xem mã chuyến bay đã tồn tại chưa
        existing_flight = Flight.query.filter_by(id=flight_id).first()
        if existing_flight:
            flash('Mã chuyến bay đã tồn tại. Vui lòng chọn mã khác.')
            return redirect(url_for('chuyen_bay_routes.them_chuyen_bay_admin'))

        # Kiểm tra xem chuyến bay có bị trùng không
        duplicate_flight = Flight.query.filter_by(
            destination_id=airport_arrival,
            start_location_id=airport_departure,
            start_location=start_location,
            destination=destination
        ).first()
        if duplicate_flight:
            flash('Chuyến bay này đã tồn tại. Vui lòng kiểm tra lại thông tin.')
            return redirect(url_for('chuyen_bay_routes.them_chuyen_bay_admin'))

        # Thêm chuyến bay mới
        flight = Flight(
            id=flight_id,
            destination_id=airport_arrival,
            start_location_id=airport_departure,
            start_location=start_location,
            destination=destination
        )
        db.session.add(flight)
        db.session.commit()
        flash('Thêm chuyến bay thành công!')
        return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

    role = session.get('user', {}).get('role', 'Customer')
    return render_template('them_chuyen_bay.html', role=role, username=username)


@chuyen_bay_routes.route('/sua_chuyen_bay_admin/<flight_id>', methods=['GET', 'POST'])
def sua_chuyen_bay_admin(flight_id):
    username = session['user']['username']
    # Lấy thông tin chuyến bay từ cơ sở dữ liệu
    flight = Flight.query.filter_by(id=flight_id).first()

    if flight:
        airport_list = Airport.query.all()
        role = session.get('user', {}).get('role', 'Customer')
    
        if request.method == 'POST':
            airport_departure_new = request.form.get('airport_departure')
            airport_arrival_new = request.form.get('airport_arrival')
            destination_new = request.form.get('destination')
            start_location_new = request.form.get('start_location')

            try:
                # Kiểm tra trùng lặp chuyến bay
                duplicate_flight = Flight.query.filter_by(
                    destination_id=airport_arrival_new,
                    start_location_id=airport_departure_new,
                    start_location=start_location_new,
                    destination=destination_new
                ).first()

                # Nếu có chuyến bay trùng lặp và không phải là chính nó
                if duplicate_flight and duplicate_flight.id != flight_id:
                    flash('Chuyến bay này đã tồn tại. Vui lòng kiểm tra lại thông tin.')
                    return redirect(url_for('chuyen_bay_routes.sua_chuyen_bay_admin', flight_id=flight_id))

                # Cập nhật thông tin chuyến bay
                flight.destination_id = airport_arrival_new
                flight.start_location_id = airport_departure_new
                flight.start_location = start_location_new
                flight.destination = destination_new

                # Lưu thay đổi vào cơ sở dữ liệu
                db.session.commit()

                flash('Cập nhật chuyến bay thành công!')
                return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

            except Exception as e:
                # Rollback nếu có lỗi
                db.session.rollback()
                flash(f'Có lỗi xảy ra: {str(e)}')
                return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))
        return render_template('sua_chuyen_bay.html', flight=flight, airport_list=airport_list, role=role, username=username)
    
    flash('Chuyến bay không tồn tại!')
    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

@chuyen_bay_routes.route('/xoa_chuyen_bay_admin/<flight_id>')
def xoa_chuyen_bay_admin(flight_id):
    try:
        # Lấy chuyến bay cần xóa
        flight = Flight.query.filter_by(id=flight_id).first()
        if not flight:
            flash('Chuyến bay không tồn tại!', 'danger')
            return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))


        # Kiểm tra lịch chuyến bay
        flight_schedules = FlightSchedule.query.filter_by(flight_id=flight_id).all()
        if flight_schedules:
            for schedule in flight_schedules:

                # Kiểm tra xem lịch chuyến bay có đơn đặt vé không
                bookings = Booking.query.filter_by(flight_schedule_id=schedule.id).all()
                if bookings:
                    flash(f'Chuyến bay này có lịch chuyến bay đã có khách hàng đặt vé, không thể xóa!', 'warning')
                    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

                # Xóa sân bay trung gian liên quan
                IntermediateAirport.query.filter_by(flight_schedule_id=schedule.id).delete()

                # Xóa vé liên quan
                Ticket.query.filter_by(flight_schedule_id=schedule.id).delete()

                # Xóa lịch chuyến bay
                flash(f'Xóa lịch chuyến bay thành công!', 'success')
                db.session.delete(schedule)

        # Xóa chuyến bay
        flash(f'Xóa chuyến bay {flight_id} thành công!', 'success')
        db.session.delete(flight)
        db.session.commit()
    except Exception as e:
        # Rollback nếu có lỗi
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}', 'danger')

    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))


@chuyen_bay_routes.route('/danh_sach_chuyen_bay_admin')
def danh_sach_chuyen_bay_admin():
    username = session['user']['username']
    search_query = request.args.get('search', '')  # Lấy từ khóa tìm kiếm
    role = session.get('user', {}).get('role', 'Customer')

    query = Flight.query
    if search_query:
        query = query.filter(
            or_(
                Flight.id.ilike(f"%{search_query}%"),  # Tìm theo mã chuyến bay
                Flight.airport_departure.has(Airport.name.ilike(f"%{search_query}%")),  # Tìm theo sân bay đi
                Flight.airport_arrival.has(Airport.name.ilike(f"%{search_query}%"))  # Tìm theo sân bay đến
            )
        )
    flight_list = query.all()

    return render_template(
        'danh_sach_chuyen_bay_admin.html',
        flight_list=flight_list,
        role=role,
        username=username,
        search_query=search_query
        )
   
@chuyen_bay_routes.route('/danh_sach_chuyen_bay')
def danh_sach_chuyen_bay():
    # try:
    username = session['user']['username']
    # Lấy danh sách chuyến bay từ cơ sở dữ liệu
    flight_list = Flight.query.all()
    if not flight_list:
        flash('Không có chuyến bay nào để hiển thị.')
        return render_template('danh_sach_chuyen_bay.html', flight_list=flight_list, role=role, username=username)

    role = session.get('user', {}).get('role', 'Customer')
    return render_template('danh_sach_chuyen_bay.html', flight_list=flight_list, role=role, username=username)



