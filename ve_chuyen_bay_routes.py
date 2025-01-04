from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from extensions import db
from datetime import datetime, timedelta
import vnpay
from models import Ticket, Flight, BookingTicket, FlightSchedule, Booking

ve_chuyen_bay_routes = Blueprint('ve_chuyen_bay_routes', __name__)


@ve_chuyen_bay_routes.route('/ve_chuyen_bay/<flight_id>', methods=['GET'])
def ve_chuyen_bay(flight_id):
    username = session['user']['username']
    try:
        # Truy vấn danh sách vé chuyến bay theo flight_schedule_id
        flight_schedules = FlightSchedule.query.filter_by(flight_id=flight_id).all()
        ticket_list = Ticket.query.filter(Ticket.flight_schedule_id.in_([fs.id for fs in flight_schedules])).all()
        role = session.get('user', {}).get('role', 'Customer')
        return render_template('ve_chuyen_bay.html', ticket_list=ticket_list, flight_id=flight_id, role=role, username=username)
    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay_admin'))

@ve_chuyen_bay_routes.route('/ve_chuyen_bay_staff/<flight_id>', methods=['GET'])
def ve_chuyen_bay_staff(flight_id):
    username = session['user']['username']
    try:
        # Truy vấn danh sách vé chuyến bay theo flight_schedule_id
        flight_schedules = FlightSchedule.query.filter_by(flight_id=flight_id).all()
        ticket_list = Ticket.query.filter(Ticket.flight_schedule_id.in_([fs.id for fs in flight_schedules])).all()
        role = session.get('user', {}).get('role', 'Staff')
        return render_template('ve_chuyen_bay_staff.html', ticket_list=ticket_list, flight_id=flight_id, role=role, username=username)
    except Exception as e:
        flash(f'Có lỗi xảy ra: {str(e)}')
        return redirect(url_for('chuyen_bay_routes.danh_sach_chuyen_bay'))

@ve_chuyen_bay_routes.route('/sua_ve_chuyen_bay/<id>', methods=['GET', 'POST'])
def sua_ve_chuyen_bay(id):
    username = session['user']['username']
    if request.method == 'GET':
        try:
            # Truy vấn thông tin vé chuyến bay theo mã vé
            flight_ticket = Ticket.query.filter_by(id=id).first()
            flight_schedule = FlightSchedule.query.get(flight_ticket.flight_schedule_id)
            role = session.get('user', {}).get('role', 'Customer')
            if flight_ticket:
                return render_template('sua_ve_chuyen_bay.html', flight_ticket=flight_ticket, role=role, username=username)
            else:
                flash('Vé chuyến bay không tồn tại!')
                return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_schedule.flight_id))
        except Exception as e:
            flash(f'Có lỗi xảy ra: {str(e)}')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay'))
    
    elif request.method == 'POST':
        try:
            # Lấy thông tin từ form
            class_new = request.form['ticket_class']
            price_new = int(request.form['price'])
            quantity_new = int(request.form['quantity'])

            # Truy vấn và cập nhật thông tin vé chuyến bay
            flight_ticket = Ticket.query.filter_by(id=id).first()
            flight_schedule = FlightSchedule.query.get(flight_ticket.flight_schedule_id)
            if flight_ticket:
                flight_ticket.ticket_class = class_new
                flight_ticket.price = price_new
                flight_ticket.quantity = quantity_new

                # Lưu thay đổi vào cơ sở dữ liệu
                db.session.commit()

                flash('Cập nhật vé chuyến bay thành công!')
                return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_schedule.flight_id))
            else:
                flash('Vé chuyến bay không tồn tại!')
                return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', id=flight_schedule.flight_id))
        except Exception as e:
            # Xử lý lỗi nếu có
            db.session.rollback()
            flash(f'Có lỗi xảy ra: {str(e)}')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_schedule.flight_id))



@ve_chuyen_bay_routes.route('/them_ve_chuyen_bay/<flight_id>', methods=['GET', 'POST'])
def them_ve_chuyen_bay(flight_id):
    username = session['user']['username']
    flight_schedules = db.session.query(FlightSchedule.id).filter(FlightSchedule.flight_id == flight_id).all()
    if request.method == 'POST':
        price = request.form['price']
        ticket_class = request.form['ticket_class']
        quantity = request.form['quantity']
        flight_schedule_id = request.form['flight_schedule_id']

        # Kiểm tra số lượng vé hiện có cho từng hạng vé
        existing_tickets = db.session.query(Ticket).filter(Ticket.flight_schedule_id == flight_schedule_id).all()
        class_1_exists = any(ticket.ticket_class == '1' for ticket in existing_tickets)
        class_2_exists = any(ticket.ticket_class == '2' for ticket in existing_tickets)

        # Kiểm tra điều kiện để thêm vé
        if class_1_exists and class_2_exists:
            flash('Đã có đủ 2 hạng vé cho lịch chuyến bay này. Không thể thêm vé mới.')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_id))

        if (ticket_class == '1' and class_1_exists) or (ticket_class == '2' and class_2_exists):
            flash('Không thể thêm vé hạng này vì đã tồn tại.')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_id))


        # Tạo một vé mới với flight_schedule_id, thay vì flight_id
        flight_schedule = FlightSchedule.query.filter_by(flight_id=flight_id).first()  
        if flight_schedule:
            ticket = Ticket(flight_schedule_id=flight_schedule_id, price=price, ticket_class=ticket_class, quantity=quantity)
            db.session.add(ticket)
            db.session.commit()
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_id))
        else:
            flash('Không tìm thấy chuyến bay tương ứng.')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_id))
    role = session.get('role', 'Admin')
    return render_template('them_ve.html', flight_id=flight_id, flight_schedules=flight_schedules,role=role,username=username)

