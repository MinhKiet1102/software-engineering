from flask import Blueprint, render_template, redirect, url_for, flash, session, request
# from db_utils import cursor, db
from extensions import db
from models import Flight, Airport, Ticket, FlightSchedule
from sqlalchemy.orm import joinedload

chuyen_bay_routes = Blueprint('chuyen_bay_routes', __name__)


@chuyen_bay_routes.route('/them_chuyen_bay_admin', methods=['GET', 'POST'])
def them_chuyen_bay_admin():
    if request.method == 'GET':
        try:
            # Lấy danh sách sân bay từ cơ sở dữ liệu
            airport_list = Airport.query.all()
            role = session.get('user', {}).get('role', 'Admin')
            return render_template('them_chuyen_bay.html', airport_list=airport_list, role=role)
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
    return render_template('them_chuyen_bay.html', role=role)


@chuyen_bay_routes.route('/sua_chuyen_bay_admin/<flight_id>', methods=['GET', 'POST'])
def sua_chuyen_bay_admin(flight_id):
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
                # Lấy chuyến bay cần sửa
                flight = Flight.query.filter_by(id=flight_id).first()

                if not flight:
                    flash('Chuyến bay không tồn tại!')
                    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

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
        return render_template('sua_chuyen_bay.html', flight=flight, airport_list=airport_list, role=role)
    
    return render_template('sua_chuyen_bay.html')

@chuyen_bay_routes.route('/xoa_chuyen_bay_admin/<flight_id>')
def xoa_chuyen_bay_admin(flight_id):
    try:
        # Lấy chuyến bay cần xóa
        FlightSchedule.query.filter_by(flight_id=flight_id).delete()
        Ticket.query.filter_by(flight_id=flight_id).delete()

        flight = Flight.query.filter_by(id=flight_id).first()

        if not flight:
            flash('Chuyến bay không tồn tại!')
            return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

        # Xóa chuyến bay
        db.session.delete(flight)
        db.session.commit()

        flash('Xóa chuyến bay thành công!')
    except Exception as e:
        # Rollback nếu có lỗi
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}')

    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

    

@chuyen_bay_routes.route('/danh_sach_chuyen_bay_admin')
def danh_sach_chuyen_bay_admin():
    flight_list = Flight.query.all()

    role = session.get('user', {}).get('role', 'Customer')
    return render_template(
        'danh_sach_chuyen_bay_admin.html',
        flight_list=flight_list,
        role=role
    )

@chuyen_bay_routes.route('/danh_sach_chuyen_bay')
def danh_sach_chuyen_bay():
    # try:
        # Lấy danh sách chuyến bay từ cơ sở dữ liệu
    flight_list = Flight.query.all()
    if not flight_list:
        flash('Không có chuyến bay nào để hiển thị.')
        return render_template('danh_sach_chuyen_bay.html', flight_list=flight_list, role=role)

    role = session.get('user', {}).get('role', 'Customer')
    return render_template('danh_sach_chuyen_bay.html', flight_list=flight_list, role=role)

@chuyen_bay_routes.route('/them_chuyen_bay', methods=['GET', 'POST'])
def them_chuyen_bay():
    if request.method == 'GET':
        try:
            # Lấy danh sách sân bay từ cơ sở dữ liệu
            airport_list = Airport.query.all()
            role = session.get('user', {}).get('role', 'Admin')
            return render_template('them_chuyen_bay.html', airport_list=airport_list, role=role)
        except Exception as e:
            flash(f'Có lỗi xảy ra khi tải danh sách sân bay: {str(e)}')
            return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))

    elif request.method == 'POST':
        # Lấy thông tin từ form
        flight_id = request.form.get('flight_id')
        airport_arrival = request.form.get('airport_arrival')
        airport_departure = request.form.get('airport_departure')
        start_location = request.form.get('start_location')
        destination = request.form.get('destination')

        # try:
            # Tạo đối tượng Flight
        flight = Flight(
            id=flight_id,
            destination_id=airport_arrival,
            start_location_id=airport_departure,
            start_location=start_location,
            destination=destination
        )
        db.session.add(flight)


        class_1 = Ticket(
            flight_id=flight_id,
            ticket_class='Hạng 1',
            price=1500000
        )
        db.session.add(class_1)


        class_2 = Ticket(
            flight_id=flight_id,
            ticket_class='Hạng 2',
            price=800000
        )
        db.session.add(class_2)

        # Lưu thay đổi vào cơ sở dữ liệu
        db.session.commit()

        flash('Thêm chuyến bay thành công!')
            # return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

        # except Exception as e:
        #     # Rollback nếu có lỗi
        #     db.session.rollback()
        #     flash(f'Có lỗi xảy ra: {str(e)}')

    role = session.get('user', {}).get('role', 'Customer')
    return render_template('them_chuyen_bay.html', role=role)


@chuyen_bay_routes.route('/sua_chuyen_bay/<flight_id>', methods=['GET', 'POST'])
def sua_chuyen_bay(flight_id):
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
                # Lấy chuyến bay cần sửa
                flight = Flight.query.filter_by(id=flight_id).first()

                if not flight:
                    flash('Chuyến bay không tồn tại!')
                    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))

                # Cập nhật thông tin chuyến bay
                flight.destination_id = airport_arrival_new
                flight.start_location_id = airport_departure_new
                flight.start_location = start_location_new
                flight.destination = destination_new

                # Lưu thay đổi vào cơ sở dữ liệu
                db.session.commit()

                flash('Cập nhật chuyến bay thành công!')
                return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))

            except Exception as e:
                # Rollback nếu có lỗi
                db.session.rollback()
                flash(f'Có lỗi xảy ra: {str(e)}')
                return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))
        return render_template('sua_chuyen_bay.html', flight=flight, airport_list=airport_list, role=role)
    
    return render_template('sua_chuyen_bay.html')

@chuyen_bay_routes.route('/xoa_chuyen_bay/<flight_id>')
def xoa_chuyen_bay(flight_id):
    try:
        # Lấy chuyến bay cần xóa
        FlightSchedule.query.filter_by(flight_id=flight_id).delete()
        Ticket.query.filter_by(flight_id=flight_id).delete()

        flight = Flight.query.filter_by(id=flight_id).first()

        if not flight:
            flash('Chuyến bay không tồn tại!')
            return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))

        # Xóa chuyến bay
        db.session.delete(flight)
        db.session.commit()

        flash('Xóa chuyến bay thành công!')
    except Exception as e:
        # Rollback nếu có lỗi
        db.session.rollback()
        flash(f'Có lỗi xảy ra: {str(e)}')

    return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))