@ve_chuyen_bay_routes.route('/them_ve_chuyen_bay_staff/<flight_id>', methods=['GET', 'POST'])
def them_ve_chuyen_bay_staff(flight_id):
    username = session['user']['username']
    flight_schedules = db.session.query(FlightSchedule.id).filter(FlightSchedule.flight_id == flight_id).all()
    
    if request.method == 'POST':
        price = request.form['price']
        ticket_class = request.form['ticket_class']
        quantity = request.form['quantity']
        flight_schedule_id = request.form['flight_schedule_id']

        # Kiểm tra số lượng vé hiện có cho từng hạng vé
        existing_tickets = db.session.query(Ticket).filter(Ticket.flight_schedule_id == flight_schedule_id).all()
        class_1_exists = any(ticket.ticket_class == '1' for ticket in existing_tickets)
        class_2_exists = any(ticket.ticket_class == '2' for ticket in existing_tickets)

        # Kiểm tra điều kiện để thêm vé
        if class_1_exists and class_2_exists:
            flash('Đã có đủ 2 hạng vé cho lịch chuyến bay này. Không thể thêm vé mới.')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay_staff', flight_id=flight_id))

        if (ticket_class == '1' and class_1_exists) or (ticket_class == '2' and class_2_exists):
            flash('Không thể thêm vé hạng này vì đã tồn tại.')
            return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay_staff', flight_id=flight_id))
        
        # Tạo một vé mới với flight_schedule_id
        ticket = Ticket(flight_schedule_id=flight_schedule_id, price=price, ticket_class=ticket_class, quantity=quantity)
        db.session.add(ticket)
        db.session.commit()
        role = session.get('user', {}).get('role', 'Staff')
        return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay_staff', flight_id=flight_id, role=role))

    role = session.get('user', {}).get('role', 'Staff')
    return render_template('them_ve_staff.html', flight_id=flight_id, flight_schedules=flight_schedules, role=role, username=username)


@ve_chuyen_bay_routes.route('/xoa_ve_chuyen_bay/<int:ticket_id>', methods=['POST'])
def xoa_ve_chuyen_bay(ticket_id):
     # Lấy vé theo ID
    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        flash('Không tìm thấy vé cần xóa.', 'danger')
        return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=None))

    # Kiểm tra xem vé này có được đặt trong bất kỳ đặt chỗ nào không (qua bảng BookingTicket)
    booking_ticket_exists = BookingTicket.query.filter_by(ticket_id=ticket_id).first()
    
    if booking_ticket_exists:
        flash('Không thể xóa vé vì đã có khách hàng đặt vé này.', 'danger')
    else:
        # Nếu vé không có trong bất kỳ đơn đặt vé nào, xóa vé
        try:
            db.session.delete(ticket)
            db.session.commit()
            flash('Đã xóa vé thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Xóa vé thất bại: {str(e)}', 'danger')

    # Lấy flight_id để chuyển hướng lại trang
    flightschedule = FlightSchedule.query.get(ticket.flight_schedule_id)
    flight_id = flightschedule.flight_id if flightschedule else None

    # Chuyển hướng lại trang danh sách vé chuyến bay
    return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay', flight_id=flight_id))


@ve_chuyen_bay_routes.route('/xoa_ve_chuyen_bay_staff/<int:ticket_id>', methods=['POST'])
def xoa_ve_chuyen_bay_staff(ticket_id):
    # Lấy vé theo ID
    ticket = Ticket.query.get(ticket_id)

    if not ticket:
        flash('Không tìm thấy vé cần xóa.', 'danger')
        return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay_staff', flight_id=None))

    # Kiểm tra xem vé này có được đặt trong bất kỳ đặt chỗ nào không (qua bảng BookingTicket)
    booking_ticket_exists = BookingTicket.query.filter_by(ticket_id=ticket_id).first()
    
    if booking_ticket_exists:
        flash('Không thể xóa vé vì đã có khách hàng đặt vé này.', 'danger')
    else:
        # Nếu vé không có trong bất kỳ đơn đặt vé nào, xóa vé
        try:
            db.session.delete(ticket)
            db.session.commit()
            flash('Đã xóa vé thành công!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Xóa vé thất bại: {str(e)}', 'danger')

    # Lấy flight_id để chuyển hướng lại trang
    flightschedule = FlightSchedule.query.get(ticket.flight_schedule_id)
    flight_id = flightschedule.flight_id if flightschedule else None

    # Chuyển hướng lại trang danh sách vé chuyến bay
    return redirect(url_for('ve_chuyen_bay_routes.ve_chuyen_bay_staff', flight_id=flight_id))
